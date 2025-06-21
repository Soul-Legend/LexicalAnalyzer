from .config import EPSILON, CONCAT_OP
from .regex_utils import is_token_literal

class NFAState:
    _id_counter = 0
    def __init__(self):
        self.id = NFAState._id_counter
        NFAState._id_counter += 1
        self.transitions = {}

    def add_transition(self, symbol, next_state):
        self.transitions.setdefault(symbol, set()).add(next_state)

    def __repr__(self):
        return f"S{self.id}"

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, NFAState) and self.id == other.id
    
    def __lt__(self, other):
        if isinstance(other, NFAState):
            return self.id < other.id
        return NotImplemented

class NFA:
    def __init__(self, start_state, accept_state):
        self.start_state = start_state
        self.accept_state = accept_state 
        self.states = set()        
        self.alphabet = set()    

    @staticmethod
    def reset_state_ids():
        NFAState._id_counter = 0

def build_nfa_from_char_token(char_token):
    start = NFAState()
    accept = NFAState()
    
    actual_char_for_transition = char_token
    if len(char_token) == 2 and char_token.startswith('\\'):
        actual_char_for_transition = char_token[1] 
    
    start.add_transition(actual_char_for_transition, accept)
    nfa = NFA(start, accept)
    return nfa

def build_nfa_concat(nfa1, nfa2):
    if not nfa1 or not nfa2 or not nfa1.accept_state or not nfa2.start_state:
        raise ValueError("Invalid NFAs for concatenation")
    nfa1.accept_state.add_transition(EPSILON, nfa2.start_state)
    new_nfa = NFA(nfa1.start_state, nfa2.accept_state)
    return new_nfa

def build_nfa_union(nfa1, nfa2):
    if not nfa1 or not nfa2 or not nfa1.start_state or not nfa1.accept_state or \
       not nfa2.start_state or not nfa2.accept_state:
        raise ValueError("Invalid NFAs for union")
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa1.start_state)
    start.add_transition(EPSILON, nfa2.start_state)
    nfa1.accept_state.add_transition(EPSILON, accept)
    nfa2.accept_state.add_transition(EPSILON, accept)
    new_nfa = NFA(start, accept)
    return new_nfa

def build_nfa_kleene_star(nfa_operand):
    if not nfa_operand or not nfa_operand.start_state or not nfa_operand.accept_state:
        raise ValueError("Invalid NFA for Kleene star")
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state)
    start.add_transition(EPSILON, accept) 
    nfa_operand.accept_state.add_transition(EPSILON, nfa_operand.start_state) 
    nfa_operand.accept_state.add_transition(EPSILON, accept) 
    new_nfa = NFA(start, accept)
    return new_nfa

def build_nfa_kleene_plus(nfa_operand): 
    if not nfa_operand or not nfa_operand.start_state or not nfa_operand.accept_state:
        raise ValueError("Invalid NFA for Kleene plus")
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state)
    nfa_operand.accept_state.add_transition(EPSILON, nfa_operand.start_state)
    nfa_operand.accept_state.add_transition(EPSILON, accept)
    new_nfa = NFA(start, accept)
    return new_nfa
    
def build_nfa_optional(nfa_operand): 
    if not nfa_operand or not nfa_operand.start_state or not nfa_operand.accept_state:
        raise ValueError("Invalid NFA for optional")
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state) 
    start.add_transition(EPSILON, accept)
    nfa_operand.accept_state.add_transition(EPSILON, accept)
    new_nfa = NFA(start, accept)
    return new_nfa

def _finalize_nfa_properties(nfa):
    '''
    Passa por cada estado e transição do automato para descobrir
    cada um de seus estados e simbolos e preencher os atributos
    states e alphabet.
    '''
    all_nfa_states, nfa_alphabet = set(), set()
    if not nfa or not nfa.start_state: return nfa 

    q = [nfa.start_state]
    visited_traversal = {nfa.start_state}
    all_nfa_states.add(nfa.start_state)

    head = 0
    while head < len(q):
        curr = q[head]
        head +=1
        
        for symbol_in_transition, next_states_set in curr.transitions.items():
            actual_symbol_for_alphabet = symbol_in_transition
            if len(symbol_in_transition) == 2 and symbol_in_transition.startswith('\\'):
                actual_symbol_for_alphabet = symbol_in_transition[1]
            
            if symbol_in_transition != EPSILON: 
                nfa_alphabet.add(actual_symbol_for_alphabet)

            for next_s in next_states_set:
                all_nfa_states.add(next_s)
                if next_s not in visited_traversal:
                    visited_traversal.add(next_s)
                    q.append(next_s)

    if nfa.accept_state:
        all_nfa_states.add(nfa.accept_state)

    nfa.states = all_nfa_states
    nfa.alphabet = nfa_alphabet
    return nfa

def postfix_to_nfa(postfix_tokens_list):
    '''
    Transforma ER posfixa em automato não deterministico ao interpretar 
    cada subexpressão da ER como um automato e utilizar a propriedade de união
    por epsilon para unir cada um dos automatos gerados em um único automato
    não deterministico que é capaz de reconhecer a linguagem descrita pela ER.
    '''
    from regex_utils import is_token_literal
    from config import CONCAT_OP

    if not postfix_tokens_list: return None
    stack = []
    for token in postfix_tokens_list:
        if is_token_literal(token): # is_token_literal já considera EPSILON
            stack.append(build_nfa_from_char_token(token))
        elif token == CONCAT_OP:
            if len(stack) < 2: raise ValueError("Not enough operands for CONCAT")
            nfa2, nfa1 = stack.pop(), stack.pop()
            stack.append(build_nfa_concat(nfa1, nfa2))
        elif token == '|':
            if len(stack) < 2: raise ValueError("Not enough operands for UNION")
            nfa2, nfa1 = stack.pop(), stack.pop()
            stack.append(build_nfa_union(nfa1, nfa2))
        elif token == '*':
            if not stack: raise ValueError("Not enough operand for STAR")
            stack.append(build_nfa_kleene_star(stack.pop()))
        elif token == '+':
            if not stack: raise ValueError("Not enough operand for PLUS")
            stack.append(build_nfa_kleene_plus(stack.pop()))
        elif token == '?':
            if not stack: raise ValueError("Not enough operand for OPTIONAL")
            stack.append(build_nfa_optional(stack.pop()))
        else:
            raise ValueError(f"Unknown operator or token '{token}' in postfix expression list.")
    if len(stack) != 1:
        raise ValueError(f"Invalid postfix expression list for NFA construction: stack size is {len(stack)}")
    
    final_nfa = stack.pop()
    return _finalize_nfa_properties(final_nfa)

def epsilon_closure(nfa_states_set_arg):
    if not isinstance(nfa_states_set_arg, set) and not isinstance(nfa_states_set_arg, frozenset):
        if isinstance(nfa_states_set_arg, NFAState):
             nfa_states_set = {nfa_states_set_arg}
        else: 
            nfa_states_set = set(nfa_states_set_arg)
    else:
        nfa_states_set = set(nfa_states_set_arg)
    if not nfa_states_set: return frozenset()
    closure = set(nfa_states_set)
    worklist = list(nfa_states_set) 
    while worklist:
        s = worklist.pop()
        if EPSILON in s.transitions:
            for next_s in s.transitions[EPSILON]:
                if next_s not in closure:
                    closure.add(next_s)
                    worklist.append(next_s)
    return frozenset(closure)

def move(nfa_states_fset, symbol_from_input):
    reachable = set()
    for s in nfa_states_fset:
        # As transições no NFA são armazenadas com o símbolo real (ex: '+', não '\+')
        # symbol_from_input é o caractere real da entrada.
        if symbol_from_input in s.transitions:
            reachable.update(s.transitions[symbol_from_input])
    return frozenset(reachable)

class DFA:
    def __init__(self):
        self.states = set()
        self.alphabet = set()
        self.transitions = {}
        self.start_state_id = None
        self.accept_states = {} 
        self._state_map = {} 
        self._next_dfa_id = 0

    def _get_dfa_state_id(self, state_representation_fset):
        canonical_key_tuple = tuple(sorted(list(state_representation_fset)))
        if canonical_key_tuple not in self._state_map:
            new_id = self._next_dfa_id
            self._state_map[canonical_key_tuple] = new_id
            self.states.add(new_id)
            self._next_dfa_id += 1
            return new_id
        return self._state_map[canonical_key_tuple]

    def add_transition(self, from_id, symbol, to_id):
        self.transitions[(from_id, symbol)] = to_id

    def set_accept_state(self, dfa_id, pattern_name):
        self.accept_states[dfa_id] = pattern_name

def _minimize_dfa(unminimized_dfa):
    if not unminimized_dfa.states:
        return unminimized_dfa 

    initial_partition_map = {}
    for state_id in unminimized_dfa.states:
        if state_id in unminimized_dfa.accept_states:
            pattern = unminimized_dfa.accept_states[state_id]
            key = (True, pattern)
        else:
            key = (False, None)
        initial_partition_map.setdefault(key, set()).add(state_id)
    
    P = {frozenset(group) for group in initial_partition_map.values() if group}
    if not P:
        return unminimized_dfa
        
    W = set(P)

    while W:
        A = W.pop()
        for char_code in unminimized_dfa.alphabet:
            X = set()
            for s_prime in unminimized_dfa.states:
                next_state_for_s_prime = unminimized_dfa.transitions.get((s_prime, char_code), None)
                if next_state_for_s_prime is not None and next_state_for_s_prime in A:
                    X.add(s_prime)
            
            if not X: continue

            new_P_for_iteration = set() 
            P_changed_in_iteration = False
            temp_P_list = list(P) 
            for Y in temp_P_list:
                Y_intersect_X = Y.intersection(X)
                Y_minus_X = Y.difference(X)

                if Y_intersect_X and Y_minus_X:
                    new_P_for_iteration.add(frozenset(Y_intersect_X))
                    new_P_for_iteration.add(frozenset(Y_minus_X))
                    P_changed_in_iteration = True
                    
                    if Y in W:
                        W.remove(Y)
                        W.add(frozenset(Y_intersect_X))
                        W.add(frozenset(Y_minus_X))
                    else:
                        if len(Y_intersect_X) <= len(Y_minus_X):
                            W.add(frozenset(Y_intersect_X))
                        else:
                            W.add(frozenset(Y_minus_X))
                else:
                    new_P_for_iteration.add(Y)
            if P_changed_in_iteration:
                P = new_P_for_iteration
    
    min_dfa = DFA()
    min_dfa.alphabet = unminimized_dfa.alphabet
    partition_map = {} 
    new_state_id_counter = 0
    
    final_partitions_sorted_list_of_tuples = sorted([tuple(sorted(list(p))) for p in P])
    final_partitions_sorted = [frozenset(p_tuple) for p_tuple in final_partitions_sorted_list_of_tuples]


    for part_fset in final_partitions_sorted:
        if part_fset not in partition_map:
            partition_map[part_fset] = new_state_id_counter
            min_dfa.states.add(new_state_id_counter)
            
            representative_old_state = next(iter(part_fset)) 
            if representative_old_state in unminimized_dfa.accept_states:
                pattern_name = unminimized_dfa.accept_states[representative_old_state]
                min_dfa.set_accept_state(new_state_id_counter, pattern_name)

            if unminimized_dfa.start_state_id is not None and unminimized_dfa.start_state_id in part_fset:
                min_dfa.start_state_id = new_state_id_counter
            
            new_state_id_counter += 1

    for part_fset in final_partitions_sorted: 
        new_from_state_id = partition_map[part_fset]
        representative_old_state = next(iter(part_fset))
        for char_code in min_dfa.alphabet:
            old_to_state_id = unminimized_dfa.transitions.get((representative_old_state, char_code), None)
            if old_to_state_id is not None:
                for target_part_fset in final_partitions_sorted: 
                    if old_to_state_id in target_part_fset:
                        new_to_state_id = partition_map[target_part_fset]
                        min_dfa.add_transition(new_from_state_id, char_code, new_to_state_id)
                        break
    return min_dfa

def construct_unminimized_dfa_from_nfa(combined_nfa_start, combined_nfa_accept_map, combined_alphabet, pattern_order):
    dfa = DFA()
    # O alfabeto do DFA é derivado do alfabeto combinado dos NFAs.
    # Se combined_alphabet já tem os caracteres reais (ex: '.', não '\.'), está correto.
    # _finalize_nfa_properties deve garantir isso para cada NFA individual, e combine_nfas os une.
    dfa.alphabet = combined_alphabet if combined_alphabet is not None else set()

    initial_nfa_set_for_closure = {combined_nfa_start} if combined_nfa_start else set()
    q0_nfa_fset_nfa_states = epsilon_closure(initial_nfa_set_for_closure)
    q0_nfa_fset_ids = frozenset(s.id for s in q0_nfa_fset_nfa_states)


    if not q0_nfa_fset_ids : 
        dfa.start_state_id = dfa._get_dfa_state_id(frozenset())
        if combined_nfa_start in combined_nfa_accept_map and not combined_alphabet and len(initial_nfa_set_for_closure)==1 and combined_nfa_start in q0_nfa_fset_nfa_states:
            pattern_name_for_epsilon = combined_nfa_accept_map[combined_nfa_start]
            dfa.set_accept_state(dfa.start_state_id, pattern_name_for_epsilon)
        return dfa

    dfa.start_state_id = dfa._get_dfa_state_id(q0_nfa_fset_ids)
    
    dfa_q_map = {q0_nfa_fset_ids: dfa.start_state_id} 
    worklist = [q0_nfa_fset_nfa_states] 

    while worklist:
        current_nfa_fset_from_worklist_states = worklist.pop(0)
        current_nfa_fset_from_worklist_ids = frozenset(s.id for s in current_nfa_fset_from_worklist_states)
        current_dfa_id = dfa_q_map[current_nfa_fset_from_worklist_ids]

        current_best_pattern = None
        highest_priority_index = float('inf')
        for nfa_s_in_subset in current_nfa_fset_from_worklist_states:
            if nfa_s_in_subset in combined_nfa_accept_map:
                pattern_name = combined_nfa_accept_map[nfa_s_in_subset]
                try:
                    priority = pattern_order.index(pattern_name)
                    if priority < highest_priority_index:
                        highest_priority_index = priority
                        current_best_pattern = pattern_name
                except ValueError: 
                    if current_best_pattern is None:
                        current_best_pattern = pattern_name
        if current_best_pattern:
            dfa.set_accept_state(current_dfa_id, current_best_pattern)

        for symbol in sorted(list(dfa.alphabet)): # 'symbol' aqui é o char real do alfabeto
            move_res_fset_states = move(current_nfa_fset_from_worklist_states, symbol)
            if not move_res_fset_states: continue
            
            target_nfa_fset_after_closure_states = epsilon_closure(move_res_fset_states)
            if not target_nfa_fset_after_closure_states: continue

            target_nfa_fset_after_closure_ids = frozenset(s.id for s in target_nfa_fset_after_closure_states)

            if target_nfa_fset_after_closure_ids not in dfa_q_map:
                target_dfa_id = dfa._get_dfa_state_id(target_nfa_fset_after_closure_ids)
                dfa_q_map[target_nfa_fset_after_closure_ids] = target_dfa_id
                worklist.append(target_nfa_fset_after_closure_states)
            else:
                target_dfa_id = dfa_q_map[target_nfa_fset_after_closure_ids]
            dfa.add_transition(current_dfa_id, symbol, target_dfa_id)
    
    return dfa

def combine_nfas(nfas_map_param):
    overall_start = NFAState()
    accept_map = {}
    alphabet = set()
    for pattern_name, nfa_component in nfas_map_param.items():
        if not nfa_component or not nfa_component.start_state or not nfa_component.accept_state:
            continue
        overall_start.add_transition(EPSILON, nfa_component.start_state)
        accept_map[nfa_component.accept_state] = pattern_name
        if nfa_component.alphabet: # Alphabeto do NFA componente já deve ter chars reais
            alphabet.update(nfa_component.alphabet)
    return overall_start, accept_map, alphabet