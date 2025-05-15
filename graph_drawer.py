# graph_drawer.py
import graphviz
import os # Para manipulação de caminhos e verificação de executável
import webbrowser # Para abrir a imagem

def draw_dfa_to_file(dfa, filename_prefix="dfa_graph", view=True):
    if not dfa or not dfa.states:
        print("DFA está vazio ou não foi gerado. Nada para desenhar.")
        return None

    dot = graphviz.Digraph(comment=f'DFA for {filename_prefix}', engine='dot')
    dot.attr(rankdir='LR') # Desenha da esquerda para a direita

    # Adiciona um nó inicial invisível para apontar para o estado inicial real
    dot.node('__start__', shape='none', label='', width='0', height='0')

    for state_id in sorted(list(dfa.states)):
        shape = 'doublecircle' if state_id in dfa.accept_states else 'circle'
        label = str(state_id)
        if state_id in dfa.accept_states:
            # Adiciona o nome do padrão ao rótulo se for um estado de aceitação
            label += f"\n({dfa.accept_states[state_id]})" 
        
        dot.node(str(state_id), label=label, shape=shape)

    # Adiciona a seta para o estado inicial
    if dfa.start_state_id is not None:
        dot.edge('__start__', str(dfa.start_state_id))

    # Adiciona transições
    # Agrupa transições entre os mesmos dois estados com múltiplos símbolos
    edges = {} # (from_state_str, to_state_str) -> [symbols]
    for (from_s, symbol), to_s in dfa.transitions.items():
        from_s_str = str(from_s)
        to_s_str = str(to_s)
        key = (from_s_str, to_s_str)
        if key not in edges:
            edges[key] = []
        edges[key].append(str(symbol)) # Garante que o símbolo é string

    for (from_s_str, to_s_str), symbols in edges.items():
        # Ordena os símbolos para consistência e junta-os
        label = ", ".join(sorted(symbols))
        dot.edge(from_s_str, to_s_str, label=label)
    
    output_filename = f"{filename_prefix}" # O format 'png' será adicionado por render
    try:
        # Tenta renderizar para PNG. Se o executável dot não estiver no PATH, isso falhará.
        rendered_path = dot.render(output_filename, format='png', cleanup=True, quiet=True)
        print(f"DFA desenhado em: {rendered_path}")
        if view:
            try:
                webbrowser.open('file://' + os.path.realpath(rendered_path))
            except Exception as e_open:
                print(f"Não foi possível abrir a imagem automaticamente: {e_open}")
        return rendered_path
    except graphviz.backend.execute.ExecutableNotFound:
        print("ERRO: Executável 'dot' do Graphviz não encontrado no PATH do sistema.")
        print("Por favor, instale Graphviz (graphviz.org/download/) e adicione seu diretório 'bin' ao PATH.")
        # Salva o arquivo .gv (DOT source) para que possa ser compilado manualmente
        dot_filepath = dot.save(filename=f"{filename_prefix}.gv")
        print(f"Arquivo DOT salvo em: {dot_filepath}. Você pode compilá-lo manualmente com: dot -Tpng {dot_filepath} -o {output_filename}.png")
        return None
    except Exception as e_render:
        print(f"Erro ao renderizar o grafo do DFA: {e_render}")
        dot_filepath = dot.save(filename=f"{filename_prefix}.gv")
        print(f"Arquivo DOT salvo em: {dot_filepath} devido ao erro de renderização.")
        return None