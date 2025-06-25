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


def get_dfa_table_str(dfa, title_prefix=""):
    output = []
    output.append(f"{title_prefix}DFA Transition Table & Details:")
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


def get_grammar_details_str(grammar):
    if not grammar:
        return "Gramática não disponível."
    return str(grammar)

def get_first_follow_sets_str(first_sets, follow_sets):
    if not first_sets and not follow_sets:
        return "Conjuntos First e Follow não calculados."
    
    output = ["--- Conjuntos First ---"]
    sorted_symbols = sorted(first_sets.keys())
    for symbol in sorted_symbols:
        f_set = first_sets.get(symbol, set())
        output.append(f"  First({symbol:<15}) = {{ {', '.join(sorted(list(f_set)))} }}")
    
    output.append("\n--- Conjuntos Follow ---")
    sorted_non_terminals = sorted(follow_sets.keys())
    for symbol in sorted_non_terminals:
        f_set = follow_sets.get(symbol, set())
        output.append(f"  Follow({symbol:<15}) = {{ {', '.join(sorted(list(f_set)))} }}")
        
    return "\n".join(output)

def get_canonical_collection_str(collection, goto_map=None):
    if not collection:
        return "Coleção canônica de itens LR(0) não gerada."

    output = ["--- Coleção Canônica de Itens LR(0) e Gotos ---"]
    for i, item_set in enumerate(collection):
        output.append(f"\nI{i}:")
        
        kernel_items = []
        closure_items = []

        for prod, dot_pos in item_set:
            if dot_pos > 0 or prod.number == 0:
                kernel_items.append((prod, dot_pos))
            else:
                closure_items.append((prod, dot_pos))
        
        kernel_items.sort(key=lambda x: x[0].number)
        closure_items.sort(key=lambda x: x[0].number)
        
        def format_and_add_item(item):
            prod, dot_pos = item
            body_list = list(prod.body)
            body_list.insert(dot_pos, '•')
            body_str = ' '.join(body_list) if body_list else '•'
            output.append(f"  {prod.head} ::= {body_str}")

        for item in kernel_items:
            format_and_add_item(item)
            
        if kernel_items and closure_items:
            output.append("  -----------")

        for item in closure_items:
            format_and_add_item(item)

        if goto_map:
            transitions = []
            for (from_state, symbol), to_state in goto_map.items():
                if from_state == i:
                    transitions.append((symbol, to_state))
            
            if transitions:
                output.append("\n  Gotos:")
                transitions.sort(key=lambda x: x[0])
                for symbol, to_state in transitions:
                    output.append(f"    {symbol} -> I{to_state}")
            
    return "\n".join(output)



def get_slr_table_str(action_table, goto_table, grammar):
    if not action_table and not goto_table:
        return "Tabela SLR não gerada."

    terminals = sorted(list(grammar.terminals)) + ['$']
    non_terminals = sorted([nt for nt in grammar.non_terminals if nt != grammar.augmented_start_symbol])
    
    header = ["Estado"] + terminals + non_terminals
    output = ["--- Tabela de Análise SLR ---"]
    output.append("\t".join(f"{h:<10}" for h in header))
    
    sorted_states = sorted(action_table.keys() | goto_table.keys())

    for state in sorted_states:
        row = [f"{state:<10}"]
        for term in terminals:
            action = action_table.get(state, {}).get(term, "")
            if action:
                action_str = f"{action[0][0]}{action[1]}"
                if action[0] == 'accept':
                    action_str = 'acc'
            else:
                action_str = ""
            row.append(f"{action_str:<10}")
        for nt in non_terminals:
            goto_val = goto_table.get(state, {}).get(nt, "")
            row.append(f"{str(goto_val):<10}")
        output.append("\t".join(row))
        
    return "\n".join(output)

def get_parse_steps_str(steps, success, message):
    if not steps:
        return "Nenhuma etapa de análise para exibir."
    
    output = ["--- Passos da Análise Sintática ---"]
    header = f"{'Pilha':<40} | {'Entrada Restante':<40} | {'Ação'}"
    output.append(header)
    output.append("-" * (len(header) + 5))

    for step in steps:
        output.append(f"{step['stack']:<40} | {step['input']:<40} | {step['action']}")
    
    output.append("\n" + "="*30)
    output.append(f"Resultado: {message}")
    output.append("="*30)
    
    return "\n".join(output)
