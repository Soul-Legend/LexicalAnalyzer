from .regex_processing import EPSILON, CONCAT_OP, is_operand

class NFAState:
    _id_counter = 0
    def __init__(self):
        self.id = NFAState._id_counter
        NFAState._id_counter += 1
        self.transitions = {} # symbol -> set of NFAState objects

    def add_transition(self, symbol, next_state):
        self.transitions.setdefault(symbol, set()).add(next_state)

    def __repr__(self):
        return f"S{self.id}"
    
    def __lt__(self, other): # For sorting states by ID
        if not isinstance(other, NFAState):
            return NotImplemented
        return self.id < other.id

    def __eq__(self, other): # For set operations and comparisons
        if not isinstance(other, NFAState):
            return NotImplemented
        return self.id == other.id

    def __hash__(self): # For using NFAState objects in sets/dictionary keys
        return hash(self.id)


class NFA:
    def __init__(self, start_state, accept_state):
        self.start_state = start_state
        self.accept_state = accept_state # Single accept state for Thompson's construction components
        self.states = set() # All unique NFAState objects in this NFA
        self.alphabet = set() # Symbols (excluding EPSILON)

    @staticmethod
    def reset_state_ids():
        NFAState._id_counter = 0


def build_nfa_from_char(char):
    start = NFAState()
    accept = NFAState()
    start.add_transition(char, accept)
    nfa = NFA(start, accept)
    nfa.states = {start, accept}
    if char != EPSILON:
        nfa.alphabet = {char}
    return nfa

def build_nfa_concat(nfa1, nfa2):
    # nfa1's accept state transitions to nfa2's start state via epsilon
    nfa1.accept_state.add_transition(EPSILON, nfa2.start_state)
    # The new NFA's start is nfa1's start, accept is nfa2's accept
    nfa = NFA(nfa1.start_state, nfa2.accept_state)
    nfa.states = nfa1.states.union(nfa2.states)
    nfa.alphabet = nfa1.alphabet.union(nfa2.alphabet)
    return nfa

def build_nfa_union(nfa1, nfa2):
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa1.start_state)
    start.add_transition(EPSILON, nfa2.start_state)
    nfa1.accept_state.add_transition(EPSILON, accept)
    nfa2.accept_state.add_transition(EPSILON, accept)
    nfa = NFA(start, accept)
    nfa.states = nfa1.states.union(nfa2.states).union({start, accept})
    nfa.alphabet = nfa1.alphabet.union(nfa2.alphabet)
    return nfa

def build_nfa_kleene_star(nfa_operand):
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state)
    start.add_transition(EPSILON, accept) # Path for zero occurrences
    nfa_operand.accept_state.add_transition(EPSILON, nfa_operand.start_state) # Loop back
    nfa_operand.accept_state.add_transition(EPSILON, accept) # Exit loop
    nfa = NFA(start, accept)
    nfa.states = nfa_operand.states.union({start, accept})
    nfa.alphabet = nfa_operand.alphabet
    return nfa

def build_nfa_kleene_plus(nfa_operand): # e+ == e.e*
    # This implementation is more direct for A+
    start = NFAState()
    accept = NFAState()
    
    # Connect new start to operand's start
    start.add_transition(EPSILON, nfa_operand.start_state)
    
    # Loop back from operand's accept to its start
    nfa_operand.accept_state.add_transition(EPSILON, nfa_operand.start_state)
    # Connect operand's accept to new accept state
    nfa_operand.accept_state.add_transition(EPSILON, accept)
    
    nfa = NFA(start, accept)
    nfa.states = nfa_operand.states.union({start, accept})
    nfa.alphabet = nfa_operand.alphabet
    return nfa


def build_nfa_optional(nfa_operand): # e?
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state) # Path for one occurrence
    start.add_transition(EPSILON, accept) # Path for zero occurrences (skip)
    nfa_operand.accept_state.add_transition(EPSILON, accept)
    nfa = NFA(start, accept)
    nfa.states = nfa_operand.states.union({start, accept})
    nfa.alphabet = nfa_operand.alphabet
    return nfa

def postfix_to_nfa(postfix_expr):
    # NFA.reset_state_ids() # Resetting here might be too aggressive if called multiple times
                         # Better to reset before starting a batch of RE processing.
    if not postfix_expr:
        # Handle empty regex (matches empty string)
        return build_nfa_from_char(EPSILON)

    stack = []
    for char in postfix_expr:
        if is_operand(char):
            # Each char NFA component should have fresh state IDs relative to its construction
            # but global counter _id_counter ensures overall uniqueness if not reset per char.
            # Resetting NFAState._id_counter per character is wrong.
            # It should be reset once before processing a set of REs.
            stack.append(build_nfa_from_char(char))
        elif char == CONCAT_OP:
            if len(stack) < 2: raise ValueError("Invalid postfix: Not enough operands for concatenation.")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            stack.append(build_nfa_concat(nfa1, nfa2))
        elif char == '|':
            if len(stack) < 2: raise ValueError("Invalid postfix: Not enough operands for union.")
            nfa2 = stack.pop()
            nfa1 = stack.pop()
            stack.append(build_nfa_union(nfa1, nfa2))
        elif char == '*':
            if len(stack) < 1: raise ValueError("Invalid postfix: Not enough operands for Kleene star.")
            nfa_operand = stack.pop()
            stack.append(build_nfa_kleene_star(nfa_operand))
        elif char == '+':
            if len(stack) < 1: raise ValueError("Invalid postfix: Not enough operands for Kleene plus.")
            nfa_operand = stack.pop()
            stack.append(build_nfa_kleene_plus(nfa_operand))
        elif char == '?':
            if len(stack) < 1: raise ValueError("Invalid postfix: Not enough operands for optional.")
            nfa_operand = stack.pop()
            stack.append(build_nfa_optional(nfa_operand))
        else:
            raise ValueError(f"Unknown operator in postfix: {char}")
            
    if len(stack) != 1:
        raise ValueError(f"Invalid postfix expression for NFA construction. Stack size: {len(stack)}")
    
    final_nfa = stack.pop()
    
    # Populate final_nfa.states and final_nfa.alphabet by traversing
    # This ensures all reachable states and the full alphabet are captured.
    all_nfa_states = set()
    alphabet = set()
    queue = [final_nfa.start_state]
    visited_traversal = {final_nfa.start_state}
    
    while queue:
        current_state = queue.pop(0)
        all_nfa_states.add(current_state)
        for symbol, next_states_set in current_state.transitions.items():
            if symbol != EPSILON:
                alphabet.add(symbol)
            for next_s in next_states_set:
                if next_s not in visited_traversal:
                    visited_traversal.add(next_s)
                    queue.append(next_s)
    
    final_nfa.states = all_nfa_states
    final_nfa.alphabet = alphabet
    return final_nfa

def epsilon_closure(nfa_states_set): # Input is a set of NFAState objects
    closure = set(nfa_states_set)
    stack = list(nfa_states_set)
    while stack:
        s = stack.pop()
        if EPSILON in s.transitions:
            for next_s in s.transitions[EPSILON]:
                if next_s not in closure:
                    closure.add(next_s)
                    stack.append(next_s)
    return frozenset(closure) # Return frozenset for use as dict keys

def move(nfa_states_set, symbol): # Input is a set of NFAState objects
    reachable = set()
    for s in nfa_states_set:
        if symbol in s.transitions:
            reachable.update(s.transitions[symbol])
    return frozenset(reachable) # Return frozenset

def combine_nfas(nfas_map): # nfas_map is {pattern_name: NFA_object}
    # NFA.reset_state_ids() # Should be done before this whole process, not inside.
    overall_start_state = NFAState()
    overall_accept_states_map = {} # NFAState_object -> pattern_name
    combined_alphabet = set()

    for pattern_name, nfa_instance in nfas_map.items():
        if nfa_instance is None: continue # Skip if NFA is None (e.g., for reserved words handled differently)
        overall_start_state.add_transition(EPSILON, nfa_instance.start_state)
        # The NFA accept state itself is the key, mapping to its pattern name
        overall_accept_states_map[nfa_instance.accept_state] = pattern_name
        combined_alphabet.update(nfa_instance.alphabet)
        
    return overall_start_state, overall_accept_states_map, combined_alphabet