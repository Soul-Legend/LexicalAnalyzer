from tkinter import filedialog, messagebox
import os
from PIL import Image
import customtkinter as ctk 

from automata import (NFA, DFA, NFAState, postfix_to_nfa, _finalize_nfa_properties,
                      combine_nfas, construct_unminimized_dfa_from_nfa, _minimize_dfa)
from lexer_core import Lexer, parse_re_file_data, SymbolTable
from regex_utils import infix_to_postfix
from syntax_tree_direct_dfa import regex_to_direct_dfa, PositionNode
from graph_drawer import draw_dfa_to_file
from ui_formatters import get_nfa_details_str, get_dfa_table_str, get_dfa_anexo_ii_format
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
    re_content = widgets["re_input_textbox"].get("1.0", "end-1c").strip()
    if not re_content: messagebox.showerror("Entrada Vazia", "Nenhuma definição regular fornecida."); return
    
    app_instance.reset_app_state()
    
    try:
        NFA.reset_state_ids()
        PositionNode.reset_id_counter()
        DFA._next_dfa_id = 0 
        DFA._state_map = {}  

        app_instance.definitions, app_instance.pattern_order, app_instance.reserved_words_defs, app_instance.patterns_to_ignore = parse_re_file_data(re_content)
        app_instance.display_definitions_and_reserved_words()
        
        construction_details_builder = [f"Processando Definições ({app_instance.current_test_name}):\n"]
        if app_instance.patterns_to_ignore: construction_details_builder.append(f"(Padrões ignorados: {', '.join(sorted(list(app_instance.patterns_to_ignore)))})\n")
        construction_details_builder.append("\n")
        
        process_successful = False

        if app_instance.active_construction_method == "thompson":
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
            if process_successful and widgets.get("combine_nfas_button"): widgets["combine_nfas_button"].configure(state="normal")

        elif app_instance.active_construction_method == "tree_direct_dfa":
            if not app_instance.pattern_order:
                messagebox.showerror("Erro", "Nenhuma definição de padrão encontrada para o modo Followpos.")
                update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", "Nenhuma definição de RE.")
                return
            
            combined_re_parts = []
            
            name_for_followpos_dfa = app_instance.pattern_order[0]
            regex_for_followpos_dfa = app_instance.definitions[name_for_followpos_dfa]
            construction_details_builder.append(f"Construindo AFD Direto (Followpos) para: {name_for_followpos_dfa}: {regex_for_followpos_dfa}\n(Para um lexer completo, as ERs seriam unidas antes.)\n")

            direct_dfa, aug_tree, pos_map = regex_to_direct_dfa(regex_for_followpos_dfa, name_for_followpos_dfa)
            
            if direct_dfa and aug_tree and pos_map:
                app_instance.unminimized_dfa = direct_dfa # Este é o nosso AFD direto
                app_instance.augmented_syntax_tree_followpos = aug_tree
                app_instance.followpos_table_followpos = pos_map
                
                construction_details_builder.append(f"  Árvore Aumentada para '{name_for_followpos_dfa}':\n{aug_tree}\n")
                fp_details = ["  Tabela Followpos:"]
                for pid_sorted in sorted(pos_map.keys()):
                    pnode = pos_map[pid_sorted]
                    fp_obj_ids_sorted = sorted([fp_obj.id for fp_obj in pnode.followpos])
                    fp_details.append(f"    {pnode}: {{ {', '.join(map(str,fp_obj_ids_sorted))} }}")
                construction_details_builder.append("\n".join(fp_details) + "\n")
                
                update_display_tab(widgets, "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", 
                                   get_dfa_table_str(direct_dfa, f"AFD Direto (Não-Minimizado) para '{name_for_followpos_dfa}'"))
                process_successful = True
            else:
                construction_details_builder.append(f"  Falha ao gerar AFD direto para '{name_for_followpos_dfa}'.\n")
            
            if process_successful and widgets.get("generate_dfa_button"): # Habilita para minimizar
                widgets["generate_dfa_button"].configure(state="normal")
        

        update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", "".join(construction_details_builder))
        if widgets.get("display_tab_view"): widgets["display_tab_view"].set("ER ➔ NFA Ind. / Árvore+Followpos")
        
        if not process_successful:
             messagebox.showwarning("Processamento Parcial", f"({app_instance.current_test_name}): Algumas ou todas as REs falharam.")
        else:
            messagebox.showinfo("Sucesso (Etapa A)", f"({app_instance.current_test_name}): Processamento de REs concluído.")

    except Exception as e:
        messagebox.showerror("Erro na Etapa A", f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}")
        update_display_tab(widgets, "ER ➔ NFA Ind. / Árvore+Followpos", f"Erro: {str(e)}")

def combine_all_nfas_callback(app_instance): # Etapa B do Thompson
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
        if widgets.get("display_tab_view"): widgets["display_tab_view"].set("NFA Combinado (União ε) / AFD Direto (Não-Minim.)")
        if widgets.get("generate_dfa_button"): widgets["generate_dfa_button"].configure(state="normal") # Habilita Minimização
        messagebox.showinfo("Sucesso (Etapa B - Thompson)", "NFAs combinados e AFD não minimizado gerado.")
    except Exception as e:
        messagebox.showerror("Erro Etapa B - Thompson", f"{type(e).__name__}: {str(e)}")
        update_display_tab(widgets, "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", f"Erro: {str(e)}")

def generate_final_dfa_and_minimize_callback(app_instance): # Etapa C
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return

    app_instance.dfa = None 
    dfa_tables_display_builder = []

    try:
        if not app_instance.unminimized_dfa:
            messagebox.showerror("Processo Incompleto", "O AFD não minimizado (da Etapa B ou A-Followpos) não foi gerado.")
            return

        dfa_tables_display_builder.append(get_dfa_table_str(app_instance.unminimized_dfa, title_prefix="AFD Não Minimizado (Entrada para Minimização): "))
        
        app_instance.dfa = _minimize_dfa(app_instance.unminimized_dfa)
        dfa_tables_display_builder.append(get_dfa_table_str(app_instance.dfa, title_prefix="AFD Minimizado (Final): "))
        
        update_display_tab(widgets, "AFD Minimizado (Final)", "\n\n====================\n\n".join(dfa_tables_display_builder))
        if widgets.get("display_tab_view"): widgets["display_tab_view"].set("AFD Minimizado (Final)")
        
        app_instance.lexer = Lexer(app_instance.dfa, app_instance.reserved_words_defs, app_instance.patterns_to_ignore, app_instance.symbol_table_instance)

        if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="normal")
        if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="normal")
        if widgets.get("draw_dfa_button"): widgets["draw_dfa_button"].configure(state="normal")
        messagebox.showinfo("Sucesso (Etapa C - Minimização)", "AFD Minimizado gerado. Lexer pronto.")

    except Exception as e:
        messagebox.showerror("Erro Etapa C - Minimização", f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}")
        update_display_tab(widgets, "AFD Minimizado (Final)", f"Erro: {str(e)}")
        for btn_key in ["tokenize_button", "save_dfa_button", "draw_dfa_button"]:
            if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")

def draw_current_minimized_dfa_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return

    dfa_img_label_current = widgets.get("dfa_image_label")

    if not app_instance.dfa:
        messagebox.showerror("Sem AFD", "Nenhum AFD minimizado para desenhar. Gere o AFD primeiro.")
        if dfa_img_label_current: dfa_img_label_current.configure(image=None, text="Nenhum AFD minimizado disponível.")
        return
    
    test_name_slug = "".join(c if c.isalnum() else "_" for c in app_instance.current_test_name)
    filename_prefix = f"dfa_graph_{test_name_slug}"
    
    try:
        image_path = draw_dfa_to_file(app_instance.dfa, filename_prefix=filename_prefix, output_subdir=app_instance.images_output_dir, view=False)
        
        if image_path and os.path.exists(image_path):
            pil_image = Image.open(image_path)
            
            original_width, original_height = pil_image.size
            tab_widget_for_drawing = None
            if widgets.get("display_tab_view"):
                 display_tab_view_widget = widgets["display_tab_view"]
                 try:
                    tab_widget_for_drawing = display_tab_view_widget.winfo_children()[display_tab_view_widget.index("Desenho AFD Minimizado")]
                 except Exception: 
                    tab_widget_for_drawing = display_tab_view_widget 

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
                new_width = int(new_height * img_aspect_ratio)

            if new_width > max_tab_width:
                new_width = max_tab_width
                new_height = int(new_width / img_aspect_ratio) if img_aspect_ratio != 0 else max_tab_height
            
            new_width = max(1, new_width)
            new_height = max(1, new_height)

            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            ctk_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width, resized_image.height))
            
            if dfa_img_label_current:
                dfa_img_label_current.configure(image=ctk_image, text="") 
                dfa_img_label_current.image = ctk_image 
            
            if widgets.get("display_tab_view"):
                try:
                    widgets["display_tab_view"].set("Desenho AFD Minimizado")
                except Exception: 
                    pass 
            messagebox.showinfo("Desenho AFD", f"Desenho do AFD exibido e salvo em:\n{image_path}")
        else:
            if dfa_img_label_current:
                dfa_img_label_current.configure(image=None, text="Falha ao gerar/encontrar imagem do AFD.")
            messagebox.showwarning("Desenho AFD", "Não foi possível gerar ou encontrar a imagem do AFD. Verifique o console.")
    except Exception as e:
        if dfa_img_label_current:
            dfa_img_label_current.configure(image=None, text=f"Erro ao desenhar AFD: {type(e).__name__}")
        messagebox.showerror("Erro ao Desenhar AFD", f"Ocorreu um erro: {e}")

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

def tokenize_source_callback(app_instance):
    widgets = app_instance.get_current_mode_widgets()
    if not widgets: return
    if not app_instance.lexer: 
        messagebox.showerror("Lexer Indisponível", "Analisador Léxico não gerado. Execute todas as etapas de construção primeiro."); return
    
    source_code = widgets["source_code_input_textbox"].get("1.0", "end-1c")
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
                    output_lines.append(f"<{lexema}, {token_type}>")
                elif token_type == "ID" and isinstance(attribute, int): 
                    output_lines.append(f"<{token_type}, {attribute}>  (Lexema: '{lexema}')")
                elif isinstance(attribute, (int, float)):
                     output_lines.append(f"<{lexema}, {token_type}> (Valor: {attribute})") # Para NUM
                else: 
                    output_lines.append(f"<{lexema}, {token_type}>")

        update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", "\n".join(output_lines))
        
        ts_static_part = widgets["textboxes_map"]["Tabela de Símbolos (Definições & Dinâmica)"].get("1.0", "end-1c").split("\n\nTabela de Símbolos (Dinâmica")[0]
        ts_dynamic_str = "\n\nTabela de Símbolos (Dinâmica - Após Análise Léxica):\n"
        ts_dynamic_str += str(populated_symbol_table)
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", ts_static_part + ts_dynamic_str)


        if widgets.get("display_tab_view"): widgets["display_tab_view"].set("Saída do Analisador Léxico (Tokens)")
    except Exception as e:
        messagebox.showerror("Erro Análise Léxica", f"({app_instance.current_test_name}): {type(e).__name__}: {str(e)}")
        update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", f"Erro: {str(e)}")
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", "Tabela de Símbolos (Dinâmica - Após Análise Léxica):\n(Erro durante a análise)")