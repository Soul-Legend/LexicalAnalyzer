import customtkinter as ctk
from tkinter import filedialog, messagebox 
import os 
from PIL import Image 
import traceback

from .frames import (create_start_screen_frame, create_manual_mode_frame_widgets, 
                     create_auto_test_mode_frame_widgets, create_full_test_mode_frame_widgets,
                     create_syntactic_mode_frame_widgets, create_syntactic_test_mode_frame_widgets,
                     create_integrated_mode_frame_widgets)
from .callbacks import (load_re_from_file_for_current_mode_callback, 
                        load_test_data_for_auto_mode_callback,
                        process_regular_expressions_callback, 
                        combine_all_nfas_callback,
                        generate_final_dfa_and_minimize_callback, 
                        draw_current_minimized_dfa_callback,
                        save_dfa_to_file_callback, 
                        tokenize_source_callback,
                        process_grammar_callback,
                        run_parser_callback,
                        run_part1_lexical_callback,
                        run_part2_syntactic_callback)
from .ui_utils import update_display_tab, clear_dfa_image, update_text_content
from tests import TEST_CASES 
from syntactic_tests import SYNTACTIC_TEST_CASES
from core.lexer_core import SymbolTable, parse_re_file_data
from core.syntactic.grammar import Grammar
from core.syntactic.slr_generator import SLRGenerator
from core.syntactic.slr_parser import SLRParser
from .ui_formatters import get_grammar_details_str, get_first_follow_sets_str, get_canonical_collection_str, get_slr_table_str, get_parse_steps_str


class LexerGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("T1/T2 Formais: Gerador de Analisadores Léxicos e Sintáticos")
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
        
        self.augmented_syntax_tree_followpos = None
        self.followpos_table_followpos = None

        self.unminimized_dfa = None 
        self.dfa = None 
        self.lexer = None
        self.current_test_name = "Manual"
        self.active_construction_method = "thompson" 
        
        self.images_output_dir = "imagens"
        self.symbol_table_instance = SymbolTable()

        self.grammar = None
        self.slr_action_table = None
        self.slr_goto_table = None
        self.generated_token_stream = []
        
        self.manual_mode_widgets = {}
        self.auto_test_mode_widgets = {}
        self.full_test_mode_widgets = {} 
        self.syntactic_mode_widgets = {}
        self.syntactic_test_mode_widgets = {}
        self.integrated_mode_widgets = {}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.current_frame_name = None

        create_start_screen_frame(self)
        create_manual_mode_frame_widgets(self)
        create_auto_test_mode_frame_widgets(self)
        create_full_test_mode_frame_widgets(self) 
        create_syntactic_mode_frame_widgets(self)
        create_syntactic_test_mode_frame_widgets(self)
        create_integrated_mode_frame_widgets(self)

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
        elif frame_name == "FullTestMode":
            if hasattr(self, 'full_test_mode_widgets') and self.full_test_mode_widgets.get("method_var"):
                self.active_construction_method = self.full_test_mode_widgets["method_var"].get()
            else: 
                self.active_construction_method = "thompson"
        elif frame_name == "AutoTestMode": 
            self.active_construction_method = "thompson"

        current_mode_display_name = "Automático" 
        if self.current_frame_name == "ManualMode":
            current_mode_display_name = f"Manual ({self.active_construction_method.replace('_', ' ').capitalize()})"
        elif self.current_frame_name == "FullTestMode":
            if hasattr(self, 'full_test_mode_widgets') and self.full_test_mode_widgets.get("method_var"):
                self.active_construction_method = self.full_test_mode_widgets["method_var"].get()
            current_mode_display_name = f"Teste Completo ({self.active_construction_method.replace('_', ' ').capitalize()})"
        elif self.current_frame_name == "StartScreen":
            current_mode_display_name = "Tela Inicial"
        elif self.current_frame_name == "SyntacticMode":
             self.current_test_name = "Analisador Sintático"
        elif self.current_frame_name == "SyntacticTestMode":
             self.current_test_name = "Teste Sintático Automático"
        elif self.current_frame_name == "IntegratedMode":
             self.current_test_name = "Modo Integrado"
        else:
             current_mode_display_name = "Testes Detalhados (Thompson)"

        self.current_test_name = current_mode_display_name

        widgets = self.get_current_mode_widgets() 
        if widgets and self.current_frame_name not in ["FullTestMode", "StartScreen", "SyntacticMode", "SyntacticTestMode", "IntegratedMode"]: 
            is_thompson = (self.active_construction_method == "thompson")
            
            combine_btn = widgets.get("combine_nfas_button")
            if combine_btn:
                if is_thompson:
                    combine_btn.configure(text="B. Unir NFAs & Determinar", command=self.combine_all_nfas, state="disabled")
                else: 
                    combine_btn.configure(text="B. (AFD Direto da Etapa A)", command=lambda: None, state="disabled")

            process_btn_text = "A. Processar ERs"
            if widgets.get("process_re_button"):
                 widgets["process_re_button"].configure(text=process_btn_text)
            
            generate_dfa_btn = widgets.get("generate_dfa_button")
            if generate_dfa_btn:
                generate_dfa_btn.configure(text="C. Minimizar AFD")

        if frame_name == "AutoTestMode": 
            if widgets and widgets.get("re_input_textbox") and \
               not widgets["re_input_textbox"].get("1.0", "end-1c").strip() and TEST_CASES:
                self.load_test_data_for_auto_mode(TEST_CASES[0], show_message=False)
        
        self.reset_app_state()

    def get_current_mode_widgets(self):
        if self.current_frame_name == "ManualMode": return self.manual_mode_widgets
        elif self.current_frame_name == "AutoTestMode": return self.auto_test_mode_widgets
        elif self.current_frame_name == "FullTestMode": return self.full_test_mode_widgets
        elif self.current_frame_name == "SyntacticMode": return self.syntactic_mode_widgets
        elif self.current_frame_name == "SyntacticTestMode": return self.syntactic_test_mode_widgets
        elif self.current_frame_name == "IntegratedMode": return self.integrated_mode_widgets
        return None

    def _update_widget_text(self, widget_key, content):
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        widget = widgets.get(widget_key)
        if widget:
            should_keep_editable = False 
            if self.current_frame_name == "ManualMode":
                if widget_key in ["re_input_textbox", "source_code_input_textbox"]:
                    should_keep_editable = True
            update_text_content(widget, content, keep_editable=should_keep_editable)
        else:
            pass

    def _set_re_definitions_for_current_mode(self, content):
        re_textbox_key = "re_input_textbox" 
        if self.current_frame_name == "FullTestMode":
            re_textbox_key = "re_display_textbox"
        self._update_widget_text(re_textbox_key, content)
        
        if self.current_frame_name != "FullTestMode": 
            self.reset_app_state()

    def _set_source_code_for_current_mode(self, content):
        source_textbox_key = "source_code_input_textbox" 
        if self.current_frame_name == "FullTestMode":
            source_textbox_key = "source_display_textbox"
        self._update_widget_text(source_textbox_key, content)

        if self.dfa and self.current_frame_name != "FullTestMode": 
            widgets = self.get_current_mode_widgets()
            update_display_tab(widgets, "Saída do Analisador Léxico (Tokens)", f"({self.current_test_name}: Texto fonte alterado, reanalisar)")

    def reset_app_state(self):
        self.definitions.clear(); self.pattern_order.clear(); self.reserved_words_defs.clear(); self.patterns_to_ignore.clear()
        self.individual_nfas.clear(); self.combined_nfa_start_obj = None; self.combined_nfa_accept_map = None; self.combined_nfa_alphabet = None
        self.augmented_syntax_tree_followpos = None; self.followpos_table_followpos = None;
        self.unminimized_dfa = None; self.dfa = None; self.lexer = None
        self.symbol_table_instance.clear()
        
        self.grammar = None
        self.slr_action_table = None
        self.slr_goto_table = None
        self.generated_token_stream = []

        widgets = self.get_current_mode_widgets()
        if not widgets: return

        for tab_name_key in widgets.get("textboxes_map", {}): 
            if tab_name_key == "Tabela de Símbolos (Definições & Dinâmica)":
                update_display_tab(widgets, tab_name_key, "Tabela de Símbolos (Definições Estáticas):\n(Aguardando processamento de REs)")
            else:
                update_display_tab(widgets, tab_name_key, "")
        
        clear_dfa_image(widgets)
        
        if self.current_frame_name not in ["FullTestMode", "StartScreen", "SyntacticTestMode"]: 
            if widgets.get("process_re_button"): widgets["process_re_button"].configure(state="normal")
            for btn_key in ["combine_nfas_button", "generate_dfa_button", "draw_dfa_button", "save_dfa_button", "tokenize_button"]:
                if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")
            
            if widgets.get("process_grammar_button"): widgets["process_grammar_button"].configure(state="normal")
            if widgets.get("parse_button"): widgets["parse_button"].configure(state="disabled")
            
            if widgets.get("part1_button"): widgets["part1_button"].configure(state="normal")
            if widgets.get("part2_button"): widgets["part2_button"].configure(state="disabled")
    
    def display_definitions_and_reserved_words(self):
        widgets = self.get_current_mode_widgets()
        if not widgets: return

        ts_builder = ["Definições de Padrões e Palavras Reservadas (Estático):\n"]
        ts_builder.append("Padrões de Token Definidos (Ordem de Prioridade):")
        for i, pattern_name in enumerate(self.pattern_order):
            ts_builder.append(f"  {i+1}. {pattern_name}: {self.definitions.get(pattern_name, 'ER não encontrada')}")
        
        ts_builder.append("\nPalavras Reservadas Identificadas (Lexema -> Tipo de Token):")
        if self.reserved_words_defs:
            for lexeme, token_type in sorted(self.reserved_words_defs.items()):
                ts_builder.append(f"  '{lexeme}' -> {token_type}")
        else:
            ts_builder.append("  (Nenhuma palavra reservada definida/identificada)")

        ts_builder.append("\nPadrões a Ignorar:")
        if self.patterns_to_ignore:
            for pattern_name in sorted(list(self.patterns_to_ignore)):
                ts_builder.append(f"  - {pattern_name}")
        else:
            ts_builder.append("  (Nenhum)")
            
        update_display_tab(widgets, "Tabela de Símbolos (Definições & Dinâmica)", "\n".join(ts_builder))
        if widgets.get("display_tab_view"):
            try:
                widgets["display_tab_view"].set("Tabela de Símbolos (Definições & Dinâmica)")
            except Exception:
                pass

    def run_full_test_case(self, test_case):
        current_widgets_for_full_test = self.full_test_mode_widgets
        if not current_widgets_for_full_test or not current_widgets_for_full_test.get("method_var"):
            messagebox.showerror("Erro Interno", "Não foi possível determinar o método de construção para o teste completo.")
            return
        
        self.active_construction_method = current_widgets_for_full_test["method_var"].get()
        self.current_test_name = f"{test_case['name']} ({self.active_construction_method.replace('_',' ').capitalize()})"

        self.reset_app_state() 

        update_text_content(current_widgets_for_full_test.get("re_display_textbox"), test_case["re_definitions"], keep_editable=False)
        update_text_content(current_widgets_for_full_test.get("source_display_textbox"), test_case["source_code"], keep_editable=False)

        try:
            self.definitions, self.pattern_order, self.reserved_words_defs, self.patterns_to_ignore = parse_re_file_data(test_case["re_definitions"])
        except Exception as e:
            messagebox.showerror("Erro ao Parsear Definições do Teste", f"Erro: {e}")
            return

        messagebox.showinfo("Teste Completo Iniciado", f"Executando teste completo para: {test_case['name']}\nMétodo: {self.active_construction_method.capitalize()}")

        try:
            self.process_regular_expressions() 
            
            if self.active_construction_method == "thompson":
                if self.individual_nfas and any(self.individual_nfas.values()):
                    self.combine_all_nfas() 
                else:
                    messagebox.showwarning("Teste Completo", "Nenhum NFA válido gerado na Etapa A para Thompson. Interrompendo.")
                    return
            
            if self.unminimized_dfa:
                self.generate_final_dfa_and_minimize() 
            else:
                 messagebox.showwarning("Teste Completo", "Nenhum AFD não minimizado gerado. Não é possível minimizar ou analisar. Interrompendo.")
                 return

            if self.dfa:
                self.draw_current_minimized_dfa() 
                self.tokenize_source() 
                messagebox.showinfo("Teste Completo Concluído", f"Teste '{test_case['name']}' ({self.active_construction_method.capitalize()}) concluído com sucesso.")
            else:
                 messagebox.showwarning("Teste Completo", "Nenhum AFD minimizado final gerado. Interrompendo antes de desenhar/tokenizar.")

        except Exception as e:
            messagebox.showerror("Erro no Teste Completo", f"Erro durante a execução do teste '{test_case['name']}':\n{type(e).__name__}: {str(e)}")

    def run_full_syntactic_test(self, test_case):
        self.reset_app_state()
        widgets = self.get_current_mode_widgets()
        if not widgets: return
        
        update_text_content(widgets["grammar_display"], test_case["grammar"], keep_editable=False)
        update_text_content(widgets["token_stream_display"], test_case["token_stream"], keep_editable=False)
        
        messagebox.showinfo("Teste Sintático Iniciado", f"Executando teste completo para: {test_case['name']}")
        
        try:
            grammar = Grammar.from_text(test_case["grammar"])
            update_display_tab(widgets, "Detalhes da Gramática", get_grammar_details_str(grammar))

            generator = SLRGenerator(grammar)
            firsts = generator.compute_first_sets()
            follows = generator.compute_follow_sets()
            update_display_tab(widgets, "Conjuntos First & Follow", get_first_follow_sets_str(firsts, follows))

            collection, _ = generator.build_canonical_collection()
            update_display_tab(widgets, "Coleção Canônica LR(0)", get_canonical_collection_str(collection))
            
            action_table, goto_table = generator.build_slr_table()
            update_display_tab(widgets, "Tabela de Análise SLR", get_slr_table_str(action_table, goto_table, grammar))
            
            token_stream = []
            if test_case["token_stream"]:
                for line in test_case["token_stream"].strip().splitlines():
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    if clean_line.endswith(','):
                        clean_line = clean_line[:-1]

                    parts = clean_line.split(',', 1)
                    token_type = parts[0].strip()
                    attribute = None
                    if len(parts) > 1:
                        attribute = parts[1].strip()

                    if not token_type and clean_line == "":
                        token_type = ","
                    token_stream.append(('', token_type, attribute))

            parser = SLRParser(grammar, action_table, goto_table)
            steps, success, message = parser.parse(token_stream)
            update_display_tab(widgets, "Passos da Análise", get_parse_steps_str(steps, success, message))

            if success:
                messagebox.showinfo("Teste Concluído", f"Teste '{test_case['name']}' concluído com sucesso.")
            else:
                messagebox.showwarning("Teste Concluído", f"Teste '{test_case['name']}' concluído com erro de sintaxe.")

        except Exception as e:
            tb_str = traceback.format_exc()
            messagebox.showerror("Erro no Teste", f"Ocorreu um erro no teste '{test_case['name']}':\n{e}\n\n{tb_str}")

    def load_re_from_file_for_current_mode(self): load_re_from_file_for_current_mode_callback(self)
    def load_test_data_for_auto_mode(self, test_case, show_message=True): load_test_data_for_auto_mode_callback(self, test_case, show_message)
    def process_regular_expressions(self): process_regular_expressions_callback(self)
    def combine_all_nfas(self): combine_all_nfas_callback(self)
    def generate_final_dfa_and_minimize(self): generate_final_dfa_and_minimize_callback(self)
    def draw_current_minimized_dfa(self): draw_current_minimized_dfa_callback(self)
    def save_dfa_to_file(self): save_dfa_to_file_callback(self)
    def tokenize_source(self): tokenize_source_callback(self)

    def process_grammar(self): process_grammar_callback(self)
    def run_syntactic_analysis(self): run_parser_callback(self)
    
    def run_part1_lexical(self): run_part1_lexical_callback(self)
    def run_part2_syntactic(self): run_part2_syntactic_callback(self)
