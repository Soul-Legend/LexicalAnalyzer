import customtkinter as ctk

def create_shared_controls_and_display(parent_frame, app_instance):
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
    
    load_re_file_button = ctk.CTkButton(outer_control_frame, text="Carregar Definições de Arquivo", command=app_instance.load_re_from_file_for_current_mode)
    load_re_file_button.pack(pady=5, padx=10, fill="x")
    widgets["load_re_file_button"] = load_re_file_button

    process_re_button = ctk.CTkButton(outer_control_frame, text="A. REs ➔ Autômatos Ind. / AFD Direto", command=app_instance.process_regular_expressions)
    process_re_button.pack(pady=(10,3), padx=10, fill="x")
    widgets["process_re_button"] = process_re_button

    combine_nfas_button = ctk.CTkButton(outer_control_frame, text="B. Unir NFAs (Thompson)", command=app_instance.combine_all_nfas, state="disabled")
    combine_nfas_button.pack(pady=3, padx=10, fill="x")
    widgets["combine_nfas_button"] = combine_nfas_button

    generate_dfa_button = ctk.CTkButton(outer_control_frame, text="C. Determinar/Minimizar ➔ AFD Final", command=app_instance.generate_final_dfa_and_minimize, state="disabled")
    generate_dfa_button.pack(pady=3, padx=10, fill="x")
    widgets["generate_dfa_button"] = generate_dfa_button
    
    draw_dfa_button = ctk.CTkButton(outer_control_frame, text="🎨 Desenhar AFD Minimizado", command=app_instance.draw_current_minimized_dfa, state="disabled")
    draw_dfa_button.pack(pady=3, padx=10, fill="x")
    widgets["draw_dfa_button"] = draw_dfa_button

    save_dfa_button = ctk.CTkButton(outer_control_frame, text="Salvar Tabela AFD Minimizada (Anexo II)", command=app_instance.save_dfa_to_file, state="disabled")
    save_dfa_button.pack(pady=(3,10), padx=10, fill="x")
    widgets["save_dfa_button"] = save_dfa_button

    ctk.CTkLabel(outer_control_frame, text="2. Texto Fonte para Análise:", font=("Arial", 13, "bold")).pack(pady=(10,2), padx=10, anchor="w", fill="x")
    source_code_input_textbox = ctk.CTkTextbox(outer_control_frame, height=150, font=("Consolas", 11))
    source_code_input_textbox.pack(pady=2, padx=10, fill="x", expand=False)
    widgets["source_code_input_textbox"] = source_code_input_textbox

    tokenize_button = ctk.CTkButton(outer_control_frame, text="Analisar Texto Fonte (Gerar Tokens)", command=app_instance.tokenize_source, state="disabled")
    tokenize_button.pack(pady=5, padx=10, fill="x")
    widgets["tokenize_button"] = tokenize_button
    
    back_button = ctk.CTkButton(outer_control_frame, text="Voltar à Tela Inicial", command=lambda: app_instance.show_frame("StartScreen"))
    back_button.pack(pady=(20,10), padx=10, fill="x")
    widgets["back_button"] = back_button

    display_tab_view = ctk.CTkTabview(parent_frame) 
    display_tab_view.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    widgets["display_tab_view"] = display_tab_view
    
    tab_names = ["Construção Detalhada", "Autômato Intermediário / União", "AFD (Não Minimizado e Minimizado)", "Desenho AFD", "Tabela de Símbolos", "Tokens Gerados"]
    textboxes_map = {} 
    widgets["dfa_image_label"] = None
    for name in tab_names:
        tab = display_tab_view.add(name)
        if name == "Desenho AFD":
            image_label = ctk.CTkLabel(tab, text="Nenhum AFD desenhado ainda.", compound="top")
            image_label.pack(expand=True, fill="both", padx=5, pady=5)
            widgets["dfa_image_label"] = image_label
        else:
            textbox = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 10), state="disabled")
            textbox.pack(expand=True, fill="both", padx=5, pady=5)
            textboxes_map[name] = textbox
    
    widgets["textboxes_map"] = textboxes_map
    display_tab_view.set(tab_names[0])
    
    return widgets