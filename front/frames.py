import customtkinter as ctk
from .controls import create_shared_controls_and_display 
from tests import TEST_CASES 

def create_start_screen_frame(app_instance):
    frame = ctk.CTkFrame(app_instance.container, fg_color=("gray90", "gray10")) 
    app_instance.frames["StartScreen"] = frame
    title_frame = ctk.CTkFrame(frame, fg_color="transparent")
    title_frame.pack(pady=(max(app_instance.winfo_height() // 7, 60), 20), padx=20, fill="x")
    app_icon_label = ctk.CTkLabel(title_frame, text="🛠️", font=("Segoe UI Emoji", 48))
    app_icon_label.pack(side="left", padx=(0, 20))
    title_text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
    title_text_frame.pack(side="left", expand=True, fill="x")
    ctk.CTkLabel(title_text_frame, text="Analisador Léxico", font=app_instance.font_title, anchor="w").pack(fill="x")
    ctk.CTkLabel(title_text_frame, text="Trabalho 1 - Linguagens Formais e Compiladores", font=app_instance.font_subtitle, anchor="w", text_color=("gray30", "gray70")).pack(fill="x")

    buttons_frame = ctk.CTkFrame(frame, fg_color="transparent")
    buttons_frame.pack(pady=20, padx=60, fill="x") 
    buttons_frame.grid_columnconfigure((0,1), weight=1)
    buttons_frame.grid_rowconfigure((0,1), weight=1) 

    manual_thompson_button = ctk.CTkButton(buttons_frame, text="📝 Modo Manual (Thompson)",
                                  command=lambda: app_instance.show_frame("ManualMode", construction_method="thompson"),
                                  height=60, font=app_instance.font_button) # Altura ajustada
    manual_thompson_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    manual_tree_button = ctk.CTkButton(buttons_frame, text="🌳 Modo Manual (Followpos)",
                                  command=lambda: app_instance.show_frame("ManualMode", construction_method="tree_direct_dfa"),
                                  height=60, font=app_instance.font_button)
    manual_tree_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

    # auto_button = ctk.CTkButton(buttons_frame, text="⚙️ Modo Testes Detalhados (Thompson)",
    #                             command=lambda: app_instance.show_frame("AutoTestMode"), # Antigo modo de teste
    #                             height=60, font=app_instance.font_button)
    # auto_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    
    full_auto_button = ctk.CTkButton(buttons_frame, text="🚀 Modo Teste Completo (Automático)",
                                command=lambda: app_instance.show_frame("FullTestMode"), # Novo modo
                                height=60, font=app_instance.font_button)
    full_auto_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew") 
    
    bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
    bottom_frame.pack(side="bottom", pady=(20, max(app_instance.winfo_height() // 10, 40)), padx=20, fill="x")
    credits_label = ctk.CTkLabel(bottom_frame, text="Desenvolvido por: Pedro Taglialenha, Vitor Praxedes & Enrico Caliolo ", font=app_instance.font_credits, text_color=("gray50", "gray50"))
    credits_label.pack(pady=(0, 20))
    exit_button = ctk.CTkButton(bottom_frame, text="Sair", command=app_instance.quit, width=120, font=app_instance.font_small_button, fg_color="transparent", border_width=1, border_color=("gray70", "gray30"), hover_color=("gray85", "gray20"))
    exit_button.pack()

    syntactic_button = ctk.CTkButton(buttons_frame, text="🧩 Gerador de Analisador Sintático (SLR)",
                                  command=lambda: app_instance.show_frame("SyntacticMode"),
                                  height=60, font=app_instance.font_button, fg_color="#1F6AA5")
    syntactic_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    full_auto_button = ctk.CTkButton(buttons_frame, text="🚀 Modo Teste Completo (Lexer)",
                                command=lambda: app_instance.show_frame("FullTestMode"),
                                height=60, font=app_instance.font_button)
    full_auto_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew") 

def create_manual_mode_frame_widgets(app_instance):
    frame = ctk.CTkFrame(app_instance.container)
    app_instance.frames["ManualMode"] = frame
    app_instance.manual_mode_widgets = create_shared_controls_and_display(frame, app_instance)
    app_instance.manual_mode_widgets["re_input_textbox"].insert("0.0", "# Defina suas expressões regulares aqui.\n# Ex: ID: (a|b)*abb\n# Ex: IF: if\n# Ex: WS: [ \t\n]+ %ignore\n")
    app_instance.manual_mode_widgets["source_code_input_textbox"].insert("0.0", "// Código fonte para teste.")

def create_auto_test_mode_frame_widgets(app_instance): 
    frame = ctk.CTkFrame(app_instance.container)
    app_instance.frames["AutoTestMode"] = frame 
    app_instance.auto_test_mode_widgets = create_shared_controls_and_display(frame, app_instance) 
    
    scrollable_control_panel = app_instance.auto_test_mode_widgets["control_frame"] 
    back_button_ref = app_instance.auto_test_mode_widgets.get("back_button")
    if back_button_ref: back_button_ref.pack_forget()

    ctk.CTkLabel(scrollable_control_panel, text="3. Selecionar Teste (Passo a Passo):", font=("Arial", 13, "bold")).pack(pady=(15,5), padx=10, anchor="w", fill="x")
    inner_scrollable_test_buttons = ctk.CTkScrollableFrame(scrollable_control_panel, height=120) 
    inner_scrollable_test_buttons.pack(pady=5, padx=10, fill="x")
    for i, test_case in enumerate(TEST_CASES):
        btn = ctk.CTkButton(inner_scrollable_test_buttons, text=f"Carregar: {test_case['name']}",
                            command=lambda tc=test_case: app_instance.load_test_data_for_auto_mode(tc))
        btn.pack(pady=3, fill="x")
    if back_button_ref: back_button_ref.pack(pady=(20,10), padx=10, fill="x")

def create_syntactic_mode_frame_widgets(app_instance):
    frame = ctk.CTkFrame(app_instance.container)
    app_instance.frames["SyntacticMode"] = frame
    widgets = {}

    frame.grid_columnconfigure(0, weight=1, minsize=420) 
    frame.grid_columnconfigure(1, weight=3)             
    frame.grid_rowconfigure(0, weight=1)

    control_frame = ctk.CTkScrollableFrame(frame, label_text="Controles do Analisador Sintático")
    control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    widgets["control_frame"] = control_frame

    # --- Entradas ---
    ctk.CTkLabel(control_frame, text="1. Definição da Gramática Livre de Contexto:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w")
    grammar_input = ctk.CTkTextbox(control_frame, height=250, font=("Consolas", 11))
    grammar_input.insert("1.0", "# Insira a gramática aqui (Ex: E ::= E + T)\n# O símbolo inicial é o do lado esquerdo da primeira produção.\n# Use '&' para épsilon.\nE ::= E + T\nE ::= T\nT ::= T * F\nT ::= F\nF ::= ( E )\nF ::= id")
    grammar_input.pack(pady=2, padx=10, fill="x")
    widgets["grammar_input"] = grammar_input

    ctk.CTkLabel(control_frame, text="2. Palavras Reservadas (opcional, uma por linha):", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w")
    reserved_words_input = ctk.CTkTextbox(control_frame, height=80, font=("Consolas", 11))
    reserved_words_input.pack(pady=2, padx=10, fill="x")
    widgets["reserved_words_input"] = reserved_words_input
    
    ctk.CTkLabel(control_frame, text="3. Sequência de Tokens de Entrada (um por linha, formato: TIPO,ATRIBUTO):", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w")
    token_stream_input = ctk.CTkTextbox(control_frame, height=150, font=("Consolas", 11))
    token_stream_input.insert("1.0", "id,0\n+,\nid,1\n*,\nid,2")
    token_stream_input.pack(pady=2, padx=10, fill="x")
    widgets["token_stream_input"] = token_stream_input

    # --- Botões de Ação ---
    process_grammar_button = ctk.CTkButton(control_frame, text="A. Processar Gramática (Gerar Tabela SLR)", command=app_instance.process_grammar)
    process_grammar_button.pack(pady=(15, 5), padx=10, fill="x")
    widgets["process_grammar_button"] = process_grammar_button
    
    parse_button = ctk.CTkButton(control_frame, text="B. Analisar Sequência de Tokens", command=app_instance.run_syntactic_analysis, state="disabled")
    parse_button.pack(pady=5, padx=10, fill="x")
    widgets["parse_button"] = parse_button
    
    back_button = ctk.CTkButton(control_frame, text="Voltar à Tela Inicial", command=lambda: app_instance.show_frame("StartScreen"))
    back_button.pack(pady=(20,10), padx=10, fill="x")
    
    # --- Painel de Exibição ---
    display_tab_view = ctk.CTkTabview(frame) 
    display_tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    widgets["display_tab_view"] = display_tab_view
    
    tab_names = [
        "Detalhes da Gramática", 
        "Conjuntos First & Follow",
        "Coleção Canônica LR(0)",
        "Tabela de Análise SLR",
        "Passos da Análise"
    ]
    textboxes_map = {} 
    for name in tab_names:
        tab = display_tab_view.add(name)
        textbox = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 10), state="disabled")
        textbox.pack(expand=True, fill="both", padx=5, pady=5)
        textboxes_map[name] = textbox
    
    widgets["textboxes_map"] = textboxes_map
    display_tab_view.set(tab_names[0])
    
    app_instance.syntactic_mode_widgets = widgets

def create_full_test_mode_frame_widgets(app_instance):
    frame = ctk.CTkFrame(app_instance.container)
    app_instance.frames["FullTestMode"] = frame
    app_instance.full_test_mode_widgets = {} 

    frame.grid_columnconfigure(0, weight=1, minsize=300) 
    frame.grid_columnconfigure(1, weight=3)            
    frame.grid_rowconfigure(0, weight=1)                

    left_panel = ctk.CTkFrame(frame)
    left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    ctk.CTkLabel(left_panel, text="Modo de Teste Completo", font=("Arial", 16, "bold")).pack(pady=10, padx=10)

    ctk.CTkLabel(left_panel, text="Escolha o Método de Construção:").pack(pady=(10,0), padx=10)
    method_var = ctk.StringVar(value="thompson")
    app_instance.full_test_mode_widgets["method_var"] = method_var
    thompson_radio = ctk.CTkRadioButton(left_panel, text="Thompson", variable=method_var, value="thompson")
    thompson_radio.pack(pady=2, padx=20, anchor="w")
    followpos_radio = ctk.CTkRadioButton(left_panel, text="Followpos", variable=method_var, value="tree_direct_dfa")
    followpos_radio.pack(pady=2, padx=20, anchor="w")

    ctk.CTkLabel(left_panel, text="Definições Regulares do Teste:").pack(pady=(10,2), padx=10, anchor="w")
    re_display_textbox = ctk.CTkTextbox(left_panel, height=150, font=("Consolas", 10), state="disabled")
    re_display_textbox.pack(pady=2, padx=10, fill="x", expand=False)
    app_instance.full_test_mode_widgets["re_display_textbox"] = re_display_textbox

    ctk.CTkLabel(left_panel, text="Texto Fonte do Teste:").pack(pady=(10,2), padx=10, anchor="w")
    source_display_textbox = ctk.CTkTextbox(left_panel, height=100, font=("Consolas", 10), state="disabled")
    source_display_textbox.pack(pady=2, padx=10, fill="x", expand=False)
    app_instance.full_test_mode_widgets["source_display_textbox"] = source_display_textbox

    ctk.CTkLabel(left_panel, text="Selecione um Teste para Executar:").pack(pady=(10,5), padx=10)
    test_buttons_scroll_frame = ctk.CTkScrollableFrame(left_panel, height=200)
    test_buttons_scroll_frame.pack(pady=5, padx=10, fill="both", expand=True)
    app_instance.full_test_mode_widgets["test_buttons_frame"] = test_buttons_scroll_frame

    for i, test_case in enumerate(TEST_CASES):
        btn = ctk.CTkButton(test_buttons_scroll_frame, text=f"Executar: {test_case['name']}",
                            command=lambda tc=test_case: app_instance.run_full_test_case(tc))
        btn.pack(pady=3, padx=5, fill="x")
    
    back_button = ctk.CTkButton(left_panel, text="Voltar à Tela Inicial", command=lambda: app_instance.show_frame("StartScreen"))
    back_button.pack(pady=(20,10), padx=10, fill="x")


    right_panel = ctk.CTkTabview(frame)
    right_panel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    app_instance.full_test_mode_widgets["display_tab_view"] = right_panel
    
    tab_names = [
        "ER ➔ NFA Ind. / Árvore+Followpos", 
        "NFA Combinado (União ε) / AFD Direto (Não-Minim.)", 
        "AFD Minimizado (Final)", 
        "Desenho AFD Minimizado", 
        "Tabela de Símbolos (Definições & Dinâmica)", 
        "Saída do Analisador Léxico (Tokens)"
    ]
    textboxes_map = {} 
    app_instance.full_test_mode_widgets["dfa_image_label"] = None 

    for name in tab_names:
        tab = right_panel.add(name)
        if name == "Desenho AFD Minimizado":
            image_label = ctk.CTkLabel(tab, text="Nenhum AFD desenhado ainda.", compound="top")
            image_label.pack(expand=True, fill="both", padx=5, pady=5)
            app_instance.full_test_mode_widgets["dfa_image_label"] = image_label
        else:
            textbox = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 10), state="disabled")
            textbox.pack(expand=True, fill="both", padx=5, pady=5)
            textboxes_map[name] = textbox
    
    app_instance.full_test_mode_widgets["textboxes_map"] = textboxes_map
    if tab_names:
        right_panel.set(tab_names[0])