from kivy.app import App
from viewer_ui import PDFViewerUI
from pdf_renderer import PDFObject
from page_navigator import PageNavigator

class SheetMusicApp(App):
    def build(self):
        self.pdf_renderer = PDFObject()
        self.page_navigator = PageNavigator()
        self.viewer_ui = PDFViewerUI(self.pdf_renderer, self.page_navigator)
        return self.viewer_ui

    def on_stop(self):
        self.viewer_ui.save_all_settings()

if __name__ == '__main__':
    SheetMusicApp().run()
