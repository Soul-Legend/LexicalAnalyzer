import customtkinter as ctk
from tkinter import filedialog, messagebox 

from .frames import create_start_screen_frame, create_manual_mode_frame_widgets, create_auto_test_mode_frame_widgets
from .callbacks import (load_re_from_file_for_current_mode_callback, 
                        load_test_data_for_auto_mode_callback,
                        process_regular_expressions_callback, 
                        combine_all_nfas_callback,
                        generate_final_dfa_and_minimize_callback, 
                        draw_current_minimized_dfa_callback,
                        save_dfa_to_file_callback, 
                        tokenize_source_callback)
from .ui_utils import update_display_tab, clear_dfa_image
from tests import TEST_CASES 
from lexer_core import SymbolTable # Importar SymbolTable


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
        
        self.augmented_syntax_tree_followpos = None
        self.followpos_table_followpos = None

        self.unminimized_dfa = None 
        self.dfa = None 
        self.lexer = None
        self.current_test_name = "Manual"
        self.active_construction_method = "thompson" 
        
        self.images_output_dir = "imagens"
        self.symbol_table_instance = SymbolTable() # Instância da TS

        self.manual_mode_widgets = {}
        self.auto_test_mode_widgets = {}

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.current_frame_name = None

        create_start_screen_frame(self)
        create_manual_mode_frame_widgets(self)
        create_auto_test_mode_frame_widgets(self)

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
            
            combine_btn = widgets.get("combine_nfas_button")
            if combine_btn:
                if is_thompson:
                    combine_btn.configure(text="B. Unir NFAs (Thompson)", command=self.combine_all_nfas, state="disabled")
                else: 
                    combine_btn.configure(text="B. (União em Etapa A para Followpos)", command=lambda: None, state="disabled")

            process_btn_text = "A. REs ➔ Autômatos Ind. / AFD Direto"
            if widgets.get("process_re_button"):
                 widgets["process_re_button"].configure(text=process_btn_text)
            
            generate_dfa_btn = widgets.get("generate_dfa_button")
            if generate_dfa_btn:
                generate_dfa_btn.configure(text="C. Determinar/Minimizar ➔ AFD Final")

        if frame_name == "AutoTestMode":
            self.active_construction_method = "thompson"
            widgets = self.get_current_mode_widgets()
            if widgets and widgets.get("process_re_button"):
                 widgets["process_re_button"].configure(text="A. REs ➔ NFAs (Thompson)")
            if widgets and widgets.get("combine_nfas_button"):
                widgets["combine_nfas_button"].configure(text="B. Unir NFAs (Thompson)", command=self.combine_all_nfas)

            if widgets and widgets.get("re_input_textbox") and \
               not widgets["re_input_textbox"].get("1.0", "end-1c").strip() and TEST_CASES:
                self.load_test_data_for_auto_mode(TEST_CASES[0], show_message=False)
        
        self.reset_app_state()

    def get_current_mode_widgets(self):
        if self.current_frame_name == "ManualMode": return self.manual_mode_widgets
        elif self.current_frame_name == "AutoTestMode": return self.auto_test_mode_widgets
        return None

    def _set_re_definitions_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets or not widgets.get("re_input_textbox"): return
        re_textbox = widgets["re_input_textbox"]
        re_textbox.configure(state="normal")
        re_textbox.delete("1.0", "end")
        re_textbox.insert("1.0", content)
        re_textbox.configure(state="disabled")
        self.reset_app_state()

    def _set_source_code_for_current_mode(self, content):
        widgets = self.get_current_mode_widgets()
        if not widgets or not widgets.get("source_code_input_textbox"): return
        source_textbox = widgets["source_code_input_textbox"]
        source_textbox.configure(state="normal")
        source_textbox.delete("1.0", "end")
        source_textbox.insert("1.0", content)
        source_textbox.configure(state="disabled")
        if self.dfa: update_display_tab(widgets, "Tokens Gerados", f"({self.current_test_name}: Texto fonte alterado, reanalisar)")

    def reset_app_state(self):
        self.definitions.clear(); self.pattern_order.clear(); self.reserved_words_defs.clear(); self.patterns_to_ignore.clear()
        self.individual_nfas.clear(); self.combined_nfa_start_obj = None; self.combined_nfa_accept_map = None; self.combined_nfa_alphabet = None
        self.augmented_syntax_tree_followpos = None; self.followpos_table_followpos = None;
        self.unminimized_dfa = None; self.dfa = None; self.lexer = None
        self.symbol_table_instance.clear() # Limpa a TS principal
        
        widgets = self.get_current_mode_widgets()
        if not widgets: return

        for tab_name_key in widgets.get("textboxes_map", {}): 
            if tab_name_key == "Tabela de Símbolos":
                update_display_tab(widgets, tab_name_key, "Tabela de Símbolos (Definições Estáticas):\n(Aguardando processamento de REs)")
            else:
                update_display_tab(widgets, tab_name_key, "")
        
        clear_dfa_image(widgets)
        
        if widgets.get("process_re_button"): widgets["process_re_button"].configure(state="normal")
        
        for btn_key in ["combine_nfas_button", "generate_dfa_button", "draw_dfa_button", "save_dfa_button", "tokenize_button"]:
            if widgets.get(btn_key): widgets[btn_key].configure(state="disabled")
    
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
            
        update_display_tab(widgets, "Tabela de Símbolos", "\n".join(ts_builder))
        if widgets.get("display_tab_view"):
            try:
                widgets["display_tab_view"].set("Tabela de Símbolos")
            except Exception:
                pass

    def load_re_from_file_for_current_mode(self): load_re_from_file_for_current_mode_callback(self)
    def load_test_data_for_auto_mode(self, test_case, show_message=True): load_test_data_for_auto_mode_callback(self, test_case, show_message)
    def process_regular_expressions(self): process_regular_expressions_callback(self)
    def combine_all_nfas(self): combine_all_nfas_callback(self)
    def generate_final_dfa_and_minimize(self): generate_final_dfa_and_minimize_callback(self)
    def draw_current_minimized_dfa(self): draw_current_minimized_dfa_callback(self)
    def save_dfa_to_file(self): save_dfa_to_file_callback(self)
    def tokenize_source(self): tokenize_source_callback(self)