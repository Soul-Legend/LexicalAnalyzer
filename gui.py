# gui.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from PIL import Image 

from automata import (NFA, DFA, NFAState, postfix_to_nfa, _finalize_nfa_properties,
                      combine_nfas, construct_unminimized_dfa_from_nfa, _minimize_dfa)
from lexer_core import Lexer, parse_re_file_data
from regex_utils import infix_to_postfix 

from syntax_tree_direct_dfa import regex_to_direct_dfa, AugmentedRegexSyntaxTreeNode, PositionNode
from graph_drawer import draw_dfa_to_file
from ui_formatters import get_nfa_details_str, get_dfa_table_str, get_dfa_anexo_ii_format

from tests import TEST_CASES

class LexerGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("T1 Formais: Gerador de Analisadores Léxicos")
        self.geometry("1300x850") 
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.font_title = ctk.CTkFont(family="Roboto", size=36, weight="bold")
        self.font_subtitle = ctk.CTkFont(family="Roboto", size=20, weight="normal")
        self.font_credits = ctk.CTkFont(family="Roboto", size=16, slant="italic")
        self.font_button = ctk.CTkFont(family="Roboto", size=16, weight="bold")
        self.font_small_button = ctk.CTkFont(family="Roboto", size=14)

        self.definitions = {}
        self.pattern_order = []
        self.reserved_words_defs = {}
        self.patterns_to_ignore = set()
        
        self.individual_nfas = {}
        self.combined_nfa_start_obj = None
        self.combined_nfa_accept_map = None
        self.combined_nfa_alphabet = None
        
        self.augmented_syntax_trees_followpos = {} 
        self.followpos_tables_followpos = {}
        self.direct_dfas_followpos = {} 

        self.unminimized_dfa = None 
        self.dfa = None 
        self.lexer = None
        self.current_test_name = "Manual"
        self.active_construction_method = "thompson" 
        
        self.images_output_dir = "imagens"
        # self.dfa_image_label não é mais um atributo de classe direto


        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.current_frame_name = None

        self._create_start_screen()
        self._create_manual_mode_frame()
        self._create_auto_test_mode_frame()

        self.show_frame("StartScreen")

    def show_frame(self, frame_name, construction_method=None):
        if self.current_frame_name and self.current_frame_name in self.frames:
            current_frame_obj = self.frames[self.current_frame_name]
            current_frame_obj.pack_forget()

        frame = self.frames[frame_name]
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.current_frame_name = frame_name
        
        if construction_method:
            self.active_construction_method = construction_method
        
        current_mode_display_name = "Automático"
        if self.current_frame_name == "ManualMode":
            current_mode_display_name = f"Manual ({self.active_construction_method.replace('_', ' ').capitalize()})"
        self.current_test_name = current_mode_display_name


        widgets = self.get_current_mode_widgets()
        if widgets:
            is_thompson = (self.active_construction_method == "thompson")
            if widgets.get("combine_nfas_button"):
                widgets["combine_nfas_button"].configure(state="disabled")
            
            process_btn_text = "A. Processar REs "
            if is_thompson: process_btn_text += "➔ NFAs (Thompson)"
            else: process_btn_text += "➔ DFAs (Followpos)"
            if widgets.get("process_re_button"):
                 widgets["process_re_button"].configure(text=process_btn_text)

        if frame_name == "AutoTestMode":
            self.active_construction_method = "thompson"
            widgets = self.get_current_mode_widgets()
            if widgets and widgets.get("process_re_button"):
                 widgets["process_re_button"].configure(text="A. Processar REs ➔ NFAs (Thompson)")

            if widgets and widgets.get("re_input_textbox") and \
               not widgets["re_input_textbox"].get("1.0", "end-1c").strip() and TEST_CASES:
                self.load_test_data_for_auto_mode(TEST_CASES[0], show_message=False)
        
        self.reset_app_state()

    def _create_start_screen(self):
        frame = ctk.CTkFrame(self.container, fg_color=("gray90", "gray10")) 
        self.frames["StartScreen"] = frame
        title_frame = ctk.CTkFrame(frame, fg_color="transparent")
        title_frame.pack(pady=(max(self.winfo_height() // 7, 60), 20), padx=20, fill="x")
        app_icon_label = ctk.CTkLabel(title_frame, text="🛠️", font=("Segoe UI Emoji", 48))
        app_icon_label.pack(side="left", padx=(0, 20))
        title_text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_text_frame.pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(title_text_frame, text="Analisador Léxico", font=self.font_title, anchor="w").pack(fill="x")
        ctk.CTkLabel(title_text_frame, text="Trabalho 1 - Linguagens Formais e Compiladores", font=self.font_subtitle, anchor="w", text_color=("gray30", "gray70")).pack(fill="x")

        buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
        buttons_frame.pack(pady=40, padx=80, fill="x")
        buttons_frame.grid_columnconfigure((0,1), weight=1)
        buttons_frame.grid_rowconfigure((0,1), weight=1)

        manual_thompson_button = ctk.CTkButton(buttons_frame, text="📝 Modo Manual (Thompson)",
                                      command=lambda: self.show_frame("ManualMode", construction_method="thompson"),
                                      height=70, font=self.font_button)
        manual_thompson_button.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        manual_tree_button = ctk.CTkButton(buttons_frame, text="🌳 Modo Manual (Followpos)",
                                      command=lambda: self.show_frame("ManualMode", construction_method="tree_direct_dfa"),
                                      height=70, font=self.font_button)
        manual_tree_button.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        auto_button = ctk.CTkButton(buttons_frame, text="⚙️ Modo Automático (Testes via Thompson)",
                                    command=lambda: self.show_frame("AutoTestMode"),
                                    height=70, font=self.font_button)
        auto_button.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
        
        bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", pady=(20, max(self.winfo_height() // 10, 40)), padx=20, fill="x")
        credits_label = ctk.CTkLabel(bottom_frame, text="Desenvolvido por: Pedro Taglialenha, Vitor Praxedes & Enrico Caliolo ", font=self.font_credits, text_color=("gray50", "gray50"))
        credits_label.pack(pady=(0, 20))
        exit_button = ctk.CTkButton(bottom_frame, text="Sair", command=self.quit, width=120, font=self.font_small_button, fg_color="transparent", border_width=1, border_color=("gray70", "gray30"), hover_color=("gray85", "gray20"))
        exit_button.pack()

    def _create_shared_controls_and_display(self, parent_frame):
        widgets = {}
        parent_frame.grid_columnconfigure(0, weight=1, minsize=420) 
        parent_frame.grid_columnconfigure(1, weight=3)             
        parent_frame.grid_rowconfigure(0, weight=1)

        outer_control_frame = ctk.CTkScrollableFrame(parent_frame, label_text="Controles e Definições")
        outer_control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        widgets["control_frame"] = outer_control_frame 

        ctk.CTkLabel(outer_control_frame, text="1. Definições Regulares:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w", fill="x")
        re_input_textbox = ctk.CTkTextbox(outer_control_frame, height=200, font=("Consolas", 11))
        re_input_textbox.pack(pady=2, padx=10, fill="x", expand=False)
        widgets["re_input_textbox"] = re_input_textbox
        
        load_re_file_button = ctk.CTkButton(outer_control_frame, text="Carregar Definições de Arquivo", command=self.load_re_from_file_for_current_mode)
        load_re_file_button.pack(pady=5, padx=10, fill="x")
        widgets["load_re_file_button"] = load_re_file_button

        process_re_button = ctk.CTkButton(outer_control_frame, text="A. Processar REs ...", command=self.process_regular_expressions)
        process_re_button.pack(pady=(10,3), padx=10, fill="x")
        widgets["process_re_button"] = process_re_button

        combine_nfas_button = ctk.CTkButton(outer_control_frame, text="B. Unir NFAs (Thompson)", command=self.combine_all_nfas, state="disabled")
        combine_nfas_button.pack(pady=3, padx=10, fill="x")
        widgets["combine_nfas_button"] = combine_nfas_button

        generate_dfa_button = ctk.CTkButton(outer_control_frame, text="C. Gerar AFD Final", command=self.generate_final_dfa_and_minimize, state="disabled")
        generate_dfa_button.pack(pady=3, padx=10, fill="x")
        widgets["generate_dfa_button"] = generate_dfa_button
        
        draw_dfa_button = ctk.CTkButton(outer_control_frame, text="🎨 Desenhar AFD Minimizado", command=self.draw_current_minimized_dfa, state="disabled")
        draw_dfa_button.pack(pady=3, padx=10, fill="x")
        widgets["draw_dfa_button"] = draw_dfa_button

        save_dfa_button = ctk.CTkButton(outer_control_frame, text="Salvar Tabela AFD Minimizada (Anexo II)", command=self.save_dfa_to_file, state="disabled")
        save_dfa_button.pack(pady=(3,10), padx=10, fill="x")
        widgets["save_dfa_button"] = save_dfa_button


        ctk.CTkLabel(outer_control_frame, text="2. Texto Fonte para Análise:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w", fill="x")
        source_code_input_textbox = ctk.CTkTextbox(outer_control_frame, height=150, font=("Consolas", 11))
        source_code_input_textbox.pack(pady=2, padx=10, fill="x", expand=False)
        widgets["source_code_input_textbox"] = source_code_input_textbox

        tokenize_button = ctk.CTkButton(outer_control_frame, text="Analisar Texto Fonte (Gerar Tokens)", command=self.tokenize_source, state="disabled")
        tokenize_button.pack(pady=5, padx=10, fill="x")
        widgets["tokenize_button"] = tokenize_button
        
        back_button = ctk.CTkButton(outer_control_frame, text="Voltar à Tela Inicial", command=lambda: self.show_frame("StartScreen"))
        back_button.pack(pady=(20,10), padx=10, fill="x")
        widgets["back_button"] = back_button

        display_tab_view = ctk.CTkTabview(parent_frame) 
        display_tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        widgets["display_tab_view"] = display_tab_view
        
        tab_names = ["Construção Detalhada", "Autômato Intermediário / Direto", "AFD Final (Tabelas)", "Desenho AFD", "Tokens Gerados"]
        textboxes_map = {} 
        widgets["dfa_image_label"] = None # Inicializa a chave para o label da imagem
        for name in tab_names:
            tab = display_tab_view.add(name)
            if name == "Desenho AFD":
                image_label = ctk.CTkLabel(tab, text="Nenhum AFD desenhado ainda.", compound="top")
                image_label.pack(expand=True, fill="both", padx=5, pady=5)
                widgets["dfa_image_label"] = image_label # Armazena no dict de widgets
            else:
                textbox = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 10), state="disabled")
                textbox.pack(expand=True, fill="both", padx=5, pady=5)
                textboxes_map[name] = textbox
        
        widgets["textboxes_map"] = textboxes_map
        display_tab_view.set(tab_names[0])
        
        return widgets

    def _create_manual_mode_frame(self):
        frame = ctk.CTkFrame(self.container)
        self.frames["ManualMode"] = frame
        self.manual_mode_widgets = self._create_shared_controls_and_display(frame)
        self.manual_mode_widgets["re_input_textbox"].insert("0.0", "# Defina suas expressões regulares aqui.\n# Ex: ID: (a|b)*abb\n")
        self.manual_mode_widgets["source_code_input_textbox"].insert("0.0", "// Código fonte para teste.")

    def _create_auto_test_mode_frame(self):
        frame = ctk.CTkFrame(self.container)
        self.frames["AutoTestMode"] = frame
        self.auto_test_mode_widgets = self._create_shared_controls_and_display(frame) 
        
        scrollable_control_panel = self.auto_test_mode_widgets["control_frame"] 
        back_button_ref = self.auto_test_mode_widgets.get("back_button")
        if back_button_ref: back_button_ref.pack_forget()

        ctk.CTkLabel(scrollable_control_panel, text="3. Selecionar Teste Automático (via Thompson):", font=("Arial", 13, "bold")).pack(pady=(15,5), padx=10, anchor="w", fill="x")
        inner_scrollable_test_buttons = ctk.CTkScrollableFrame(scrollable_control_panel, height=120) 
        inner_scrollable_test_buttons.pack(pady=5, padx=10, fill="x")
        for i, test_case in enumerate(TEST_CASES):
            btn = ctk.CTkButton(inner_scrollable_test_buttons, text=f"Carregar: {test_case['name']}",
                                command=lambda tc=test_case: self.load_test_data_for_auto_mode(tc))
            btn.pack(pady=3, fill="x")
        if back_button_ref: back_button_ref.pack(pady=(20,10), padx=10, fill="x")

    def get_current_mode_widgets(self):
        if self.current_frame_name == "ManualMode": return self.manual_mode_widgets
        elif self.current_frame_name == "AutoTestMode": return self.auto_test_mode_widgets
        return None

    def _update_text_content(self, textbox_widget, content):
        textbox_widget.configure(state="normal")
        textbox_widget.delete("1.0", "end")
        textbox_widget.insert("1.0", content)
        textbox_widget.configure(state="disabled")

    def _update_display(self, tab_key_name, content_str):
        widgets = self.get_current_mode_widgets()
        if not widgets or "textboxes_map" not in widgets: return 
        textbox = widgets["textboxes_map"].get(tab_key_name)
        if textbox: self._update_text_content(textbox, content_str)

    def _set_re_definitions_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        self._update_text_content(widgets["re_input_textbox"], content)
        self.reset_app_state()

    def _set_source_code_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        self._update_text_content(widgets["source_code_input_textbox"], content) 
        if self.dfa: self._update_display("Tokens Gerados", f"({self.current_test_name}: Texto fonte alterado, reanalisar)")
    
    def load_re_from_file_for_current_mode(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        filepath = filedialog.askopenfilename(title="Carregar Definições Regulares", filetypes=(("Text files", "*.txt"), ("RE files", "*.re"), ("All files", "*.*")))
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f_in: content = f_in.read()
                self._set_re_definitions_for_current_mode(content)
                method_name = self.active_construction_method.replace('_', ' ').capitalize()
                self.current_test_name = f"Arquivo ({method_name}): {filepath.split('/')[-1]}"
                messagebox.showinfo("Sucesso", f"Arquivo '{filepath.split('/')[-1]}' carregado.")
            except Exception as e: messagebox.showerror("Erro ao Ler Arquivo", str(e))

    def load_test_data_for_auto_mode(self, test_case, show_message=True):
        if self.current_frame_name != "AutoTestMode": self.show_frame("AutoTestMode")
        self.active_construction_method = "thompson"
        self._set_re_definitions_for_current_mode(test_case["re_definitions"])
        self._set_source_code_for_current_mode(test_case["source_code"])
        self.current_test_name = test_case["name"]
        if show_message and hasattr(self, 'auto_test_mode_widgets') and self.auto_test_mode_widgets["control_frame"].winfo_ismapped():
             messagebox.showinfo("Teste Carregado", f"Teste '{test_case['name']}' carregado (via Thompson).")

    def reset_app_state(self):
        self.definitions.clear(); self.pattern_order.clear(); self.reserved_words_defs.clear(); self.patterns_to_ignore.clear()
        self.individual_nfas.clear(); self.combined_nfa_start_obj = None; self.combined_nfa_accept_map = None; self.combined_nfa_alphabet = None
        self.augmented_syntax_trees_followpos.clear(); self.followpos_tables_followpos.clear(); self.direct_dfas_followpos.clear()
        self.unminimized_dfa = None; self.dfa = None; self.lexer = None
        
        widgets = self.get_current_mode_widgets()
        if not widgets: return

        for tab_name_key in widgets["textboxes_map"]: self._update_display(tab_name_key, "")
        
        dfa_img_label_current = widgets.get("dfa_image_label")
        if dfa_img_label_current:
            dfa_img_label_current.configure(image=None, text="Nenhum AFD desenhado ainda.")
        
        widgets["process_re_button"].configure(state="normal")
        
        for btn_key in ["combine_nfas_button", "generate_dfa_button", "draw_dfa_button", "save_dfa_button", "tokenize_button"]:
            if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")

    def process_regular_expressions(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        re_content = widgets["re_input_textbox"].get("1.0", "end-1c").strip()
        if not re_content: messagebox.showerror("Entrada Vazia", "Nenhuma definição regular fornecida."); return
        
        self.reset_app_state() 
        
        is_thompson_method = (self.active_construction_method == "thompson")
        btn_text = "A. Processar REs "
        if is_thompson_method: btn_text += "➔ NFAs (Thompson)"
        else: btn_text += "➔ DFAs (Followpos)"
        widgets["process_re_button"].configure(text=btn_text, state="normal")


        try:
            NFA.reset_state_ids()
            PositionNode.reset_id_counter()
            DFA._next_dfa_id = 0 
            DFA._state_map = {}  

            self.definitions, self.pattern_order, self.reserved_words_defs, self.patterns_to_ignore = parse_re_file_data(re_content)
            
            construction_details_builder = [f"Processando Definições ({self.current_test_name}):\n"]
            if self.patterns_to_ignore: construction_details_builder.append(f"(Padrões ignorados: {', '.join(sorted(list(self.patterns_to_ignore)))})\n")
            construction_details_builder.append("\n")
            
            process_successful = False

            if self.active_construction_method == "thompson":
                has_any_valid_nfa = False
                for name in self.pattern_order:
                    regex_str = self.definitions.get(name, "")
                    if not regex_str: continue
                    construction_details_builder.append(f"Definição: {name}: {regex_str}\n")
                    try:
                        postfix_expr = infix_to_postfix(regex_str)
                        construction_details_builder.append(f"  Pós-fixada: {postfix_expr if postfix_expr else '(VAZIA)'}\n")
                        nfa = postfix_to_nfa(postfix_expr)
                        if nfa: 
                            self.individual_nfas[name] = nfa
                            construction_details_builder.append(get_nfa_details_str(nfa, f"NFA para '{name}'") + "\n\n")
                            has_any_valid_nfa = True
                        else: construction_details_builder.append("  NFA: (Não gerado)\n\n")
                    except Exception as ve_re: construction_details_builder.append(f"  ERRO NFA '{name}': {ve_re}\n\n")
                process_successful = has_any_valid_nfa
                if process_successful and widgets.get("combine_nfas_button"): widgets["combine_nfas_button"].configure(state="normal")

            elif self.active_construction_method == "tree_direct_dfa":
                has_any_valid_direct_dfa = False
                temp_direct_dfa_display = []

                for name in self.pattern_order:
                    regex_str = self.definitions.get(name, "")
                    if not regex_str: continue
                    construction_details_builder.append(f"Definição: {name}: {regex_str}\n")
                    try:
                        direct_dfa, aug_tree, pos_map = regex_to_direct_dfa(regex_str, name)
                        if direct_dfa and aug_tree and pos_map:
                            if not direct_dfa.states and not (direct_dfa.start_state_id is not None and direct_dfa.start_state_id in direct_dfa.accept_states) :
                                construction_details_builder.append(f"  DFA Direto para '{name}': (Linguagem vazia ou erro na geração)\n\n")
                            else:
                                self.direct_dfas_followpos[name] = direct_dfa
                                self.augmented_syntax_trees_followpos[name] = aug_tree
                                self.followpos_tables_followpos[name] = pos_map
                                
                                construction_details_builder.append(f"  Árvore Aumentada para '{name}':\n{aug_tree}\n")
                                fp_details = ["  Tabela Followpos:"]
                                sorted_pos_ids = sorted(pos_map.keys())
                                for pid_sorted in sorted_pos_ids:
                                    pnode = pos_map[pid_sorted]
                                    fp_obj_ids_sorted = sorted([fp_obj.id for fp_obj in pnode.followpos])
                                    fp_details.append(f"    {pnode}: {{ {', '.join(map(str,fp_obj_ids_sorted))} }}")
                                construction_details_builder.append("\n".join(fp_details) + "\n")
                                temp_direct_dfa_display.append(get_dfa_table_str(direct_dfa, f"DFA Direto (não minimizado) para '{name}'"))
                                has_any_valid_direct_dfa = True
                        else: construction_details_builder.append(f"  DFA Direto para '{name}': (Não gerado ou regex original resultou em linguagem vazia/epsilon que foi tratada especialmente)\n\n")
                    except Exception as ve_re: construction_details_builder.append(f"  ERRO DFA Direto '{name}': {type(ve_re).__name__} - {ve_re}\n\n");
                
                process_successful = has_any_valid_direct_dfa
                if process_successful and widgets.get("generate_dfa_button"):
                    widgets["generate_dfa_button"].configure(state="normal")
                
                self._update_display("Autômato Intermediário / Direto", "\n\n".join(temp_direct_dfa_display))
                if widgets.get("display_tab_view"): widgets["display_tab_view"].set("Autômato Intermediário / Direto")


            self._update_display("Construção Detalhada", "".join(construction_details_builder))
            if widgets.get("display_tab_view") and self.active_construction_method == "thompson":
                 widgets["display_tab_view"].set("Construção Detalhada")
            
            if not process_successful:
                 messagebox.showwarning("Processamento Parcial", f"({self.current_test_name}): Algumas ou todas as REs falharam.")
            else:
                messagebox.showinfo("Sucesso (Etapa A)", f"({self.current_test_name}): Processamento de REs concluído.")

        except Exception as e:
            messagebox.showerror("Erro na Etapa A", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("Construção Detalhada", f"Erro: {str(e)}")
    
    def combine_all_nfas(self):
        widgets = self.get_current_mode_widgets()
        if not widgets or self.active_construction_method != "thompson": return
        if not self.individual_nfas: messagebox.showerror("Sem NFAs", "Nenhum NFA individual (Thompson) para combinar."); return
        
        nfas_for_combination = {k: v for k,v in self.individual_nfas.items() if v is not None}
        if not nfas_for_combination: messagebox.showerror("Sem NFAs Válidos", "Nenhum NFA individual válido para combinar."); return

        try:
            self.combined_nfa_start_obj, self.combined_nfa_accept_map, self.combined_nfa_alphabet = combine_nfas(nfas_for_combination)
            if not self.combined_nfa_start_obj:
                messagebox.showerror("Erro Combinação", "Falha ao criar NFA combinado."); return
            
            combined_nfa_shell = NFA(self.combined_nfa_start_obj, None)
            output_str = get_nfa_details_str(combined_nfa_shell, "NFA Combinado Global (Thompson)", combined_accept_map=self.combined_nfa_accept_map)
            self._update_display("Autômato Intermediário / Direto", output_str)
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("Autômato Intermediário / Direto")
            if widgets.get("generate_dfa_button"): widgets["generate_dfa_button"].configure(state="normal")
            messagebox.showinfo("Sucesso (Etapa B - Thompson)", "NFAs combinados.")
        except Exception as e:
            messagebox.showerror("Erro Etapa B - Thompson", f"{type(e).__name__}: {str(e)}")
            self._update_display("Autômato Intermediário / Direto", f"Erro: {str(e)}")

    def generate_final_dfa_and_minimize(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return

        dfa_output_str_parts = []
        self.unminimized_dfa = None 
        self.dfa = None            

        try:
            DFA._next_dfa_id = 0 
            DFA._state_map = {}  

            if self.active_construction_method == "thompson":
                if not self.combined_nfa_start_obj:
                    messagebox.showerror("NFA Ausente", "NFA combinado (Thompson) não pronto."); return
                
                self.unminimized_dfa = construct_unminimized_dfa_from_nfa(
                    self.combined_nfa_start_obj, self.combined_nfa_accept_map,
                    self.combined_nfa_alphabet, self.pattern_order
                )
                dfa_output_str_parts.append(get_dfa_table_str(self.unminimized_dfa, title_prefix="AFD (de NFA Combinado) Não Minimizado: "))
            
            elif self.active_construction_method == "tree_direct_dfa":
                if not self.direct_dfas_followpos:
                    messagebox.showerror("DFAs Diretos Ausentes", "Nenhum DFA direto (Followpos) gerado na Etapa A."); return
                
                if len(self.direct_dfas_followpos) == 1:
                    first_pattern_name = self.pattern_order[0] 
                    self.unminimized_dfa = self.direct_dfas_followpos.get(first_pattern_name)
                    if self.unminimized_dfa:
                        dfa_output_str_parts.append(get_dfa_table_str(self.unminimized_dfa, title_prefix=f"AFD Direto (Followpos) para '{first_pattern_name}' Não Minimizado: "))
                    else:
                        messagebox.showerror("Erro", "DFA direto não encontrado para o primeiro padrão.")
                        return
                else: 
                    messagebox.showinfo("Info Followpos Múltiplo", 
                                        "Múltiplas REs processadas com Followpos individualmente.\n"
                                        "Para um lexer completo com Followpos, combine as REs em uma única expressão "
                                        "(ex: (R1)|(R2)|...) antes de aplicar o algoritmo de Followpos.\n"
                                        "Para esta demonstração, o AFD direto do *primeiro* padrão será usado para minimização.")
                    if not self.pattern_order or not self.direct_dfas_followpos.get(self.pattern_order[0]):
                        messagebox.showerror("Erro", "Nenhum DFA direto disponível para demonstração de minimização.")
                        return
                    self.unminimized_dfa = self.direct_dfas_followpos[self.pattern_order[0]]
                    dfa_output_str_parts.append(get_dfa_table_str(self.unminimized_dfa, title_prefix=f"AFD Direto (Followpos) para '{self.pattern_order[0]}' (Não Minimizado): "))


            if not self.unminimized_dfa:
                messagebox.showerror("Erro", "Nenhum AFD não minimizado foi gerado ou selecionado para esta etapa.")
                return

            self.dfa = _minimize_dfa(self.unminimized_dfa)
            dfa_output_str_parts.append(get_dfa_table_str(self.dfa, title_prefix="AFD Minimizado: "))
            
            self._update_display("AFD Final (Tabelas)", "\n\n====================\n\n".join(dfa_output_str_parts))
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("AFD Final (Tabelas)")
            
            self.lexer = Lexer(self.dfa, self.reserved_words_defs, self.patterns_to_ignore)
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="normal")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="normal")
            if widgets.get("draw_dfa_button"): widgets["draw_dfa_button"].configure(state="normal")
            messagebox.showinfo("Sucesso (Etapa C)", "AFD Final (Não Minimizado e Minimizado) gerado. Lexer pronto.")

        except Exception as e:
            messagebox.showerror("Erro Etapa C", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("AFD Final (Tabelas)", f"Erro: {str(e)}")
            for btn_key in ["tokenize_button", "save_dfa_button", "draw_dfa_button"]:
                if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")

    def draw_current_minimized_dfa(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return

        dfa_img_label_current = widgets.get("dfa_image_label")

        if not self.dfa:
            messagebox.showerror("Sem AFD", "Nenhum AFD minimizado para desenhar. Gere o AFD primeiro.")
            if dfa_img_label_current: dfa_img_label_current.configure(image=None, text="Nenhum AFD minimizado disponível.")
            return
        
        test_name_slug = "".join(c if c.isalnum() else "_" for c in self.current_test_name)
        filename_prefix = f"dfa_graph_{test_name_slug}"
        
        try:
            image_path = draw_dfa_to_file(self.dfa, filename_prefix=filename_prefix, output_subdir=self.images_output_dir, view=False)
            
            if image_path and os.path.exists(image_path):
                pil_image = Image.open(image_path)
                
                # Manter proporção, mas limitar tamanho para caber na GUI
                original_width, original_height = pil_image.size
                # Tentar obter o tamanho da aba (pode ser aproximado se a aba não estiver visível)
                tab_widget = widgets["display_tab_view"].winfo_children()[ widgets["display_tab_view"].index("Desenho AFD") ]
                
                # Usar um tamanho máximo se a aba não tiver dimensões ainda
                # Estes valores podem precisar de ajuste
                max_tab_width = tab_widget.winfo_width() if tab_widget.winfo_width() > 20 else 700 
                max_tab_height = tab_widget.winfo_height() if tab_widget.winfo_height() > 20 else 500

                img_aspect_ratio = original_width / original_height
                
                new_width = original_width
                new_height = original_height

                if new_width > max_tab_width:
                    new_width = max_tab_width
                    new_height = int(new_width / img_aspect_ratio)
                
                if new_height > max_tab_height:
                    new_height = max_tab_height
                    new_width = int(new_height * img_aspect_ratio)

                # Garantir que a nova largura também não exceda max_tab_width após ajuste de altura
                if new_width > max_tab_width:
                    new_width = max_tab_width
                    new_height = int(new_width / img_aspect_ratio)


                resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width, resized_image.height))
                
                if dfa_img_label_current:
                    dfa_img_label_current.configure(image=ctk_image, text="") 
                    dfa_img_label_current.image = ctk_image 
                
                if widgets.get("display_tab_view"):
                    try:
                        widgets["display_tab_view"].set("Desenho AFD")
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


    def save_dfa_to_file(self):
        if not self.dfa: messagebox.showerror("Sem AFD Minimizado", "Nenhum AFD minimizado para salvar."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".dfa.txt", filetypes=(("DFA Text files", "*.dfa.txt"),("Text files", "*.txt"), ("All files", "*.*")), title=f"Salvar Tabela AFD Minimizada ({self.current_test_name})")
        if filepath:
            try:
                anexo_ii_content = get_dfa_anexo_ii_format(self.dfa)
                with open(filepath, 'w', encoding='utf-8') as f_out: f_out.write(anexo_ii_content)
                
                base_name, ext = os.path.splitext(filepath)

                hr_filepath_min = f"{base_name}_min_readable.txt"
                hr_content_min = get_dfa_table_str(self.dfa, title_prefix="Minimized ");
                with open(hr_filepath_min, 'w', encoding='utf-8') as f_hr_min: f_hr_min.write(hr_content_min)

                if self.unminimized_dfa:
                    hr_filepath_unmin = f"{base_name}_unmin_readable.txt"
                    hr_content_unmin = get_dfa_table_str(self.unminimized_dfa, title_prefix="Unminimized ");
                    with open(hr_filepath_unmin, 'w', encoding='utf-8') as f_hr_unmin: f_hr_unmin.write(hr_content_unmin)

                messagebox.showinfo("Sucesso", "Tabela AFD Minimizada (Anexo II) e versões legíveis salvas.")
            except Exception as e: messagebox.showerror("Erro Salvar AFD", str(e))

    def tokenize_source(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        if not self.lexer: messagebox.showerror("Lexer Indisponível", "Analisador Léxico não gerado."); return
        source_code = widgets["source_code_input_textbox"].get("1.0", "end-1c")
        if not source_code: self._update_display("Tokens Gerados", "(Nenhum texto fonte)"); return
        try:
            tokens = self.lexer.tokenize(source_code)
            output_lines = [f"Tokens Gerados ({self.current_test_name} - com AFD Minimizado):\n"]
            if not tokens: output_lines.append("(Nenhum token reconhecido)")
            for lexeme, pattern in tokens: output_lines.append(f"<{lexeme}, {pattern if pattern != 'erro!' else 'ERRO!'}>")
            self._update_display("Tokens Gerados", "\n".join(output_lines))
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("Tokens Gerados")
        except Exception as e:
            messagebox.showerror("Erro Análise Léxica", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("Tokens Gerados", f"Erro: {str(e)}")

