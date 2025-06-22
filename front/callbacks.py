from tkinter import filedialog, messagebox
import os
from PIL import Image
import customtkinter as ctk
import traceback

from core.automata import (NFA, DFA, NFAState, postfix_to_nfa, _finalize_nfa_properties,
                           combine_nfas, construct_unminimized_dfa_from_nfa, _minimize_dfa)
from core.lexer_core import Lexer, parse_re_file_data, SymbolTable
from core.regex_utils import infix_to_postfix
from core.syntax_tree_direct_dfa import regex_to_direct_dfa
from core.syntactic.grammar import Grammar
from core.syntactic.slr_generator import SLRGenerator
from core.syntactic.slr_parser import SLRParser

from .graph_drawer import draw_dfa_to_file
from .ui_formatters import (get_nfa_details_str, get_dfa_table_str, get_dfa_anexo_ii_format,
                            get_grammar_details_str, get_first_follow_sets_str,
                            get_canonical_collection_str, get_slr_table_str, get_parse_steps_str)
from .ui_utils import update_display_tab, clear_dfa_image


def load_re_from_file_for_current_mode_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return
    filepath = filedialog.askopenfilename(title="Carregar Definições Regulares", filetypes=(("Text files", "*.txt"), ("RE files", "*.re"), ("All files", "*.*")))
    if filepath:
        try:
            with open(filepath, 'r', encoding='utf-8') as f_in: content = f_in.read()
            app_instance._set_re_definitions_for_current_mode(content)
            method_name = app_instance.active_construction_method.replace('_', ' ').capitalize()
            app_instance.current_test_name = f"Arquivo ({method_name}): {filepath.split('/')[-1]}"
            messagebox.showinfo("Sucesso", f"Arquivo '{filepath.split('/')[-1]}' carregado.")
        except Exception as e: messagebox.showerror("Erro ao Ler Arquivo", str(e))

def load_test_data_for_auto_mode_callback(app_instance, test_case, show_message=True):
    if app_instance.current_frame_name != "AutoTestMode": app_instance.show_frame("AutoTestMode")
    app_instance.active_construction_method = "thompson"
    app_instance._set_re_definitions_for_current_mode(test_case["re_definitions"])
    app_instance._set_source_code_for_current_mode(test_case["source_code"])
    app_instance.current_test_name = test_case["name"]
    if show_message and hasattr(app_instance, 'auto_test_mode_widgets') and app_instance.auto_test_mode_widgets["control_frame"].winfo_ismapped():
         messagebox.showinfo("Teste Carregado", f"Teste '{test_case['name']}' carregado (via Thompson).")

def process_regular_expressions_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return

    re_content_for_parsing = ""
    if app_instance.current_frame_name != "FullTestMode":
        re_input_tb = widgets.get("re_input_textbox")
        if not re_input_tb:
            messagebox.showerror("Erro Interno", "Textbox de input de RE não encontrado.")
            return
        re_content_for_parsing = re_input_tb.get("1.0", "end-1c").strip()
        if not re_content_for_parsing: 
            messagebox.showerror("Entrada Vazia", "Nenhuma definição regular fornecida."); return
        
        try:
            app_instance.definitions, app_instance.pattern_order, app_instance.reserved_words_defs, app_instance.patterns_to_ignore = parse_re_file_data(re_content_for_parsing)
        except Exception as e:
            messagebox.showerror("Erro ao Parsear Definições", f"Erro: {e}")
            return
    
    app_instance.display_definitions_and_reserved_words()
    
    construction_details_builder = [f"Processando Definições ({app_instance.current_test_name}):\n"]
    if app_instance.patterns_to_ignore: construction_details_builder.append(f"(Padrões ignorados: {', '.join(sorted(list(app_instance.patterns_to_ignore)))})\n")
    construction_details_builder.append("\n")
    
    process_successful = False
    
    try:
        if app_instance.active_construction_method == "thompson":
            NFA.reset_state_ids() 
            DFA._next_dfa_id = 0 
            DFA._state_map = {}  
            has_any_valid_nfa = False
            for name in app_instance.pattern_order:
                regex_str = app_instance.definitions.get(name, "")
                if not regex_str: continue
                construction_details_builder.append(f"Definição: {name}: {regex_str}\n")
                try:
                    postfix_expr_tokens = infix_to_postfix(regex_str)
                    postfix_expr_str_display = "".join(postfix_expr_tokens)
                    construction_details_builder.append(f"  Pós-fixada: {postfix_expr_str_display if postfix_expr_str_display else '(VAZIA)'}\n")
                    nfa = postfix_to_nfa(postfix_expr_tokens)
                    if nfa: 
                        app_instance.individual_nfas[name] = nfa
                        construction_details_builder.append(get_nfa_details_str(nfa, f"NFA para '{name}'") + "\n\n")
                        has_any_valid_nfa = True
                    else: construction_details_builder.append("  NFA: (Não gerado)\n\n")
                except Exception as ve_re: construction_details_builder.append(f"  ERRO NFA '{name}': {ve_re}\n\n")
            process_successful = has_any_valid_nfa
            if process_successful and widgets.get("combine_nfas_button") and app_instance.current_frame_name != "FullTestMode": 
                widgets["combine_nfas_button"].configure(state="normal")

        elif app_instance.active_construction_method == "tree_direct_dfa":
            DFA._next_dfa_id = 0 
            DFA._state_map = {}  
            
            if not app_instance.pattern_order or not app_instance.definitions:
                update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", "Nenhuma definição de RE para Followpos.")
                if app_instance.current_frame_name != "FullTestMode":
                    messagebox.showwarning("Entrada Vazia", "Nenhuma definição de RE para Followpos.")
                return

            direct_dfa, aug_tree, pos_map, pseudo_nfa_union_display = regex_to_direct_dfa(
                app_instance.definitions, 
                app_instance.pattern_order
            )
            
            followpos_nfa_union_tab_content = []
            if pseudo_nfa_union_display:
                accept_map_for_disp = getattr(pseudo_nfa_union_display, 'accept_map_for_display', None)
                followpos_nfa_union_tab_content.append(get_nfa_details_str(pseudo_nfa_union_display, "NFA Combinado Conceitual (União ε para Followpos)", combined_accept_map=accept_map_for_disp))
                followpos_nfa_union_tab_content.append("\n\n====================\n\n")
            else:
                followpos_nfa_union_tab_content.append("NFA Combinado Conceitual (União ε para Followpos): Não gerado ou falha.\n\n====================\n\n")

            if direct_dfa:
                followpos_nfa_union_tab_content.append(get_dfa_table_str(direct_dfa, f"AFD Direto Consolidado (Não-Minimizado)"))
            else:
                followpos_nfa_union_tab_content.append("AFD Direto Consolidado (Não-Minimizado): Falha na geração.")

            update_display_tab(widgets, "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", "\n".join(followpos_nfa_union_tab_content))

            if direct_dfa and aug_tree and pos_map:
                app_instance.unminimized_dfa = direct_dfa 
                app_instance.augmented_syntax_tree_followpos = aug_tree
                app_instance.followpos_table_followpos = pos_map
                
                construction_details_builder.append(f"Construindo AFD Direto (Followpos) para TODAS as definições:\n")
                construction_details_builder.append(f"  Árvore Aumentada Combinada:\n{aug_tree}\n") 
                
                fp_details = ["  Tabela Followpos (Consolidada):"]
                sorted_pos_ids = sorted(pos_map.keys())
                for pid_sorted in sorted_pos_ids:
                    pnode = pos_map[pid_sorted]
                    fp_obj_ids_sorted = sorted([fp_obj.id for fp_obj in pnode.followpos])
                    fp_details.append(f"    {pnode}: {{ {', '.join(map(str,fp_obj_ids_sorted))} }}")
                construction_details_builder.append("\n".join(fp_details) + "\n")
                
                process_successful = True
            else: 
                construction_details_builder.append(f"  Falha ao gerar árvore ou followpos para AFD direto consolidado.\n")
            
            if process_successful and direct_dfa and widgets.get("generate_dfa_button") and app_instance.current_frame_name != "FullTestMode": 
                widgets["generate_dfa_button"].configure(state="normal")
        
        update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", "".join(construction_details_builder))
        if widgets.get("display_tab_view") and app_instance.current_frame_name != "FullTestMode": 
             widgets["display_tab_view"].set("ER ➔ NFA Ind. / Árvore+Followpos")
        
        if app_instance.current_frame_name != "FullTestMode":
            if not process_successful:
                 messagebox.showwarning("Processamento Parcial/Falha", f"({app_instance.current_test_name}): Verifique os detalhes. Algumas etapas podem ter falhado.")
            else:
                messagebox.showinfo("Sucesso (Etapa A)", f"({app_instance.current_test_name}): Processamento de REs concluído.")

    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}\n\nTraceback:\n{tb_str}"
        messagebox.showerror("Erro na Etapa A", error_message)
        update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", f"Erro: {str(e)}\n{tb_str}")


def combine_all_nfas_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets or app_instance.active_construction_method != "thompson": return
    if not app_instance.individual_nfas: messagebox.showerror("Sem NFAs", "Nenhum NFA individual (Thompson) para combinar."); return
    
    nfas_for_combination = {k: v for k,v in app_instance.individual_nfas.items() if v is not None}
    if not nfas_for_combination: messagebox.showerror("Sem NFAs Válidos", "Nenhum NFA individual válido para combinar."); return
    
    try:
        DFA._next_dfa_id = 0 
        DFA._state_map = {}

        app_instance.combined_nfa_start_obj, app_instance.combined_nfa_accept_map, app_instance.combined_nfa_alphabet = combine_nfas(nfas_for_combination)
        if not app_instance.combined_nfa_start_obj:
            messagebox.showerror("Erro União NFA", "Falha ao criar NFA combinado."); return
        
        combined_nfa_shell = NFA(app_instance.combined_nfa_start_obj, None)
        display_str_builder = [get_nfa_details_str(combined_nfa_shell, "NFA Combinado Global (Após União ε)", combined_accept_map=app_instance.combined_nfa_accept_map)]
        
        app_instance.unminimized_dfa = construct_unminimized_dfa_from_nfa(
            app_instance.combined_nfa_start_obj, app_instance.combined_nfa_accept_map,
            app_instance.combined_nfa_alphabet, app_instance.pattern_order
        )
        display_str_builder.append("\n\n====================\n\n")
        display_str_builder.append(get_dfa_table_str(app_instance.unminimized_dfa, title_prefix="AFD Não Minimizado (Após Determinização): "))

        update_display_tab(widgets, "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", "\n".join(display_str_builder))
        if widgets.get("display_tab_view") and app_instance.current_frame_name != "FullTestMode":
            widgets["display_tab_view"].set("NFA Combinado (União ε) / AFD Direto (Não-Minim.)")
        if widgets.get("generate_dfa_button") and app_instance.current_frame_name != "FullTestMode": 
            widgets["generate_dfa_button"].configure(state="normal")
        if app_instance.current_frame_name != "FullTestMode":
            messagebox.showinfo("Sucesso (Etapa B - Thompson)", "NFAs combinados e AFD não minimizado gerado.")
    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = f"{type(e).__name__}: {str(e)}\n\nTraceback:\n{tb_str}"
        messagebox.showerror("Erro Etapa B - Thompson", error_message)
        update_display_tab(widgets, "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", f"Erro: {str(e)}\n{tb_str}")

def generate_final_dfa_and_minimize_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return

    app_instance.dfa = None 
    dfa_tables_display_builder = []
    
    try:
        if not app_instance.unminimized_dfa:
            if app_instance.current_frame_name != "FullTestMode": 
                messagebox.showerror("Processo Incompleto", "O AFD não minimizado (da Etapa B ou A-Followpos) não foi gerado.")
            return

        dfa_tables_display_builder.append(get_dfa_table_str(app_instance.unminimized_dfa, title_prefix="AFD Não Minimizado (Entrada para Minimização): "))
        
        app_instance.dfa = _minimize_dfa(app_instance.unminimized_dfa)
        dfa_tables_display_builder.append(get_dfa_table_str(app_instance.dfa, title_prefix="AFD Minimizado (Final): "))
        
        update_display_tab(widgets, "AFD Minimizado (Final)", "\n\n====================\n\n".join(dfa_tables_display_builder))
        if widgets.get("display_tab_view") and app_instance.current_frame_name != "FullTestMode":
             widgets["display_tab_view"].set("AFD Minimizado (Final)")
        
        app_instance.lexer = Lexer(app_instance.dfa, app_instance.reserved_words_defs, app_instance.patterns_to_ignore, app_instance.symbol_table_instance)

        if app_instance.current_frame_name != "FullTestMode":
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="normal")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="normal")
            if widgets.get("draw_dfa_button"): widgets["draw_dfa_button"].configure(state="normal")
            messagebox.showinfo("Sucesso (Etapa C - Minimização)", "AFD Minimizado gerado. Lexer pronto.")

    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}\n\nTraceback:\n{tb_str}"
        messagebox.showerror("Erro Etapa C - Minimização", error_message)
        update_display_tab(widgets, "AFD Minimizado (Final)", f"Erro: {str(e)}\n{tb_str}")
        if app_instance.current_frame_name != "FullTestMode":
            for btn_key in ["tokenize_button", "save_dfa_button", "draw_dfa_button"]:
                if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")

def draw_current_minimized_dfa_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return

    dfa_img_label_current = widgets.get("dfa_image_label")

    if not app_instance.dfa:
        if app_instance.current_frame_name != "FullTestMode":
            messagebox.showerror("Sem AFD", "Nenhum AFD minimizado para desenhar. Gere o AFD primeiro.")
        if dfa_img_label_current: dfa_img_label_current.configure(image=None, text="Nenhum AFD minimizado disponível.")
        return
    
    test_name_slug = "".join(c if c.isalnum() else "_" for c in app_instance.current_test_name)
    if not test_name_slug: test_name_slug = "default_test" 
    filename_prefix = f"dfa_graph_{test_name_slug}"
    
    try:
        image_path = draw_dfa_to_file(app_instance.dfa, filename_prefix=filename_prefix, output_subdir=app_instance.images_output_dir, view=False)
        
        if image_path and os.path.exists(image_path):
            pil_image = Image.open(image_path)
            
            original_width, original_height = pil_image.size
            tab_widget_for_drawing = None
            tab_view_widget = widgets.get("display_tab_view")

            if tab_view_widget:
                 try:
                    if "Desenho AFD Minimizado" in tab_view_widget._name_list:
                        tab_index = tab_view_widget._name_list.index("Desenho AFD Minimizado")
                        tab_widget_for_drawing = tab_view_widget._tab_dict["Desenho AFD Minimizado"]
                    else: 
                        tab_widget_for_drawing = tab_view_widget 
                 except (AttributeError, ValueError, KeyError): 
                    tab_widget_for_drawing = tab_view_widget 

            max_tab_width = tab_widget_for_drawing.winfo_width() if tab_widget_for_drawing and tab_widget_for_drawing.winfo_width() > 20 else 700 
            max_tab_height = tab_widget_for_drawing.winfo_height() if tab_widget_for_drawing and tab_widget_for_drawing.winfo_height() > 20 else 500

            img_aspect_ratio = original_width / original_height if original_height > 0 else 1
            
            new_width = original_width
            new_height = original_height

            if new_width > max_tab_width:
                new_width = max_tab_width
                new_height = int(new_width / img_aspect_ratio) if img_aspect_ratio != 0 else max_tab_height
            
            if new_height > max_tab_height:
                new_height = max_tab_height
                new_width = int(new_height * img_aspect_ratio) if img_aspect_ratio != 0 else max_tab_width 

            if new_width > max_tab_width:
                new_width = max_tab_width
                new_height = int(new_width / img_aspect_ratio) if img_aspect_ratio != 0 else max_tab_height

            new_width = max(1, int(new_width)) 
            new_height = max(1, int(new_height)) 

            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width, resized_image.height))
            
            if dfa_img_label_current:
                dfa_img_label_current.configure(image=ctk_image, text="") 
                dfa_img_label_current.image = ctk_image 
            
            if tab_view_widget and "Desenho AFD Minimizado" in tab_view_widget._name_list:
                try:
                    tab_view_widget.set("Desenho AFD Minimizado")
                except Exception: 
                    pass 
            if app_instance.current_frame_name != "FullTestMode":
                messagebox.showinfo("Desenho AFD", f"Desenho do AFD exibido e salvo em:\n{image_path}")
        else:
            if dfa_img_label_current:
                dfa_img_label_current.configure(image=None, text="Falha ao gerar/encontrar imagem do AFD.")
            if app_instance.current_frame_name != "FullTestMode":
                messagebox.showwarning("Desenho AFD", "Não foi possível gerar ou encontrar a imagem do AFD. Verifique o console.")
    except Exception as e:
        tb_str = traceback.format_exc()
        if dfa_img_label_current:
            dfa_img_label_current.configure(image=None, text=f"Erro ao desenhar AFD: {type(e).__name__}")
        if app_instance.current_frame_name != "FullTestMode":
            messagebox.showerror("Erro ao Desenhar AFD", f"Ocorreu um erro: {e}\n\nTraceback:\n{tb_str}")

def save_dfa_to_file_callback(app_instance):
    if not app_instance.dfa: messagebox.showerror("Sem AFD Minimizado", "Nenhum AFD minimizado para salvar."); return
    filepath = filedialog.asksaveasfilename(defaultextension=".dfa.txt", filetypes=(("DFA Text files", "*.dfa.txt"),("Text files", "*.txt"), ("All files", "*.*")), title=f"Salvar Tabela AFD Minimizada ({app_instance.current_test_name})")
    if filepath:
        try:
            anexo_ii_content = get_dfa_anexo_ii_format(app_instance.dfa)
            with open(filepath, 'w', encoding='utf-8') as f_out: f_out.write(anexo_ii_content)
            
            base_name, ext = os.path.splitext(filepath)

            hr_filepath_min = f"{base_name}_min_readable.txt"
            hr_content_min = get_dfa_table_str(app_instance.dfa, title_prefix="Minimized ");
            with open(hr_filepath_min, 'w', encoding='utf-8') as f_hr_min: f_hr_min.write(hr_content_min)

            if app_instance.unminimized_dfa:
                hr_filepath_unmin = f"{base_name}_unmin_readable.txt"
                hr_content_unmin = get_dfa_table_str(app_instance.unminimized_dfa, title_prefix="Unminimized ");
                with open(hr_filepath_unmin, 'w', encoding='utf-8') as f_hr_unmin: f_hr_unmin.write(hr_content_unmin)

            messagebox.showinfo("Sucesso", "Tabela AFD Minimizada (Anexo II) e versões legíveis salvas.")
        except Exception as e: messagebox.showerror("Erro Salvar AFD", str(e))

def process_grammar_callback(app_instance):
    widgets = app_instance.syntactic_mode_widgets
    grammar_text = widgets["grammar_input"].get("1.0", "end-1c")
    if not grammar_text.strip():
        messagebox.showerror("Erro", "A definição da gramática está vazia.")
        return
    
    try:
        app_instance.grammar = Grammar.from_text(grammar_text)
        update_display_tab(widgets, "Detalhes da Gramática", get_grammar_details_str(app_instance.grammar))

        generator = SLRGenerator(app_instance.grammar)
        
        firsts = generator.compute_first_sets()
        follows = generator.compute_follow_sets()
        update_display_tab(widgets, "Conjuntos First & Follow", get_first_follow_sets_str(firsts, follows))

        collection, _ = generator.build_canonical_collection()
        update_display_tab(widgets, "Coleção Canônica LR(0)", get_canonical_collection_str(collection))
        
        action_table, goto_table = generator.build_slr_table()
        app_instance.slr_action_table = action_table
        app_instance.slr_goto_table = goto_table
        update_display_tab(widgets, "Tabela de Análise SLR", get_slr_table_str(action_table, goto_table, app_instance.grammar))

        widgets["parse_button"].configure(state="normal")
        widgets["display_tab_view"].set("Tabela de Análise SLR")
        messagebox.showinfo("Sucesso", "Gramática processada e Tabela SLR gerada com sucesso.")

    except Exception as e:
        tb_str = traceback.format_exc()
        messagebox.showerror("Erro ao Processar Gramática", f"Ocorreu um erro: {e}\n\nTraceback:\n{tb_str}")
        widgets["parse_button"].configure(state="disabled")

def run_parser_callback(app_instance):
    widgets = app_instance.syntactic_mode_widgets
    if not app_instance.grammar or not app_instance.slr_action_table:
        messagebox.showerror("Erro", "Gramática não processada ou tabela SLR não gerada.")
        return

    token_stream_text = widgets["token_stream_input"].get("1.0", "end-1c").strip()
    
    token_stream = []
    if token_stream_text:
        try:
            for line_num, line in enumerate(token_stream_text.splitlines()):
                line = line.strip()
                if not line: continue
                
                token_type = ""
                attribute = None
                
                if line == ',':
                    token_type = ','
                else:
                    parts = line.split(',', 1)
                    token_type = parts[0].strip()
                    if len(parts) > 1:
                        attribute = parts[1].strip()

                if not token_type:
                    raise ValueError(f"Tipo de token vazio na linha {line_num + 1}")
                
                token_stream.append( ('', token_type, attribute) )
        except Exception as e:
            messagebox.showerror("Erro de Formato de Token", f"Linha mal formada: '{line}'.\nUse o formato 'TIPO' ou 'TIPO,ATRIBUTO'.\nDetalhes: {e}")
            return
    
    try:
        parser = SLRParser(app_instance.grammar, app_instance.slr_action_table, app_instance.slr_goto_table)
        steps, success, message = parser.parse(token_stream)
        
        update_display_tab(widgets, "Passos da Análise", get_parse_steps_str(steps, success, message))
        widgets["display_tab_view"].set("Passos da Análise")
        
        if success:
            messagebox.showinfo("Análise Concluída", message)
        else:
            messagebox.showerror("Análise Concluída", message)

    except Exception as e:
        tb_str = traceback.format_exc()
        messagebox.showerror("Erro na Análise Sintática", f"{e}\n\n{tb_str}")

def tokenize_source_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return
    if not app_instance.lexer: 
        if app_instance.current_frame_name != "FullTestMode":
            messagebox.showerror("Lexer Indisponível", "Analisador Léxico não gerado. Execute todas as etapas de construção primeiro."); 
        return
    
    source_code = ""
    if app_instance.current_frame_name == "FullTestMode":
        source_code_tb = widgets.get("source_display_textbox")
        if source_code_tb: source_code = source_code_tb.get("1.0", "end-1c")
    else:
        source_code_tb = widgets.get("source_code_input_textbox")
        if source_code_tb: source_code = source_code_tb.get("1.0", "end-1c")

    if not source_code: 
        update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", "(Nenhum texto fonte)"); 
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", "Tabela de Símbolos (Dinâmica):\n(Nenhum texto fonte para analisar)")
        return
    
    try:
        tokens_data_list, populated_symbol_table = app_instance.lexer.tokenize(source_code)
        
        output_lines = [f"Tokens Gerados ({app_instance.current_test_name} - com AFD Minimizado):\n"]
        if not tokens_data_list: 
            output_lines.append("(Nenhum token reconhecido)")
        else:
            for lexema, token_type, attribute in tokens_data_list:
                if token_type == "ERRO!":
                    output_lines.append(f"<'{lexema}', {token_type}>")
                elif token_type == "ID":
                    output_lines.append(f"<'{lexema}', {token_type}> (Atributo: índice {attribute})")
                elif isinstance(attribute, (int, float)):
                     output_lines.append(f"<'{lexema}', {token_type}> (Atributo: valor {attribute})")
                else:
                    output_lines.append(f"<'{lexema}', {token_type}> (Atributo: {attribute if attribute else 'N/A'})")

        update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", "\n".join(output_lines))
        
        ts_static_part = ""
        ts_textbox = widgets.get("textboxes_map",{}).get("Tabela de Símbolos (Definições & Dinâmica)")
        if ts_textbox:
            current_ts_content = ts_textbox.get("1.0", "end-1c")
            if "Tabela de Símbolos (Dinâmica" in current_ts_content:
                ts_static_part = current_ts_content.split("\n\nTabela de Símbolos (Dinâmica")[0]
            elif "Definições de Padrões e Palavras Reservadas (Estático):" in current_ts_content:
                 ts_static_part = current_ts_content 
        if not ts_static_part.strip(): 
            ts_static_part = "Definições de Padrões e Palavras Reservadas (Estático):\n(Não exibido ou recarregado)"


        ts_dynamic_str = "\n\nTabela de Símbolos (Dinâmica - Após Análise Léxica):\n"
        ts_dynamic_str += str(populated_symbol_table)
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", ts_static_part + ts_dynamic_str)


        if widgets.get("display_tab_view") and app_instance.current_frame_name != "FullTestMode":
             widgets["display_tab_view"].set("Saída do Analisador Léxico (Tokens)")
    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}\n\nTraceback:\n{tb_str}"
        messagebox.showerror("Erro Análise Léxica", error_message)
        update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", f"Erro: {str(e)}\n{tb_str}")
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", "Tabela de Símbolos (Dinâmica - Após Análise Léxica):\n(Erro durante a análise)")