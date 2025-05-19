import customtkinter as ctk
from .controls import create_shared_controls_and_display # Referência local
from tests import TEST_CASES # Importa TEST_CASES

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
    buttons_frame.pack(pady=40, padx=80, fill="x")
    buttons_frame.grid_columnconfigure((0,1), weight=1)
    buttons_frame.grid_rowconfigure((0,1), weight=1)

    manual_thompson_button = ctk.CTkButton(buttons_frame, text="📝 Modo Manual (Thompson)",
                                  command=lambda: app_instance.show_frame("ManualMode", construction_method="thompson"),
                                  height=70, font=app_instance.font_button)
    manual_thompson_button.grid(row=0, column=0, padx=15, pady=15, sticky="ew")

    manual_tree_button = ctk.CTkButton(buttons_frame, text="🌳 Modo Manual (Followpos)",
                                  command=lambda: app_instance.show_frame("ManualMode", construction_method="tree_direct_dfa"),
                                  height=70, font=app_instance.font_button)
    manual_tree_button.grid(row=0, column=1, padx=15, pady=15, sticky="ew")

    auto_button = ctk.CTkButton(buttons_frame, text="⚙️ Modo Automático (Testes via Thompson)",
                                command=lambda: app_instance.show_frame("AutoTestMode"),
                                height=70, font=app_instance.font_button)
    auto_button.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="ew")
    
    bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
    bottom_frame.pack(side="bottom", pady=(20, max(app_instance.winfo_height() // 10, 40)), padx=20, fill="x")
    credits_label = ctk.CTkLabel(bottom_frame, text="Desenvolvido por: Pedro Taglialenha, Vitor Praxedes & Enrico Caliolo ", font=app_instance.font_credits, text_color=("gray50", "gray50"))
    credits_label.pack(pady=(0, 20))
    exit_button = ctk.CTkButton(bottom_frame, text="Sair", command=app_instance.quit, width=120, font=app_instance.font_small_button, fg_color="transparent", border_width=1, border_color=("gray70", "gray30"), hover_color=("gray85", "gray20"))
    exit_button.pack()

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

    ctk.CTkLabel(scrollable_control_panel, text="3. Selecionar Teste Automático (via Thompson):", font=("Arial", 13, "bold")).pack(pady=(15,5), padx=10, anchor="w", fill="x")
    inner_scrollable_test_buttons = ctk.CTkScrollableFrame(scrollable_control_panel, height=120) 
    inner_scrollable_test_buttons.pack(pady=5, padx=10, fill="x")
    for i, test_case in enumerate(TEST_CASES):
        btn = ctk.CTkButton(inner_scrollable_test_buttons, text=f"Carregar: {test_case['name']}",
                            command=lambda tc=test_case: app_instance.load_test_data_for_auto_mode(tc))
        btn.pack(pady=3, fill="x")
    if back_button_ref: back_button_ref.pack(pady=(20,10), padx=10, fill="x")