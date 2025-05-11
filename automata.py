from config import EPSILON

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

def build_nfa_from_char(char):
    start = NFAState()
    accept = NFAState()
    start.add_transition(char, accept)
    nfa = NFA(start, accept)
    nfa.states = {start, accept}
    if char != EPSILON: nfa.alphabet = {char}
    return nfa

def build_nfa_concat(nfa1, nfa2):
    if not nfa1 or not nfa2 or not nfa1.accept_state or not nfa2.start_state:
        raise ValueError("Invalid NFAs for concatenation")
    nfa1.accept_state.add_transition(EPSILON, nfa2.start_state)
    new_nfa = NFA(nfa1.start_state, nfa2.accept_state)
    new_nfa.states = nfa1.states.union(nfa2.states)
    new_nfa.alphabet = nfa1.alphabet.union(nfa2.alphabet)
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
    new_nfa.states = nfa1.states.union(nfa2.states).union({start, accept})
    new_nfa.alphabet = nfa1.alphabet.union(nfa2.alphabet)
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
    new_nfa.states = nfa_operand.states.union({start, accept})
    new_nfa.alphabet = nfa_operand.alphabet
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
    new_nfa.states = nfa_operand.states.union({start, accept})
    new_nfa.alphabet = nfa_operand.alphabet
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
    new_nfa.states = nfa_operand.states.union({start, accept})
    new_nfa.alphabet = nfa_operand.alphabet
    return new_nfa

def postfix_to_nfa(postfix_expr):
    from regex_utils import is_literal_char
    from config import CONCAT_OP
    if not postfix_expr: return None
    stack = []
    for char_code in postfix_expr:
        if is_literal_char(char_code):
            stack.append(build_nfa_from_char(char_code))
        elif char_code == CONCAT_OP:
            if len(stack) < 2: raise ValueError("Not enough operands for CONCAT")
            nfa2, nfa1 = stack.pop(), stack.pop()
            stack.append(build_nfa_concat(nfa1, nfa2))
        elif char_code == '|':
            if len(stack) < 2: raise ValueError("Not enough operands for UNION")
            nfa2, nfa1 = stack.pop(), stack.pop()
            stack.append(build_nfa_union(nfa1, nfa2))
        elif char_code == '*':
            if not stack: raise ValueError("Not enough operand for STAR")
            stack.append(build_nfa_kleene_star(stack.pop()))
        elif char_code == '+':
            if not stack: raise ValueError("Not enough operand for PLUS")
            stack.append(build_nfa_kleene_plus(stack.pop()))
        elif char_code == '?':
            if not stack: raise ValueError("Not enough operand for OPTIONAL")
            stack.append(build_nfa_optional(stack.pop()))
        else:
            raise ValueError(f"Unknown operator or character '{char_code}' in postfix expression '{postfix_expr}'")
    if len(stack) != 1:
        raise ValueError(f"Invalid postfix expression '{postfix_expr}' for NFA construction: stack size is {len(stack)}")
    final_nfa = stack.pop()
    all_nfa_states, nfa_alphabet = set(), set()
    q = [final_nfa.start_state]
    visited_traversal = {final_nfa.start_state}
    while q:
        curr = q.pop(0)
        all_nfa_states.add(curr)
        for symbol, next_states_set in curr.transitions.items():
            if symbol != EPSILON: nfa_alphabet.add(symbol)
            for next_s in next_states_set:
                if next_s not in visited_traversal:
                    visited_traversal.add(next_s)
                    q.append(next_s)
    final_nfa.states = all_nfa_states
    final_nfa.alphabet = nfa_alphabet
    return final_nfa

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

def move(nfa_states_fset, symbol):
    reachable = set()
    for s in nfa_states_fset:
        if symbol in s.transitions:
            reachable.update(s.transitions[symbol])
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

    def _get_dfa_state_id(self, nfa_states_fset):
        canonical_key_tuple = tuple(sorted([s.id for s in nfa_states_fset]))
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

    # P: Current partition of states. Each element in P is a frozenset of state IDs.
    # Initial partition: group by (is_accept_state, pattern_name_if_accept)
    # This means accept states for different patterns are initially in different groups.
    initial_partition_map = {} # (is_accept, pattern_name_or_None) -> set_of_state_ids
    for state_id in unminimized_dfa.states:
        if state_id in unminimized_dfa.accept_states:
            pattern = unminimized_dfa.accept_states[state_id]
            key = (True, pattern)
        else:
            key = (False, None)
        initial_partition_map.setdefault(key, set()).add(state_id)
    
    P = {frozenset(group) for group in initial_partition_map.values() if group}
    
    # W: Worklist of sets in P to process.
    W = set(P) # Initially, all groups in P are in W

    while W:
        A = W.pop() # Pick a set A from W
        for char_code in unminimized_dfa.alphabet:
            # X = set of states s such that transition(s, char_code) is in A
            X = set()
            for s_prime in unminimized_dfa.states:
                # Find where s_prime goes on char_code
                next_state_for_s_prime = unminimized_dfa.transitions.get((s_prime, char_code), None)
                if next_state_for_s_prime is not None and next_state_for_s_prime in A:
                    X.add(s_prime)
            
            if not X: continue

            # For each Y in P such that Y intersects X and Y-X is also non-empty, split Y
            new_P = set() # To build the next P, as P cannot be modified during iteration
            P_changed_in_iteration = False
            for Y in P:
                Y_intersect_X = Y.intersection(X)
                Y_minus_X = Y.difference(X)

                if Y_intersect_X and Y_minus_X: # If Y needs to be split
                    new_P.add(frozenset(Y_intersect_X))
                    new_P.add(frozenset(Y_minus_X))
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
                else: # Y is not split by A and char_code
                    new_P.add(Y)
            if P_changed_in_iteration:
                P = new_P
    
    # P now contains the final partition of equivalent states. Construct the minimized DFA.
    min_dfa = DFA()
    min_dfa.alphabet = unminimized_dfa.alphabet
    
    # Map old state_ids to their partition (which will be the new state id)
    partition_map = {} # frozenset_of_old_ids -> new_min_dfa_state_id
    new_state_id_counter = 0
    
    final_partitions_sorted = sorted([tuple(sorted(list(p))) for p in P]) # Canonical order for consistent new IDs

    for part_tuple in final_partitions_sorted:
        part_fset = frozenset(part_tuple)
        if part_fset not in partition_map:
            partition_map[part_fset] = new_state_id_counter
            min_dfa.states.add(new_state_id_counter)
            
            # Determine if this new state is an accept state and its pattern
            # Pick any old state from the partition to check its properties
            representative_old_state = next(iter(part_fset)) 
            if representative_old_state in unminimized_dfa.accept_states:
                pattern_name = unminimized_dfa.accept_states[representative_old_state]
                min_dfa.set_accept_state(new_state_id_counter, pattern_name)

            # Set start state
            if unminimized_dfa.start_state_id in part_fset:
                min_dfa.start_state_id = new_state_id_counter
            
            new_state_id_counter += 1

    # Create transitions for the minimized DFA
    for part_fset in P:
        new_from_state_id = partition_map[part_fset]
        # Pick any old state from this partition to find its transitions
        representative_old_state = next(iter(part_fset))
        for char_code in min_dfa.alphabet:
            old_to_state_id = unminimized_dfa.transitions.get((representative_old_state, char_code), None)
            if old_to_state_id is not None:
                # Find which partition old_to_state_id belongs to
                for target_part_fset in P:
                    if old_to_state_id in target_part_fset:
                        new_to_state_id = partition_map[target_part_fset]
                        min_dfa.add_transition(new_from_state_id, char_code, new_to_state_id)
                        break
    return min_dfa

def nfa_to_dfa(combined_nfa_start, combined_nfa_accept_map, combined_alphabet, pattern_order):
    unminimized_dfa = DFA()
    unminimized_dfa.alphabet = combined_alphabet if combined_alphabet is not None else set()

    initial_nfa_set_for_closure = {combined_nfa_start} if combined_nfa_start else set()
    q0_nfa_fset = epsilon_closure(initial_nfa_set_for_closure)

    if not q0_nfa_fset : 
        unminimized_dfa.start_state_id = unminimized_dfa._get_dfa_state_id(frozenset())
        if combined_nfa_start in combined_nfa_accept_map and not combined_alphabet:
            pattern_name_for_epsilon = combined_nfa_accept_map[combined_nfa_start]
            unminimized_dfa.set_accept_state(unminimized_dfa.start_state_id, pattern_name_for_epsilon)
        return _minimize_dfa(unminimized_dfa) # Minimize even if it's simple

    unminimized_dfa.start_state_id = unminimized_dfa._get_dfa_state_id(q0_nfa_fset)
    unmarked_dfa_q = {q0_nfa_fset: unminimized_dfa.start_state_id} 
    worklist = [q0_nfa_fset]

    while worklist:
        current_nfa_fset_from_worklist = worklist.pop(0)
        current_dfa_id = unmarked_dfa_q[current_nfa_fset_from_worklist]
        current_best_pattern = None
        highest_priority_index = float('inf')
        for nfa_s_in_subset in current_nfa_fset_from_worklist:
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
            unminimized_dfa.set_accept_state(current_dfa_id, current_best_pattern)

        for symbol in sorted(list(unminimized_dfa.alphabet)):
            move_res_fset = move(current_nfa_fset_from_worklist, symbol)
            if not move_res_fset: continue
            target_nfa_fset_after_closure = epsilon_closure(move_res_fset)
            if not target_nfa_fset_after_closure: continue
            if target_nfa_fset_after_closure not in unmarked_dfa_q:
                target_dfa_id = unminimized_dfa._get_dfa_state_id(target_nfa_fset_after_closure)
                unmarked_dfa_q[target_nfa_fset_after_closure] = target_dfa_id
                worklist.append(target_nfa_fset_after_closure)
            else:
                target_dfa_id = unmarked_dfa_q[target_nfa_fset_after_closure]
            unminimized_dfa.add_transition(current_dfa_id, symbol, target_dfa_id)
    
    # After constructing the unminimized DFA, minimize it.
    minimized_dfa = _minimize_dfa(unminimized_dfa)
    return minimized_dfa

def combine_nfas(nfas_map_param):
    overall_start = NFAState()
    accept_map = {}
    alphabet = set()
    for pattern_name, nfa_component in nfas_map_param.items():
        if not nfa_component or not nfa_component.start_state or not nfa_component.accept_state:
            continue
        overall_start.add_transition(EPSILON, nfa_component.start_state)
        accept_map[nfa_component.accept_state] = pattern_name
        if nfa_component.alphabet:
            alphabet.update(nfa_component.alphabet)
    return overall_start, accept_map, alphabet