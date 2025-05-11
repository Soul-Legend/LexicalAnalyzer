import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- Imports from our modules ---
from regex_processing import infix_to_postfix
from nfa_model import NFA, NFAState, postfix_to_nfa, combine_nfas
from dfa_model import nfa_to_dfa # DFA class is used internally by nfa_to_dfa
from lexer_core import Lexer
from input_parser import parse_re_file_data
from output_formatters import get_nfa_details_str, get_dfa_table_str, get_dfa_anexo_ii_format


class LexerGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gerador de Analisadores Léxicos")
        self.geometry("1200x850") # Increased height a bit
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue") 

        # --- Application State ---
        self.definitions = {}
        self.pattern_order = []
        self.reserved_words_defs = {} # "if" -> "IF_TOKEN"
        self.individual_nfas = {} # pattern_name -> NFA_object
        
        self.combined_nfa_object_for_display = None # A conceptual NFA object for display
        self.combined_nfa_start_state_actual = None # The actual start NFAState for DFA conversion
        self.combined_nfa_accept_map_actual = None # The actual map {NFAState: pattern} for DFA conversion
        self.combined_nfa_alphabet_actual = None # The actual alphabet set for DFA conversion

        self.dfa_instance = None # Will hold the generated DFA object
        self.lexer_instance = None # Will hold the Lexer object

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3) # Give more space to display
        self.grid_rowconfigure(0, weight=1)


        # --- Control Frame (Left) ---
        self.control_frame = ctk.CTkFrame(self, width=350) # Increased width
        self.control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.control_frame.grid_propagate(False) 

        # RE Definitions
        ctk.CTkLabel(self.control_frame, text="1. Definições Regulares (Anexo I):").pack(pady=(10,0), padx=10, anchor="w")
        self.re_input_textbox = ctk.CTkTextbox(self.control_frame, height=200) # Increased height
        self.re_input_textbox.pack(pady=5, padx=10, fill="x")
        self.re_input_textbox.insert("0.0", "ID: [a-zA-Z]([a-zA-Z]|[0-9])*\nNUM: [0-9]+|[1-9]([0-9])*\nFLOAT: [0-9]+\\.[0-9]*([eE][+-]?[0-9]+)?\nIF: if\nELSE: else\nWHILE: while\n# Comentário de linha simples\nWS: ( |\t|\n|\r)+")
        
        self.load_re_file_button = ctk.CTkButton(self.control_frame, text="Carregar Definições de Arquivo", command=self.load_re_from_file)
        self.load_re_file_button.pack(pady=(10,0), padx=10, fill="x")

        self.process_re_button = ctk.CTkButton(self.control_frame, text="A. Processar REs e Gerar NFAs Individuais", command=self.gui_process_regular_expressions, state="normal")
        self.process_re_button.pack(pady=10, padx=10, fill="x")

        self.combine_nfas_button = ctk.CTkButton(self.control_frame, text="B. Unir NFAs (ε-transições)", command=self.gui_combine_all_nfas, state="disabled")
        self.combine_nfas_button.pack(pady=5, padx=10, fill="x")

        self.generate_dfa_button = ctk.CTkButton(self.control_frame, text="C. Determinizar para AFD", command=self.gui_generate_dfa_from_nfa, state="disabled")
        self.generate_dfa_button.pack(pady=5, padx=10, fill="x")
        
        self.save_dfa_button = ctk.CTkButton(self.control_frame, text="Salvar Tabela AFD (Anexo II)", command=self.gui_save_dfa_to_file, state="disabled")
        self.save_dfa_button.pack(pady=5, padx=10, fill="x")

        # Lexer Execution
        ctk.CTkLabel(self.control_frame, text="2. Texto Fonte para Análise:").pack(pady=(20,0), padx=10, anchor="w")
        self.source_code_input_textbox = ctk.CTkTextbox(self.control_frame, height=150) # Increased height
        self.source_code_input_textbox.pack(pady=5, padx=10, fill="x")
        self.source_code_input_textbox.insert("0.0", "identificador1 123 if\n  0.99 else num_float 3.14e-2\n // outro_id\ninv@lid while")

        self.tokenize_button = ctk.CTkButton(self.control_frame, text="Analisar Texto Fonte (Gerar Tokens)", command=self.gui_tokenize_source, state="disabled")
        self.tokenize_button.pack(pady=10, padx=10, fill="x")

        # --- Display Frame (Right) ---
        self.display_frame = ctk.CTkTabview(self)
        self.display_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.tab_re_nfa_name = "REs & NFAs Ind."
        self.tab_combined_nfa_name = "NFA Combinado"
        self.tab_dfa_name = "AFD (Tabela)"
        self.tab_tokens_name = "Tokens Gerados"

        self.tab_re_nfa = self.display_frame.add(self.tab_re_nfa_name)
        self.tab_combined_nfa = self.display_frame.add(self.tab_combined_nfa_name)
        self.tab_dfa = self.display_frame.add(self.tab_dfa_name)
        self.tab_tokens = self.display_frame.add(self.tab_tokens_name)

        self.re_nfa_output_textbox = ctk.CTkTextbox(self.tab_re_nfa, wrap="none", font=("Courier New", 10))
        self.re_nfa_output_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        self.combined_nfa_output_textbox = ctk.CTkTextbox(self.tab_combined_nfa, wrap="none", font=("Courier New", 10))
        self.combined_nfa_output_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        self.dfa_output_textbox = ctk.CTkTextbox(self.tab_dfa, wrap="none", font=("Courier New", 10))
        self.dfa_output_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        self.token_output_textbox = ctk.CTkTextbox(self.tab_tokens, wrap="none", font=("Courier New", 10))
        self.token_output_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.reset_application_state() # Initialize UI elements properly

    def _update_display(self, textbox, content):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", content)
        textbox.configure(state="disabled") # Make read-only

    def reset_application_state(self):
        self.definitions = {}
        self.pattern_order = []
        self.reserved_words_defs = {}
        self.individual_nfas = {}
        
        self.combined_nfa_object_for_display = None
        self.combined_nfa_start_state_actual = None
        self.combined_nfa_accept_map_actual = None
        self.combined_nfa_alphabet_actual = None

        self.dfa_instance = None
        self.lexer_instance = None
        
        NFA.reset_state_ids() # Important: Reset global NFA state counter

        self._update_display(self.re_nfa_output_textbox, "Defina ou carregue expressões regulares.")
        self._update_display(self.combined_nfa_output_textbox, "NFAs individuais precisam ser gerados e combinados.")
        self._update_display(self.dfa_output_textbox, "NFA combinado precisa ser determinizado.")
        self._update_display(self.token_output_textbox, "AFD precisa ser gerado e texto fonte fornecido.")

        self.process_re_button.configure(state="normal")
        self.combine_nfas_button.configure(state="disabled")
        self.generate_dfa_button.configure(state="disabled")
        self.save_dfa_button.configure(state="disabled")
        self.tokenize_button.configure(state="disabled")
        self.display_frame.set(self.tab_re_nfa_name)


    def load_re_from_file(self):
        filepath = filedialog.askopenfilename(
            title="Abrir Arquivo de Definições Regulares",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.re_input_textbox.delete("1.0", "end")
                self.re_input_textbox.insert("1.0", content)
                messagebox.showinfo("Sucesso", "Arquivo de definições carregado.")
                self.reset_application_state() # Reset state when new REs are loaded
            except Exception as e:
                messagebox.showerror("Erro ao Ler Arquivo", str(e))
                
    def gui_process_regular_expressions(self):
        re_content = self.re_input_textbox.get("1.0", "end-1c")
        if not re_content.strip():
            messagebox.showerror("Erro", "Nenhuma definição regular fornecida.")
            return

        try:
            NFA.reset_state_ids() # Reset before processing a batch of REs
            self.definitions, self.pattern_order, self.reserved_words_defs = parse_re_file_data(re_content)
            self.individual_nfas = {} # pattern_name -> NFA_object
            output_str = "Processando Definições Regulares:\n\n"
            has_actual_nfas = False

            for name in self.pattern_order:
                regex_str = self.definitions[name]
                output_str += f"Definição: {name}: {regex_str}\n"
                
                # If it's a reserved word defined simply (e.g., IF: if), skip NFA generation for it.
                # It's handled by the reserved_words_defs map in the lexer.
                if name.lower() in self.reserved_words_defs and self.reserved_words_defs[name.lower()] == name:
                     output_str += f"  '{name}' é uma Palavra Reservada (Padrão: {name}). Será tratada pelo Léxico.\n\n"
                     self.individual_nfas[name] = None # Mark that no NFA is built for this
                     continue

                postfix_expr = infix_to_postfix(regex_str)
                output_str += f"  Expressão Pós-fixada: {postfix_expr}\n"
                
                # NFA.reset_state_ids() # No, reset only once per batch
                nfa = postfix_to_nfa(postfix_expr)
                self.individual_nfas[name] = nfa
                has_actual_nfas = True
                output_str += get_nfa_details_str(nfa, f"NFA para '{name}'") + "\n\n"
            
            self._update_display(self.re_nfa_output_textbox, output_str)
            self.display_frame.set(self.tab_re_nfa_name)
            
            if has_actual_nfas or any(nfa is not None for nfa in self.individual_nfas.values()):
                self.combine_nfas_button.configure(state="normal")
            else: # Only reserved words defined, no NFAs to combine
                self.combine_nfas_button.configure(state="disabled") # Cannot combine if no NFAs built
                # However, we might still be able to create a lexer if only reserved words are used (unlikely for this assignment)

            self.generate_dfa_button.configure(state="disabled")
            self.save_dfa_button.configure(state="disabled")
            self.tokenize_button.configure(state="disabled")
            messagebox.showinfo("Sucesso", "Definições processadas e NFAs individuais gerados (se aplicável).")

        except Exception as e:
            messagebox.showerror("Erro ao Processar REs", str(e))
            self._update_display(self.re_nfa_output_textbox, f"Erro:\n{str(e)}")

    def gui_combine_all_nfas(self):
        nfas_to_combine = {k: v for k, v in self.individual_nfas.items() if v is not None}
        if not nfas_to_combine:
            messagebox.showerror("Erro", "Nenhum NFA individual para combinar. Processe REs que gerem NFAs.")
            return
        try:
            # NFA.reset_state_ids() # No, global counter handles uniqueness. Reset was done before RE processing.
            # The combine_nfas function will create a new start state.
            
            start_s, accept_map, alphabet = combine_nfas(nfas_to_combine)
            self.combined_nfa_start_state_actual = start_s
            self.combined_nfa_accept_map_actual = accept_map
            self.combined_nfa_alphabet_actual = alphabet

            # For display purposes, create a conceptual NFA object
            self.combined_nfa_object_for_display = NFA(start_s, None) # Accept state not singular here
            self.combined_nfa_object_for_display.accept_states_map = accept_map # Store the map for the formatter
            
            # Populate states for the display NFA by traversing from its new start state
            all_combined_states = set()
            q_bfs = [start_s]
            visited_display = {start_s}
            while q_bfs:
                curr = q_bfs.pop(0)
                all_combined_states.add(curr)
                # Also add states from the original NFAs that are now part of this combined structure
                # This ensures that the `get_nfa_details_str` can find them if it needs to.
                for nfa_orig in nfas_to_combine.values():
                    all_combined_states.update(nfa_orig.states)

                for _, next_states_s in curr.transitions.items():
                    for next_s_node in next_states_s:
                        if next_s_node not in visited_display:
                            visited_display.add(next_s_node)
                            q_bfs.append(next_s_node)
            self.combined_nfa_object_for_display.states = all_combined_states
            self.combined_nfa_object_for_display.alphabet = alphabet


            output_str = get_nfa_details_str(self.combined_nfa_object_for_display, "NFA Combinado")
            self._update_display(self.combined_nfa_output_textbox, output_str)
            self.display_frame.set(self.tab_combined_nfa_name)
            self.generate_dfa_button.configure(state="normal")
            self.save_dfa_button.configure(state="disabled")
            self.tokenize_button.configure(state="disabled")
            messagebox.showinfo("Sucesso", "NFAs combinados.")
        except Exception as e:
            messagebox.showerror("Erro ao Combinar NFAs", str(e))
            self._update_display(self.combined_nfa_output_textbox, f"Erro:\n{str(e)}")

    def gui_generate_dfa_from_nfa(self):
        if not self.combined_nfa_start_state_actual or \
           self.combined_nfa_accept_map_actual is None or \
           self.combined_nfa_alphabet_actual is None:
            messagebox.showerror("Erro", "NFA combinado não disponível. Combine os NFAs primeiro.")
            return
        try:
            self.dfa_instance = nfa_to_dfa(
                self.combined_nfa_start_state_actual, 
                self.combined_nfa_accept_map_actual, 
                self.combined_nfa_alphabet_actual, 
                self.pattern_order 
            )
            output_str = get_dfa_table_str(self.dfa_instance)
            self._update_display(self.dfa_output_textbox, output_str)
            self.display_frame.set(self.tab_dfa_name)
            
            # Setup lexer with the generated DFA and reserved words definitions
            self.lexer_instance = Lexer(self.dfa_instance, self.reserved_words_defs)

            self.tokenize_button.configure(state="normal")
            self.save_dfa_button.configure(state="normal")
            messagebox.showinfo("Sucesso", "AFD gerado e Analisador Léxico pronto.")
        except Exception as e:
            messagebox.showerror("Erro ao Gerar AFD", str(e))
            self._update_display(self.dfa_output_textbox, f"Erro:\n{str(e)}")

    def gui_save_dfa_to_file(self):
        if not self.dfa_instance:
            messagebox.showerror("Erro", "Nenhum AFD para salvar.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
            title="Salvar Tabela AFD como (Formato Anexo II)"
        )
        if filepath:
            try:
                anexo_ii_content = get_dfa_anexo_ii_format(self.dfa_instance)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(anexo_ii_content)
                
                human_readable_content = get_dfa_table_str(self.dfa_instance)
                human_readable_filepath = filepath.replace(".txt", "_human_readable.txt")
                if human_readable_filepath == filepath: 
                    human_readable_filepath += "_human_readable" # Append if no extension change
                with open(human_readable_filepath, 'w', encoding='utf-8') as f:
                    f.write(human_readable_content)

                messagebox.showinfo("Sucesso", f"Tabela AFD salva em:\n{filepath}\n(e formato legível em {human_readable_filepath})")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar AFD", str(e))

    def gui_tokenize_source(self):
        if not self.lexer_instance:
            messagebox.showerror("Erro", "Analisador Léxico não está pronto. Gere o AFD primeiro.")
            return
        
        source_code = self.source_code_input_textbox.get("1.0", "end-1c")
        # Do not strip here, lexer should handle leading/trailing whitespace based on WS rule
        # if not source_code.strip(): 
        if not source_code:
            messagebox.showinfo("Info", "Nenhum código fonte para analisar.")
            self._update_display(self.token_output_textbox, "")
            return

        try:
            tokens = self.lexer_instance.tokenize(source_code)
            output_str = "Tokens Gerados (lexema, padrão):\n"
            for lexeme, pattern in tokens:
                output_str += f"<{lexeme}, {pattern}>\n"
            
            self._update_display(self.token_output_textbox, output_str)
            self.display_frame.set(self.tab_tokens_name)
        except Exception as e:
            messagebox.showerror("Erro na Análise Léxica", str(e))
            self._update_display(self.token_output_textbox, f"Erro durante a tokenização:\n{str(e)}")


if __name__ == "__main__":
    app = LexerGeneratorApp()
    app.mainloop()