import customtkinter as ctk

def update_text_content(textbox_widget, content):
    if textbox_widget:
        textbox_widget.configure(state="normal")
        textbox_widget.delete("1.0", "end")
        textbox_widget.insert("1.0", content)
        textbox_widget.configure(state="disabled")

def update_display_tab(widgets, tab_key_name, content_str):
    if not widgets or "textboxes_map" not in widgets: return 
    textbox = widgets.get("textboxes_map", {}).get(tab_key_name)
    if textbox:
        update_text_content(textbox, content_str)

def clear_dfa_image(widgets):
    dfa_img_label_current = widgets.get("dfa_image_label")
    if dfa_img_label_current:
        dfa_img_label_current.configure(image=None, text="Nenhum AFD desenhado ainda.")