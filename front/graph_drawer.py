import graphviz
import os
import webbrowser

def draw_dfa_to_file(dfa, filename_prefix="dfa_graph", output_subdir="imagens", view=True):
    if not dfa or not dfa.states:
        print("DFA está vazio ou não foi gerado. Nada para desenhar.")
        return None

    # Garante que o subdiretório de saída exista
    if not os.path.exists(output_subdir):
        try:
            os.makedirs(output_subdir)
            print(f"Subdiretório '{output_subdir}' criado.")
        except OSError as e:
            print(f"Erro ao criar subdiretório '{output_subdir}': {e}")
            # Tenta salvar no diretório atual como fallback
            output_subdir = "." 
    
    # Caminho completo para o arquivo de saída, sem extensão
    base_output_path = os.path.join(output_subdir, filename_prefix)


    dot = graphviz.Digraph(comment=f'DFA for {filename_prefix}', engine='dot')
    dot.attr(rankdir='LR') 

    dot.node('__start__', shape='none', label='', width='0', height='0')

    for state_id in sorted(list(dfa.states)):
        shape = 'doublecircle' if state_id in dfa.accept_states else 'circle'
        label = str(state_id)
        if state_id in dfa.accept_states:
            label += f"\n({dfa.accept_states[state_id]})" 
        
        dot.node(str(state_id), label=label, shape=shape)

    if dfa.start_state_id is not None:
        dot.edge('__start__', str(dfa.start_state_id))

    edges = {}
    for (from_s, symbol), to_s in dfa.transitions.items():
        from_s_str = str(from_s)
        to_s_str = str(to_s)
        key = (from_s_str, to_s_str)
        if key not in edges:
            edges[key] = []
        edges[key].append(str(symbol))

    for (from_s_str, to_s_str), symbols in edges.items():
        label = ", ".join(sorted(symbols))
        dot.edge(from_s_str, to_s_str, label=label)
    
    try:
        rendered_path_with_ext = dot.render(filename=base_output_path, format='png', cleanup=True, quiet=True)
        
        if not rendered_path_with_ext.lower().endswith('.png'):
             rendered_path_with_ext += '.png' # graphviz <0.17 might not add extension to returned path
        
        # Verificar se o arquivo realmente foi criado no caminho esperado
        if not os.path.exists(rendered_path_with_ext):
            # Tentar um caminho alternativo se o graphviz se comportou de forma inesperada
            alt_path = base_output_path + ".png"
            if os.path.exists(alt_path):
                rendered_path_with_ext = alt_path
            else:
                print(f"Arquivo de imagem não encontrado em '{rendered_path_with_ext}' ou '{alt_path}'. Verifique a saída do Graphviz.")
                # Salvar o arquivo .gv como fallback
                dot_filepath_fallback = dot.save(filename=f"{base_output_path}.gv")
                print(f"Arquivo DOT salvo em: {dot_filepath_fallback} para compilação manual.")
                return None


        print(f"DFA desenhado em: {os.path.abspath(rendered_path_with_ext)}")
        if view:
            try:
                # Usar file URI scheme para compatibilidade
                file_uri = 'file:///' + os.path.abspath(rendered_path_with_ext).replace('\\', '/')
                webbrowser.open(file_uri)
            except Exception as e_open:
                print(f"Não foi possível abrir a imagem automaticamente: {e_open}")
        return os.path.abspath(rendered_path_with_ext)
    except graphviz.backend.execute.ExecutableNotFound:
        print("ERRO: Executável 'dot' do Graphviz não encontrado no PATH do sistema.")
        print("Por favor, instale Graphviz (graphviz.org/download/) e adicione seu diretório 'bin' ao PATH.")
        dot_filepath = dot.save(filename=f"{base_output_path}.gv")
        print(f"Arquivo DOT salvo em: {dot_filepath}. Você pode compilá-lo manualmente com: dot -Tpng {dot_filepath} -o {base_output_path}.png")
        return None
    except Exception as e_render:
        print(f"Erro ao renderizar o grafo do DFA: {e_render}")
        dot_filepath = dot.save(filename=f"{base_output_path}.gv")
        print(f"Arquivo DOT salvo em: {dot_filepath} devido ao erro de renderização.")
        return None