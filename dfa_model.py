from .nfa_model import epsilon_closure, move, NFAState # NFAState needed for type hints or checks if any

class DFA:
    def __init__(self):
        self.states = set() # Set of DFA state IDs (integers)
        self.alphabet = set() # Set of input symbols
        self.transitions = {} # (dfa_state_id, symbol) -> dfa_state_id
        self.start_state_id = None # Integer ID
        self.accept_states = {} # dfa_state_id -> pattern_name
        self._state_map = {} # frozenset(NFAState objects) -> dfa_state_id (integer)
        self._next_dfa_id = 0

    def _get_dfa_state_id(self, nfa_states_frozenset):
        if nfa_states_frozenset not in self._state_map:
            self._state_map[nfa_states_frozenset] = self._next_dfa_id
            self.states.add(self._next_dfa_id)
            self._next_dfa_id += 1
        return self._state_map[nfa_states_frozenset]

    def add_transition(self, from_id, symbol, to_id):
        self.transitions[(from_id, symbol)] = to_id

    def set_accept_state(self, dfa_id, pattern_name):
        # Handles precedence if a DFA state corresponds to multiple NFA accept states
        if dfa_id not in self.accept_states:
            self.accept_states[dfa_id] = pattern_name
        # else: keep the first one assigned (based on pattern_order logic in nfa_to_dfa)


def nfa_to_dfa(combined_nfa_start_state, combined_nfa_accept_states_map, alphabet, pattern_order):
    dfa = DFA()
    dfa.alphabet = alphabet

    # Initial DFA state from epsilon closure of combined NFA start state
    q0_nfa_set = epsilon_closure({combined_nfa_start_state})
    dfa.start_state_id = dfa._get_dfa_state_id(q0_nfa_set)
    
    # Worklist for unmarked DFA states (represented by their set of NFA states)
    worklist = [q0_nfa_set]
    # Keep track of processed DFA states to avoid redundant work
    processed_dfa_sets = set()

    while worklist:
        current_nfa_states_set = worklist.pop(0) # This is a frozenset of NFAState objects
        
        if current_nfa_states_set in processed_dfa_sets:
            continue
        processed_dfa_sets.add(current_nfa_states_set)

        current_dfa_id = dfa._get_dfa_state_id(current_nfa_states_set)

        # Determine if this DFA state is an accept state
        # And handle multiple NFA accept states by order of RE definition
        current_dfa_pattern = None
        min_pattern_index = float('inf')

        for nfa_s in current_nfa_states_set:
            if nfa_s in combined_nfa_accept_states_map:
                pattern_name = combined_nfa_accept_states_map[nfa_s]
                try:
                    idx = pattern_order.index(pattern_name)
                    if idx < min_pattern_index:
                        min_pattern_index = idx
                        current_dfa_pattern = pattern_name
                except ValueError: # Should not happen if pattern_order is correct
                    print(f"Warning: Pattern '{pattern_name}' from NFA accept map not in pattern_order.")
        
        if current_dfa_pattern:
            dfa.set_accept_state(current_dfa_id, current_dfa_pattern)


        # For each symbol in the alphabet
        for symbol in sorted(list(alphabet)): # Sorting ensures consistent processing order
            move_result = move(current_nfa_states_set, symbol)
            if not move_result: # No transitions on this symbol from this set of NFA states
                continue 
            
            target_nfa_states_set = epsilon_closure(move_result)
            if not target_nfa_states_set: # Epsilon closure is empty
                continue

            target_dfa_id = dfa._get_dfa_state_id(target_nfa_states_set)
            dfa.add_transition(current_dfa_id, symbol, target_dfa_id)

            if target_nfa_states_set not in processed_dfa_sets and target_nfa_states_set not in worklist:
                worklist.append(target_nfa_states_set)
                
    return dfa