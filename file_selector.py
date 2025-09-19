from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
import os

def open_pdf_filechooser(on_file_selected_callback):
    content = FileChooserListView(filters=["*.pdf"], rootpath=os.getcwd())
    popup = Popup(title="Selecteer PDF-bestand", content=content, size_hint=(0.9, 0.9))

    def file_selected(inst, selection, touch):
        if selection:
            popup.dismiss()
            on_file_selected_callback(selection[0])

    content.bind(on_submit=file_selected)
    popup.open()
