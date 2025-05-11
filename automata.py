"""
Finite Automata (NFA, DFA) classes and conversion algorithms.
- NFAState, NFA, DFA classes
- Thompson's construction (postfix_to_nfa)
- Epsilon closure, move operations
- NFA to DFA conversion (subset construction)
- NFA combination
"""
from config import EPSILON
# is_operand and CONCAT_OP will be imported locally in postfix_to_nfa where needed

class NFAState:
    """Represents a state in an NFA."""
    _id_counter = 0

    def __init__(self):
        self.id = NFAState._id_counter
        NFAState._id_counter += 1
        self.transitions = {}  # symbol -> set of NFAState objects

    def add_transition(self, symbol, next_state):
        """Adds a transition from this state."""
        self.transitions.setdefault(symbol, set()).add(next_state)

    def __repr__(self):
        return f"S{self.id}"

    def __hash__(self): # Essential for using states in sets/dictionary keys directly
        return hash(self.id)

    def __eq__(self, other): # Essential for using states in sets/dictionary keys
        return isinstance(other, NFAState) and self.id == other.id
    
    def __lt__(self, other): # For sorting states to make frozensets canonical if needed
        if isinstance(other, NFAState):
            return self.id < other.id
        return NotImplemented

class NFA:
    """Represents a Non-deterministic Finite Automaton."""
    def __init__(self, start_state, accept_state):
        self.start_state = start_state
        self.accept_state = accept_state 
        self.states = set()        
        self.alphabet = set()    

    @staticmethod
    def reset_state_ids():
        NFAState._id_counter = 0

# --- NFA Construction (Thompson's Algorithm building blocks) ---
def build_nfa_from_char(char): # char is a literal character or EPSILON
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
    # Essentially operand followed by operand*
    # Simpler: new_start -> operand.start, operand.accept -> new_accept, operand.accept -> operand.start
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state)
    nfa_operand.accept_state.add_transition(EPSILON, nfa_operand.start_state) # Loop back
    nfa_operand.accept_state.add_transition(EPSILON, accept) # Exit
    new_nfa = NFA(start, accept)
    new_nfa.states = nfa_operand.states.union({start, accept})
    new_nfa.alphabet = nfa_operand.alphabet
    return new_nfa

def build_nfa_optional(nfa_operand): 
    if not nfa_operand or not nfa_operand.start_state or not nfa_operand.accept_state:
        raise ValueError("Invalid NFA for optional")
    # Union with epsilon implicitly
    start = NFAState()
    accept = NFAState()
    start.add_transition(EPSILON, nfa_operand.start_state) 
    start.add_transition(EPSILON, accept) # Path to skip operand
    nfa_operand.accept_state.add_transition(EPSILON, accept)
    new_nfa = NFA(start, accept)
    new_nfa.states = nfa_operand.states.union({start, accept})
    new_nfa.alphabet = nfa_operand.alphabet
    return new_nfa


def postfix_to_nfa(postfix_expr):
    """Converts a postfix regex string to an NFA using Thompson's construction."""
    from regex_utils import is_literal_char # Corrected import
    from config import CONCAT_OP

    if not postfix_expr: return None # Or an NFA that accepts empty string, or error
    
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
            # This should not be reached if postfix_expr is valid and is_literal_char is correct
            raise ValueError(f"Unknown operator or character '{char_code}' in postfix expression '{postfix_expr}'")
            
    if len(stack) != 1:
        # This can happen if the postfix_expr was empty or malformed.
        # e.g. if preprocess_regex or infix_to_postfix returned empty for a non-empty input.
        raise ValueError(f"Invalid postfix expression '{postfix_expr}' for NFA construction: stack size is {len(stack)}")
    
    final_nfa = stack.pop()
    # Populate final_nfa.states and final_nfa.alphabet by traversing
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

# --- NFA to DFA Conversion (epsilon_closure, move, DFA class, nfa_to_dfa) ---
# ... (These parts should be okay from the previous refactored version, ensure DFA state mapping uses NFAState hash/eq) ...
def epsilon_closure(nfa_states_set_arg):
    """Computes the epsilon closure of a set of NFA states."""
    if not isinstance(nfa_states_set_arg, set) and not isinstance(nfa_states_set_arg, frozenset):
        # Ensure input is a set, typically it's a frozenset from `move` or initial set
        if isinstance(nfa_states_set_arg, NFAState): # Single state passed
             nfa_states_set = {nfa_states_set_arg}
        else: # Iterable of states
            nfa_states_set = set(nfa_states_set_arg)
    else:
        nfa_states_set = set(nfa_states_set_arg) # Convert frozenset to mutable for processing

    if not nfa_states_set: return frozenset()

    closure = set(nfa_states_set) # Start with the given states
    
    # Use a list as a stack/worklist for states whose epsilon transitions need checking
    worklist = list(nfa_states_set) 
    
    while worklist:
        s = worklist.pop()
        if EPSILON in s.transitions:
            for next_s in s.transitions[EPSILON]:
                if next_s not in closure:
                    closure.add(next_s)
                    worklist.append(next_s) # Add newly reached states to the worklist
    return frozenset(closure) # Return as frozenset for use as dict keys

def move(nfa_states_fset, symbol): # nfa_states_fset is a frozenset of NFAState
    """Computes the set of NFA states reachable from nfa_states_fset on a given symbol."""
    reachable = set()
    for s in nfa_states_fset:
        if symbol in s.transitions:
            reachable.update(s.transitions[symbol])
    return frozenset(reachable)

class DFA:
    """Represents a Deterministic Finite Automaton."""
    def __init__(self):
        self.states = set()             # Set of DFA state IDs (integers)
        self.alphabet = set()           # Set of input symbols
        self.transitions = {}           # (from_dfa_id, symbol) -> to_dfa_id
        self.start_state_id = None
        self.accept_states = {}         # dfa_id -> pattern_name
        self._state_map = {}            # frozenset(NFAState sorted by ID) -> dfa_id. Changed key to use NFAState.id
        self._next_dfa_id = 0

    def _get_dfa_state_id(self, nfa_states_fset): # nfa_states_fset is a frozenset of NFAState objects
        """Gets or creates a DFA state ID for a frozenset of NFA states."""
        # Create a canonical key from the frozenset of NFAState objects.
        # Sorting by ID ensures that frozenset({s1, s2}) and frozenset({s2, s1}) map to the same key.
        canonical_key_tuple = tuple(sorted([s.id for s in nfa_states_fset]))
        
        if canonical_key_tuple not in self._state_map:
            new_id = self._next_dfa_id
            self._state_map[canonical_key_tuple] = new_id
            self.states.add(new_id) # Add the integer ID to DFA states
            self._next_dfa_id += 1
            return new_id
        return self._state_map[canonical_key_tuple]

    def add_transition(self, from_id, symbol, to_id):
        self.transitions[(from_id, symbol)] = to_id

    def set_accept_state(self, dfa_id, pattern_name):
        # Handle priority: if dfa_id already an accept state, only update if new pattern has higher priority
        # This logic should be handled in nfa_to_dfa based on pattern_order
        self.accept_states[dfa_id] = pattern_name


def nfa_to_dfa(combined_nfa_start, combined_nfa_accept_map, combined_alphabet, pattern_order):
    """Converts a combined NFA to a DFA using subset construction."""
    dfa = DFA()
    dfa.alphabet = combined_alphabet if combined_alphabet is not None else set()

    initial_nfa_set_for_closure = {combined_nfa_start} if combined_nfa_start else set()
    q0_nfa_fset = epsilon_closure(initial_nfa_set_for_closure)

    if not q0_nfa_fset : 
        # This means the NFA accepts an empty language or only epsilon if start is accept.
        # Create a start state. If it's an accept state for epsilon, mark it.
        dfa.start_state_id = dfa._get_dfa_state_id(frozenset()) # DFA state 0 for empty NFA set
        if combined_nfa_start in combined_nfa_accept_map and not combined_alphabet: # Epsilon language
            pattern_name_for_epsilon = combined_nfa_accept_map[combined_nfa_start]
            dfa.set_accept_state(dfa.start_state_id, pattern_name_for_epsilon)
        return dfa

    dfa.start_state_id = dfa._get_dfa_state_id(q0_nfa_fset)
    
    # unmarked_dfa_q stores frozenset(NFAState) -> dfa_id for discovered DFA states
    unmarked_dfa_q = {q0_nfa_fset: dfa.start_state_id} 
    worklist = [q0_nfa_fset] # List of frozensets of NFAState objects

    while worklist:
        current_nfa_fset_from_worklist = worklist.pop(0)
        current_dfa_id = unmarked_dfa_q[current_nfa_fset_from_worklist]

        # Determine if current_dfa_id is an accept state
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
                except ValueError: # Should not happen if pattern_order is comprehensive
                    if current_best_pattern is None: # Fallback if pattern not in order list
                        current_best_pattern = pattern_name
        
        if current_best_pattern:
            dfa.set_accept_state(current_dfa_id, current_best_pattern)

        for symbol in sorted(list(dfa.alphabet)): # Process symbols consistently
            move_res_fset = move(current_nfa_fset_from_worklist, symbol)
            if not move_res_fset: continue # No transitions on this symbol
            
            target_nfa_fset_after_closure = epsilon_closure(move_res_fset)
            if not target_nfa_fset_after_closure: continue # Epsilon closure is empty

            if target_nfa_fset_after_closure not in unmarked_dfa_q: # If this DFA state (NFA subset) is new
                target_dfa_id = dfa._get_dfa_state_id(target_nfa_fset_after_closure)
                unmarked_dfa_q[target_nfa_fset_after_closure] = target_dfa_id
                worklist.append(target_nfa_fset_after_closure)
            else: # DFA state already exists
                target_dfa_id = unmarked_dfa_q[target_nfa_fset_after_closure]
            
            dfa.add_transition(current_dfa_id, symbol, target_dfa_id)
    return dfa

def combine_nfas(nfas_map_param): # pattern_name -> NFA object
    """Combines multiple NFAs into a single NFA using a new start state and epsilon transitions."""
    # NFA.reset_state_ids() # Do this *before* creating the overall_start NFAState if you want it to be S0
    
    overall_start = NFAState() # New global start state
    accept_map = {}            # NFAState_object_of_component_NFA -> pattern_name
    alphabet = set()

    for pattern_name, nfa_component in nfas_map_param.items():
        if not nfa_component or not nfa_component.start_state or not nfa_component.accept_state:
            print(f"Info: Skipping NFA component for '{pattern_name}' during combination (likely ignored or invalid).")
            continue
        overall_start.add_transition(EPSILON, nfa_component.start_state)
        accept_map[nfa_component.accept_state] = pattern_name
        if nfa_component.alphabet:
            alphabet.update(nfa_component.alphabet)
        
    return overall_start, accept_map, alphabet