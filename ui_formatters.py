# ui_formatters.py
def get_nfa_details_str(nfa_obj, name="NFA", combined_accept_map=None):
    output = []
    output.append(f"--- {name} Details ---")

    if not hasattr(nfa_obj, 'start_state') or not nfa_obj.start_state:
        output.append("NFA is empty or not properly initialized.")
        return "\n".join(output)

    states_to_print = set()
    if hasattr(nfa_obj, 'states') and nfa_obj.states:
        states_to_print.update(nfa_obj.states)

    if nfa_obj.start_state: states_to_print.add(nfa_obj.start_state)
    if hasattr(nfa_obj, 'accept_state') and nfa_obj.accept_state: states_to_print.add(nfa_obj.accept_state)
    if combined_accept_map:
        for s_obj in combined_accept_map.keys(): states_to_print.add(s_obj)
    
    q_bfs = []
    if nfa_obj.start_state: q_bfs.append(nfa_obj.start_state)
    
    visited_for_print = set()
    if nfa_obj.start_state: visited_for_print.add(nfa_obj.start_state)

    head = 0
    while head < len(q_bfs):
        curr = q_bfs[head]
        head += 1
        states_to_print.add(curr)
        for symbol, next_states_set in curr.transitions.items():
            for next_s in next_states_set:
                states_to_print.add(next_s)
                if next_s not in visited_for_print:
                    visited_for_print.add(next_s)
                    q_bfs.append(next_s)
    
    sorted_states_list = sorted(list(states_to_print), key=lambda s: s.id)

    output.append(f"Start State: S{nfa_obj.start_state.id}")
    
    accept_display_parts = []
    if hasattr(nfa_obj, 'accept_state') and nfa_obj.accept_state in states_to_print :
        pattern_name_guess = name.split("'")[1] if "'" in name else "Current"
        accept_display_parts.append(f"S{nfa_obj.accept_state.id} (Pattern: {pattern_name_guess})")

    if combined_accept_map:
        for s_obj, pat_name in combined_accept_map.items():
            if s_obj in states_to_print:
                accept_display_parts.append(f"S{s_obj.id}({pat_name})")
    
    output.append(f"Accept State(s): {', '.join(sorted(list(set(accept_display_parts)))) if accept_display_parts else 'None'}")

    output.append("Transitions (State, Symbol -> NextStates):")
    for s in sorted_states_list:
        if s.transitions:
            for symbol, next_states_set in sorted(s.transitions.items()):
                sorted_next_ids = sorted([f"S{ns.id}" for ns in next_states_set])
                output.append(f"  S{s.id}, {symbol if symbol else 'ε'} -> {{{', '.join(sorted_next_ids)}}}")
    output.append("--------------------")
    return "\n".join(output)


def get_dfa_table_str(dfa, title_prefix=""): # Added title_prefix
    output = []
    output.append(f"{title_prefix}DFA Transition Table & Details:") # Used title_prefix
    if not dfa or not dfa.states:
        output.append(f"{title_prefix}DFA not generated or empty.")
        return "\n".join(output)

    output.append(f"Number of states: {len(dfa.states)}")
    output.append(f"Start State: {dfa.start_state_id}")
    
    accept_states_str_parts = [f"{s_id}({p_name})" for s_id, p_name in sorted(dfa.accept_states.items())]
    output.append(f"Accept States (ID(Pattern)): {', '.join(accept_states_str_parts) if accept_states_str_parts else 'None'}")
    
    sorted_alphabet = sorted(list(dfa.alphabet))
    output.append(f"Alphabet: {{ {', '.join(sorted_alphabet)} }}")
    
    output.append("\nTransition Table:")
    header = ["State".ljust(8)] + [sym.center(max(len(sym),5)) for sym in sorted_alphabet]
    output.append("\t".join(header))
    output.append("-" * (len(header[0]) + sum(len(h) for h in header[1:]) + len(header[1:])*4 ))


    for state_id in sorted(list(dfa.states)):
        row_parts = []
        prefix = ""
        if state_id == dfa.start_state_id: prefix += "->"
        if state_id in dfa.accept_states: prefix += f"*{dfa.accept_states[state_id]}"
        
        row_parts.append((prefix + str(state_id)).ljust(8))
        
        for symbol in sorted_alphabet:
            next_state = dfa.transitions.get((state_id, symbol), '-')
            row_parts.append(str(next_state).center(max(len(symbol),5)))
        output.append("\t".join(row_parts))
    
    return "\n".join(output)

def get_dfa_anexo_ii_format(dfa):
    if not dfa or not dfa.states: return "DFA not available for Anexo II format."
    lines = []
    lines.append(str(len(dfa.states)))
    lines.append(str(dfa.start_state_id))
    lines.append(",".join(map(str, sorted(list(dfa.accept_states.keys())))))
    lines.append(",".join(sorted(list(dfa.alphabet))))
    
    sorted_transitions = sorted(dfa.transitions.items(), key=lambda item: (item[0][0], str(item[0][1])))
    for (from_s, sym), to_s in sorted_transitions:
        lines.append(f"{from_s},{sym},{to_s}")
    return "\n".join(lines)