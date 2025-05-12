# gui.py
"""
CustomTkinter GUI for the Lexer Generator application.
Manages different views: Start Screen, Manual Mode, Automatic Test Mode.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox

from automata import NFA, DFA, NFAState, postfix_to_nfa, combine_nfas, nfa_to_dfa
from lexer_core import Lexer, parse_re_file_data
from regex_utils import infix_to_postfix
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
        self.dfa = None
        self.lexer = None
        self.current_test_name = "Manual"

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

    def show_frame(self, frame_name):
        if self.current_frame_name and self.current_frame_name in self.frames:
            current_frame_obj = self.frames[self.current_frame_name]
            current_frame_obj.pack_forget()

        frame = self.frames[frame_name]
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.current_frame_name = frame_name
        
        if frame_name == "AutoTestMode":
            widgets = self.get_current_mode_widgets()
            if widgets and widgets.get("re_input_textbox") and \
               not widgets["re_input_textbox"].get("1.0", "end-1c").strip() and TEST_CASES:
                self.load_test_data_for_auto_mode(TEST_CASES[0], show_message=False)

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

        manual_button = ctk.CTkButton(buttons_frame, text="📝 Modo Manual",
                                      command=lambda: self.show_frame("ManualMode"),
                                      height=70, font=self.font_button,
                                      hover_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"]) 
        manual_button.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

        auto_button = ctk.CTkButton(buttons_frame, text="⚙️ Modo Automático (Testes)",
                                    command=lambda: self.show_frame("AutoTestMode"),
                                    height=70, font=self.font_button,
                                    hover_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        auto_button.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

        bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_frame.pack(side="bottom", pady=(20, max(self.winfo_height() // 10, 40)), padx=20, fill="x")

        credits_label = ctk.CTkLabel(bottom_frame,
                                     text="Desenvolvido por: Pedro Taglialenha, Vitor Praxedes & Enrico Caliolo",
                                     font=self.font_credits, text_color=("gray50", "gray50"))
        credits_label.pack(pady=(0, 20))

        exit_button = ctk.CTkButton(bottom_frame, text="Sair", command=self.quit,
                                    width=120, font=self.font_small_button, fg_color="transparent",
                                    border_width=1, border_color=("gray70", "gray30"),
                                    hover_color=("gray85", "gray20"))
        exit_button.pack()

    def _create_shared_controls_and_display(self, parent_frame):
        widgets = {}
        parent_frame.grid_columnconfigure(0, weight=1, minsize=420) 
        parent_frame.grid_columnconfigure(1, weight=3)             
        parent_frame.grid_rowconfigure(0, weight=1)

        # ***** MODIFICATION START *****
        # Create a CTkScrollableFrame for the entire control panel content
        outer_control_frame = ctk.CTkScrollableFrame(parent_frame, label_text="Controles e Definições")
        outer_control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        # The 'widgets["control_frame"]' will now refer to this scrollable frame
        # or an inner static frame if you prefer more structure.
        # For simplicity, we'll pack directly into outer_control_frame.
        widgets["control_frame"] = outer_control_frame 
        # All subsequent .pack() calls for controls will be on this scrollable frame.
        # ***** MODIFICATION END *****


        ctk.CTkLabel(outer_control_frame, text="1. Definições Regulares:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w", fill="x")
        re_input_textbox = ctk.CTkTextbox(outer_control_frame, height=200, font=("Consolas", 11))
        re_input_textbox.pack(pady=2, padx=10, fill="x", expand=False) # expand=False is important for textboxes in scrollable frames
        widgets["re_input_textbox"] = re_input_textbox
        
        load_re_file_button = ctk.CTkButton(outer_control_frame, text="Carregar Definições de Arquivo", command=self.load_re_from_file_for_current_mode)
        load_re_file_button.pack(pady=5, padx=10, fill="x")
        widgets["load_re_file_button"] = load_re_file_button

        process_re_button = ctk.CTkButton(outer_control_frame, text="A. Processar REs ➔ NFAs", command=self.process_regular_expressions)
        process_re_button.pack(pady=(10,3), padx=10, fill="x")
        widgets["process_re_button"] = process_re_button

        combine_nfas_button = ctk.CTkButton(outer_control_frame, text="B. Unir NFAs (ε)", command=self.combine_all_nfas, state="disabled")
        combine_nfas_button.pack(pady=3, padx=10, fill="x")
        widgets["combine_nfas_button"] = combine_nfas_button

        generate_dfa_button = ctk.CTkButton(outer_control_frame, text="C. Determinizar NFA ➔ AFD", command=self.generate_dfa_from_nfa, state="disabled")
        generate_dfa_button.pack(pady=3, padx=10, fill="x")
        widgets["generate_dfa_button"] = generate_dfa_button
        
        save_dfa_button = ctk.CTkButton(outer_control_frame, text="Salvar Tabela AFD (Anexo II)", command=self.save_dfa_to_file, state="disabled")
        save_dfa_button.pack(pady=(3,10), padx=10, fill="x")
        widgets["save_dfa_button"] = save_dfa_button

        ctk.CTkLabel(outer_control_frame, text="2. Texto Fonte para Análise:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w", fill="x")
        source_code_input_textbox = ctk.CTkTextbox(outer_control_frame, height=150, font=("Consolas", 11))
        source_code_input_textbox.pack(pady=2, padx=10, fill="x", expand=False)
        widgets["source_code_input_textbox"] = source_code_input_textbox

        tokenize_button = ctk.CTkButton(outer_control_frame, text="Analisar Texto Fonte (Gerar Tokens)", command=self.tokenize_source, state="disabled")
        tokenize_button.pack(pady=5, padx=10, fill="x")
        widgets["tokenize_button"] = tokenize_button
        
        # The "Selecionar Teste Automático" section will be added specifically in _create_auto_test_mode_frame
        # It will also be packed into this outer_control_frame (scrollable)

        # Back to Start Screen Button needs to be accessible even when scrolled
        # So, it's better to pack it into parent_frame's control_frame directly if it's static,
        # or at the very bottom of the scrollable area.
        # For now, let's keep it inside the scrollable area.
        back_button = ctk.CTkButton(outer_control_frame, text="Voltar à Tela Inicial", command=lambda: self.show_frame("StartScreen"))
        back_button.pack(pady=(20,10), padx=10, fill="x") # Will be at the bottom of scrollable content
        widgets["back_button"] = back_button # Though it's inside, reference is still useful


        # --- Display Frame (Right) with Tabs --- (This part is outside the scrollable control frame)
        display_tab_view = ctk.CTkTabview(parent_frame) 
        display_tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        widgets["display_tab_view"] = display_tab_view

        tab_names = ["REs & NFAs Ind.", "NFA Combinado", "AFD (Tabela)", "Tokens Gerados"]
        textboxes_map = {} 
        for name in tab_names:
            tab = display_tab_view.add(name)
            textbox = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 10), state="disabled")
            textbox.pack(expand=True, fill="both", padx=5, pady=5)
            textboxes_map[name] = textbox
        display_tab_view.set(tab_names[0])
        widgets["textboxes_map"] = textboxes_map
        
        return widgets

    def _create_manual_mode_frame(self):
        frame = ctk.CTkFrame(self.container)
        self.frames["ManualMode"] = frame
        self.manual_mode_widgets = self._create_shared_controls_and_display(frame)
        # No specific additions for manual mode's control panel here, already handled by shared.
        self.manual_mode_widgets["re_input_textbox"].insert("0.0", "# Defina suas expressões regulares aqui, uma por linha.\n# Ex: ID: [a-z]+\n# Ex: NUM: [0-9]+\n# Ex: WS: [ ]+ %ignore\n")
        self.manual_mode_widgets["source_code_input_textbox"].insert("0.0", "// Digite o código fonte para testar aqui.")


    def _create_auto_test_mode_frame(self):
        frame = ctk.CTkFrame(self.container)
        self.frames["AutoTestMode"] = frame
        # _create_shared_controls_and_display returns a dict including the scrollable 'control_frame'
        self.auto_test_mode_widgets = self._create_shared_controls_and_display(frame) 
        
        # Get the scrollable control frame to add auto-test specific widgets
        scrollable_control_panel = self.auto_test_mode_widgets["control_frame"] 
        
        # The "Voltar à Tela Inicial" button is already packed at the end by _create_shared_controls_and_display
        # We need to insert the test selection widgets *before* it.
        # To do this, we can temporarily forget the back button, pack new things, then re-pack back button.
        back_button_ref = self.auto_test_mode_widgets.get("back_button")
        if back_button_ref:
            back_button_ref.pack_forget()

        ctk.CTkLabel(scrollable_control_panel, text="3. Selecionar Teste Automático:", font=("Arial", 13, "bold")).pack(pady=(15,5), padx=10, anchor="w", fill="x")

        # This scrollable frame for test buttons will be *inside* the main scrollable control panel
        # which might be a bit much, but let's try. Max height for this inner scroll.
        inner_scrollable_test_buttons = ctk.CTkScrollableFrame(scrollable_control_panel, height=120) 
        inner_scrollable_test_buttons.pack(pady=5, padx=10, fill="x")

        for i, test_case in enumerate(TEST_CASES):
            btn = ctk.CTkButton(inner_scrollable_test_buttons, text=f"Carregar: {test_case['name']}",
                                command=lambda tc=test_case: self.load_test_data_for_auto_mode(tc))
            btn.pack(pady=3, fill="x")
        
        if back_button_ref: # Re-pack the back button at the very end of the scrollable content
            back_button_ref.pack(pady=(20,10), padx=10, fill="x")


    # ... (rest of the methods: get_current_mode_widgets, _update_text_content, _update_display, etc.
    #      should remain the same as your provided version)
    def get_current_mode_widgets(self):
        if self.current_frame_name == "ManualMode":
            return self.manual_mode_widgets
        elif self.current_frame_name == "AutoTestMode":
            return self.auto_test_mode_widgets
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
        if textbox:
            self._update_text_content(textbox, content_str) 

    def _set_re_definitions_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        self._update_text_content(widgets["re_input_textbox"], content)
        self.reset_app_state()

    def _set_source_code_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        self._update_text_content(widgets["source_code_input_textbox"], content) 
        if self.dfa:
             self._update_display("Tokens Gerados", f"({self.current_test_name}: Texto fonte alterado, reanalisar)")
    
    def load_re_from_file_for_current_mode(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        filepath = filedialog.askopenfilename(title="Carregar Definições Regulares", filetypes=(("Text files", "*.txt"), ("RE files", "*.re"), ("All files", "*.*")))
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f_in: content = f_in.read()
                self._set_re_definitions_for_current_mode(content)
                self.current_test_name = f"Arquivo: {filepath.split('/')[-1]}"
                messagebox.showinfo("Sucesso", f"Arquivo '{filepath.split('/')[-1]}' carregado para {self.current_frame_name}.")
            except Exception as e: messagebox.showerror("Erro ao Ler Arquivo", str(e))

    def load_test_data_for_auto_mode(self, test_case, show_message=True):
        if self.current_frame_name != "AutoTestMode":
             self.show_frame("AutoTestMode")
        
        self._set_re_definitions_for_current_mode(test_case["re_definitions"])
        self._set_source_code_for_current_mode(test_case["source_code"])
        self.current_test_name = test_case["name"]
        
        if show_message and hasattr(self, 'auto_test_mode_widgets') and self.auto_test_mode_widgets["control_frame"].winfo_ismapped():
             messagebox.showinfo("Teste Carregado", f"Teste '{test_case['name']}' carregado no Modo Automático.")

    def reset_app_state(self):
        self.definitions.clear()
        self.pattern_order.clear()
        self.reserved_words_defs.clear()
        self.patterns_to_ignore.clear()
        self.individual_nfas.clear()
        self.combined_nfa_start_obj = None; self.combined_nfa_accept_map = None; self.combined_nfa_alphabet = None
        self.dfa = None; self.lexer = None
        widgets = self.get_current_mode_widgets()
        if not widgets or "textboxes_map" not in widgets : return
        for tab_name in widgets["textboxes_map"]: self._update_display(tab_name, "")
        widgets["process_re_button"].configure(state="normal")
        widgets["combine_nfas_button"].configure(state="disabled")
        widgets["generate_dfa_button"].configure(state="disabled")
        widgets["save_dfa_button"].configure(state="disabled")
        widgets["tokenize_button"].configure(state="disabled")

    def process_regular_expressions(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        re_content = widgets["re_input_textbox"].get("1.0", "end-1c").strip()
        if not re_content: messagebox.showerror("Entrada Vazia", "Nenhuma definição regular fornecida."); return
        try:
            self.individual_nfas.clear(); self.combined_nfa_start_obj = None; self.dfa = None; self.lexer = None
            self._update_display("REs & NFAs Ind.", ""); self._update_display("NFA Combinado", ""); self._update_display("AFD (Tabela)", ""); self._update_display("Tokens Gerados", "")
            NFA.reset_state_ids()
            self.definitions, self.pattern_order, self.reserved_words_defs, self.patterns_to_ignore = parse_re_file_data(re_content)
            output_str_builder = [f"Processando Definições ({self.current_test_name}):\n"]
            if self.patterns_to_ignore: output_str_builder.append(f"(Padrões ignorados: {', '.join(sorted(list(self.patterns_to_ignore)))})\n")
            output_str_builder.append("\n"); has_any_valid_nfa = False
            for name in self.pattern_order:
                regex_str = self.definitions.get(name, "");
                if not regex_str: continue
                output_str_builder.append(f"Definição: {name}: {regex_str}\n")
                try:
                    postfix_expr = infix_to_postfix(regex_str)
                    if not postfix_expr: output_str_builder.append(f"  Expressão Pós-fixada: (VAZIA para '{regex_str}')\n"); nfa = None
                    else: output_str_builder.append(f"  Expressão Pós-fixada: {postfix_expr}\n"); nfa = postfix_to_nfa(postfix_expr)
                    if nfa: self.individual_nfas[name] = nfa; output_str_builder.append(get_nfa_details_str(nfa, f"NFA para '{name}'") + "\n\n"); has_any_valid_nfa = True
                    else: output_str_builder.append("  NFA: (Não gerado)\n\n")
                except Exception as ve_re: output_str_builder.append(f"  ERRO em '{name}': {type(ve_re).__name__} - {ve_re}\n\n"); self.individual_nfas[name] = None
            self._update_display("REs & NFAs Ind.", "".join(output_str_builder))
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("REs & NFAs Ind.")
            if has_any_valid_nfa and any(nfa_obj for nfa_obj in self.individual_nfas.values()):
                if widgets.get("combine_nfas_button"): widgets["combine_nfas_button"].configure(state="normal")
            else:
                if widgets.get("combine_nfas_button"): widgets["combine_nfas_button"].configure(state="disabled")
            if widgets.get("generate_dfa_button"): widgets["generate_dfa_button"].configure(state="disabled")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="disabled")
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="disabled")
            messagebox.showinfo("Sucesso (Etapa A)", f"({self.current_test_name}): Processamento de REs e NFAs concluído.")
        except Exception as e:
            messagebox.showerror("Erro na Etapa A", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("REs & NFAs Ind.", f"Erro: {type(e).__name__}: {str(e)}")
            if widgets.get("combine_nfas_button"): widgets["combine_nfas_button"].configure(state="disabled")


    def combine_all_nfas(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        nfas_for_combination = {k: v for k,v in self.individual_nfas.items() if v is not None}
        if not nfas_for_combination: messagebox.showerror("Sem NFAs", f"({self.current_test_name}): Nenhum NFA individual válido para combinar."); return
        try:
            self.combined_nfa_start_obj, self.combined_nfa_accept_map, self.combined_nfa_alphabet = combine_nfas(nfas_for_combination)
            if not self.combined_nfa_start_obj: messagebox.showerror("Erro Combinação", f"({self.current_test_name}): Falha ao criar NFA combinado."); widgets["generate_dfa_button"].configure(state="disabled"); return
            combined_nfa_shell_for_display = NFA(self.combined_nfa_start_obj, None)
            output_str = get_nfa_details_str(combined_nfa_shell_for_display, "NFA Combinado Global", combined_accept_map=self.combined_nfa_accept_map)
            self._update_display("NFA Combinado", output_str)
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("NFA Combinado")
            if widgets.get("generate_dfa_button"): widgets["generate_dfa_button"].configure(state="normal")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="disabled")
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="disabled")
            messagebox.showinfo("Sucesso (Etapa B)", f"({self.current_test_name}): NFAs combinados.")
        except Exception as e:
            messagebox.showerror("Erro Etapa B", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("NFA Combinado", f"Erro: {type(e).__name__}: {str(e)}")
            if widgets.get("generate_dfa_button"): widgets["generate_dfa_button"].configure(state="disabled")


    def generate_dfa_from_nfa(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        if not self.combined_nfa_start_obj or self.combined_nfa_accept_map is None or self.combined_nfa_alphabet is None: messagebox.showerror("NFA Ausente", f"({self.current_test_name}): NFA combinado não pronto."); return
        try:
            self.dfa = nfa_to_dfa(self.combined_nfa_start_obj, self.combined_nfa_accept_map, self.combined_nfa_alphabet, self.pattern_order)
            output_str = get_dfa_table_str(self.dfa)
            self._update_display("AFD (Tabela)", output_str)
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("AFD (Tabela)")
            self.lexer = Lexer(self.dfa, self.reserved_words_defs, self.patterns_to_ignore)
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="normal")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="normal")
            messagebox.showinfo("Sucesso (Etapa C)", f"({self.current_test_name}): AFD gerado e Lexer pronto.")
        except Exception as e:
            messagebox.showerror("Erro Etapa C", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("AFD (Tabela)", f"Erro: {type(e).__name__}: {str(e)}")
            if widgets.get("tokenize_button"): widgets["tokenize_button"].configure(state="disabled")
            if widgets.get("save_dfa_button"): widgets["save_dfa_button"].configure(state="disabled")


    def save_dfa_to_file(self):
        if not self.dfa: messagebox.showerror("Sem AFD", f"({self.current_test_name}): Nenhum AFD para salvar."); return
        filepath = filedialog.asksaveasfilename(defaultextension=".dfa.txt", filetypes=(("DFA Text files", "*.dfa.txt"),("Text files", "*.txt"), ("All files", "*.*")), title=f"Salvar Tabela AFD ({self.current_test_name})")
        if filepath:
            try:
                anexo_ii_content = get_dfa_anexo_ii_format(self.dfa)
                with open(filepath, 'w', encoding='utf-8') as f_out: f_out.write(anexo_ii_content)
                hr_filepath = filepath.replace(".dfa.txt", "_readable.txt");
                if hr_filepath == filepath: hr_filepath += "_readable"
                hr_content = get_dfa_table_str(self.dfa);
                with open(hr_filepath, 'w', encoding='utf-8') as f_hr: f_hr.write(hr_content)
                messagebox.showinfo("Sucesso", f"({self.current_test_name}): Tabela AFD salva.")
            except Exception as e: messagebox.showerror("Erro Salvar AFD", str(e))

    def tokenize_source(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        if not self.lexer: messagebox.showerror("Lexer Indisponível", f"({self.current_test_name}): Analisador Léxico não gerado."); return
        source_code = widgets["source_code_input_textbox"].get("1.0", "end-1c")
        if not source_code: self._update_display("Tokens Gerados", f"({self.current_test_name}: Nenhum texto fonte)"); return
        try:
            tokens = self.lexer.tokenize(source_code)
            output_lines = [f"Tokens Gerados ({self.current_test_name}):\n"]
            if not tokens: output_lines.append("(Nenhum token reconhecido)")
            for lexeme, pattern in tokens: output_lines.append(f"<{lexeme}, {pattern if pattern != 'erro!' else 'ERRO!'}>")
            self._update_display("Tokens Gerados", "\n".join(output_lines))
            if widgets.get("display_tab_view"): widgets["display_tab_view"].set("Tokens Gerados")
        except Exception as e:
            messagebox.showerror("Erro Análise Léxica", f"({self.current_test_name}): {type(e).__name__}: {str(e)}")
            self._update_display("Tokens Gerados", f"Erro: {type(e).__name__}: {str(e)}")