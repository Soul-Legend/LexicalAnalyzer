from .nfa_model import NFAState # For isinstance checks or type hints if needed
from .regex_processing import EPSILON # For displaying epsilon transitions

def get_nfa_details_str(nfa_instance, name="NFA"): # nfa_instance is an NFA object
    output = []
    output.append(f"--- {name} Details ---")
    if not nfa_instance or not hasattr(nfa_instance, 'start_state') or not nfa_instance.start_state:
        output.append("NFA is empty or not properly initialized.")
        return "\n".join(output)

    # Use the states stored in the NFA object if populated, otherwise traverse.
    # The NFA build process should populate nfa_instance.states.
    states_to_print = nfa_instance.states
    if not states_to_print: # Fallback: traverse from start if .states is empty
        states_to_print = set()
        q_bfs = [nfa_instance.start_state]
        visited_print = {nfa_instance.start_state}
        while q_bfs:
            curr = q_bfs.pop(0)
            states_to_print.add(curr)
            for symbol, next_states_set in curr.transitions.items():
                for next_s in next_states_set:
                    if next_s not in visited_print:
                        visited_print.add(next_s)
                        q_bfs.append(next_s)
    
    sorted_states = sorted(list(states_to_print), key=lambda s: s.id)

    output.append(f"Start State: S{nfa_instance.start_state.id}")
    
    accept_state_display = "None"
    if hasattr(nfa_instance, 'accept_state') and nfa_instance.accept_state and \
       (not states_to_print or nfa_instance.accept_state in states_to_print) : # For single NFA from Thompson
         accept_state_display = f"S{nfa_instance.accept_state.id} (Thompson component)"
    elif hasattr(nfa_instance, 'accept_states_map') and nfa_instance.accept_states_map: # For combined NFA display
        accept_str_parts = []
        # Ensure nfa_instance.accept_states_map is {NFAState_obj: pattern_name}
        for s_obj, pat_name in nfa_instance.accept_states_map.items():
            if not states_to_print or s_obj in states_to_print: 
                accept_str_parts.append(f"S{s_obj.id}({pat_name})")
        if accept_str_parts:
            accept_state_display = ", ".join(accept_str_parts)
        else:
            accept_state_display = "None in current view (check combined map consistency)"
        accept_state_display += " (from combined NFA map)"
    
    output.append(f"Accept State(s): {accept_state_display}")
    output.append(f"Alphabet: {{ {', '.join(sorted(list(nfa_instance.alphabet)))} }}")


    output.append("Transitions (State, Symbol -> NextStates):")
    for s in sorted_states:
        if s.transitions:
            for symbol, next_states_set in sorted(s.transitions.items()): # Sort symbols for consistent output
                # Sort next states by ID for consistent output
                next_ids = ", ".join([f"S{ns.id}" for ns in sorted(list(next_states_set))])
                display_symbol = EPSILON if symbol == EPSILON else symbol
                output.append(f"  S{s.id}, {display_symbol} -> {{{next_ids}}}")
    output.append(f"Total states in this NFA view: {len(sorted_states)}")
    output.append("--------------------")
    return "\n".join(output)


def get_dfa_table_str(dfa_instance): # dfa_instance is a DFA object
    output = []
    output.append(f"DFA Details:")
    if not dfa_instance or not dfa_instance.states:
        output.append("DFA not generated or empty.")
        return "\n".join(output)

    output.append(f"Number of states: {len(dfa_instance.states)}")
    output.append(f"Start State: {dfa_instance.start_state_id}")
    
    accept_states_str = []
    # Sort accept states by DFA state ID for consistent output
    for s_id, p_name in sorted(dfa_instance.accept_states.items()):
        accept_states_str.append(f"{s_id}({p_name})")
    output.append(f"Accept States (ID(Pattern)): {', '.join(accept_states_str) if accept_states_str else 'None'}")
    
    output.append(f"Alphabet: {{ {', '.join(sorted(list(dfa_instance.alphabet)))} }}")
    
    output.append("\nTransition Table (State, Symbol -> NextState):")
    # Sort alphabet for header and columns
    sorted_alphabet = sorted(list(dfa_instance.alphabet))
    header = ["State"] + sorted_alphabet
    output.append("\t".join(header))

    # Sort DFA states by ID for rows
    for state_id in sorted(list(dfa_instance.states)):
        row_cells = []
        prefix = ""
        if state_id == dfa_instance.start_state_id:
            prefix += "->"
        if state_id in dfa_instance.accept_states:
            prefix += f"*{dfa_instance.accept_states[state_id]} " # Add pattern name
        
        row_cells.append(prefix + str(state_id))
        
        for symbol in sorted_alphabet:
            next_state = dfa_instance.transitions.get((state_id, symbol), '-')
            row_cells.append(str(next_state))
        output.append("\t".join(row_cells))
    
    return "\n".join(output)

def get_dfa_anexo_ii_format(dfa_instance): # dfa_instance is a DFA object
    if not dfa_instance or not dfa_instance.states: return "DFA not available"
    lines = []
    lines.append(str(len(dfa_instance.states)))
    lines.append(str(dfa_instance.start_state_id))
    # Sort accept state IDs for consistent output
    lines.append(",".join(map(str, sorted(list(dfa_instance.accept_states.keys())))))
    # Sort alphabet for consistent output
    lines.append(",".join(sorted(list(dfa_instance.alphabet))))
    # Sort transitions for consistent output: by from_state, then by symbol
    for (from_s, sym), to_s in sorted(dfa_instance.transitions.items()):
        lines.append(f"{from_s},{sym},{to_s}")
    return "\n".join(lines)