from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorPicker
from kivy.clock import Clock
from kivy.app import App
from page_settings import PageSettings
from annotation_widget import AnnotationWidget
from annotation_storage import AnnotationStorage
from file_selector import open_pdf_filechooser

DEFAULT_ZOOM = 1.0
DEFAULT_ROTATION = 0

class PDFViewerUI(FloatLayout):
    

    def __init__(self, pdf_renderer, page_navigator, **kwargs):
        super().__init__(**kwargs)
        self.pdf_renderer = pdf_renderer
        self.page_navigator = page_navigator
        # self.page_settings = PageSettings()
        self.annotation_storage = AnnotationStorage()
        self.filepath = None
        self.color_popup = None
        self.buttons_visible = BooleanProperty(True)
        self.pencil_mode = BooleanProperty(False)
        self.draw_color = ListProperty([1, 0, 0, 1])

        self.scatter = Scatter(size_hint=(None, None), do_rotation=False,
                               do_translation=False, do_scale=False)
        self.img_widget = Image()
        self.annotation_widget = AnnotationWidget()
        # self.annotation_widget.scatter = self.scatter
        self.scatter.add_widget(self.img_widget)
        self.scatter.add_widget(self.annotation_widget)
        self.add_widget(self.scatter)

        self.button_bar_container = GridLayout(cols=4, size_hint=(2, None), height=100, pos_hint={'x': 0, 'y': 0})
        self.add_widget(self.button_bar_container)

        self.create_buttons()
        self.update_button_bar_visibility()
        self.page_navigator.bind(current_page=self.on_page_change)
        self.bind(size=lambda *a: self.rescale_to_window())
        Clock.schedule_once(lambda dt: self.rescale_to_window(), 0.1)

    def update_button_bar_visibility(self):
        self.button_bar_container.opacity = 1 if self.buttons_visible else 0
        self.button_bar_container.disabled = not self.buttons_visible

    def toggle_button_bar(self):
        self.buttons_visible = not self.buttons_visible
        self.update_button_bar_visibility()

    def create_buttons(self):
        top_buttons = [
            ("Open PDF", self.open_pdf),
            ("Zoom +", lambda _: self.on_zoom_in()),
            ("Zoom –", lambda _: self.on_zoom_out()),
            ("Draai 90°", lambda _: self.on_rotate()),
        ]
        bottom_buttons = [
            ("Potlood", self.toggle_pencil),
            ("Kleur", self.open_color_picker),
            ("Clear Annotations", self.clear_annotations),
            ("Opslaan & Afsluiten", lambda _: self.save_and_quit()),
        ]

        self.button_bar_container.clear_widgets()
        for label, cb in top_buttons:
            btn = Button(text=label, size_hint_x=None, width=200)
            btn.bind(on_release=cb)
            self.button_bar_container.add_widget(btn)

        for label, cb in bottom_buttons:
            if label == "Potlood":
                btn = ToggleButton(text=label, size_hint_x=None,
                                   width=200, group='tools')
                btn.bind(on_release=cb)
            else:
                btn = Button(text=label, size_hint_x=None, width=200)
                btn.bind(on_release=cb)
            self.button_bar_container.add_widget(btn)

    def toggle_pencil(self, btn):
        self.pencil_mode = btn.state == 'down'
        self.annotation_widget.drawing = self.pencil_mode

        if not self.pencil_mode:
            self.save_annotations_for_page()

    def open_pdf(self, instance):
        open_pdf_filechooser(self.load_pdf)

    def load_pdf(self, filepath):
        self.filepath = filepath
        self.pdf_renderer.open_pdf(filepath)
        self.page_navigator.set_total_pages(self.pdf_renderer.get_page_count())
        Clock.schedule_once(lambda dt: self.rescale_to_window(), 0.1)

    def rescale_to_window(self, *args):
        w, h = self.size
        self.scatter.size = (w - 40, h - 120)
        self.scatter.pos = (20, 100)
        if not self.filepath or not self.pdf_renderer.doc:
            return
        zoom = self.fit_page_to_widget(self.page_navigator.current_page)
        # self.current_zoom = zoom
        # self.page_settings.set(self.filepath, self.page_navigator.current_page,
        #                        self.current_zoom, self.current_rotation)
        self.show_page(self.page_navigator.current_page)
        # self.load_annotations_for_page(self.page_navigator.current_page)  # Belangrijk!

    def fit_page_to_widget(self, page_number):
        if not self.filepath or not self.pdf_renderer.doc:
            return 1.0
        page = self.pdf_renderer.doc.load_page(page_number)
        pix = page.get_pixmap()
        page_w, page_h = pix.width, pix.height
        widget_w, widget_h = self.scatter.size
        if widget_w == 0 or widget_h == 0:
            return 1.0
        scale_w = widget_w / page_w
        scale_h = widget_h / page_h
        scale = min(scale_w, scale_h)
        scale = min(max(scale, 0.5), 3.0)
        return scale

    def show_page(self, page_number, *args):
        result = self.pdf_renderer.render_page(page_number)
                                            #    zoom=self.current_zoom,
                                            #    rotation=self.current_rotation)
        if result:
            texture, size = result
            self.img_widget.texture = texture
            self.img_widget.size = size
            self.annotation_widget.page_size = size
            self.annotation_widget.size = size
            self.load_annotations_for_page(page_number)

    def on_page_change(self, instance, value):
        self.show_page(value)

    def on_zoom_in(self):
        self.pdf_renderer.adjust_zoom(self.page_navigator.current_page, 1.1)
        self.show_page(self.page_navigator.current_page)

    def on_zoom_out(self):
        self.pdf_renderer.adjust_zoom(self.page_navigator.current_page, 1 / 1.1)
        self.show_page(self.page_navigator.current_page)

    def on_rotate(self):
        self.pdf_renderer.adjust_rotation(self.page_navigator.current_page, 90)
        self.show_page(self.page_navigator.current_page)
        # self.load_annotations_for_page(self.page_navigator.current_page)  # Herlaad annotaties

    def save_all_settings(self):
        self.pdf_renderer.save()
        # self.save_annotations_for_page()
        # self.page_settings.save()

    def save_and_quit(self):
        self.save_all_settings()
        App.get_running_app().stop()

    def save_annotations_for_page(self):
        if not self.filepath:
            return
        
        self.pdf_renderer.set_value(self.page_navigator.current_page,
                                    'annotations',
                                    self.annotation_widget.lines)
        
        self.pdf_renderer.save()
        # page = self.page_navigator.current_page
        # self.annotation_storage.set(self.filepath, page,
        #                             self.annotation_widget.lines)
        # self.annotation_storage.save()

    def load_annotations_for_page(self, page_number):
        if not self.filepath:
            return
        annotations = self.pdf_renderer.get_annotations(page_number)
        self.annotation_widget.load_lines(annotations)

    def open_color_picker(self, instance):
        if self.color_popup:
            return
        color_picker = ColorPicker()
        btn_confirm = Button(text="Bevestig")
        container = BoxLayout(orientation='vertical')
        container.add_widget(color_picker)
        container.add_widget(btn_confirm)
        self.color_popup = Popup(title="Kies kleur", content=container,
                                 size_hint=(0.8, 0.8))
        btn_confirm.bind(on_release=self.confirm_color)
        color_picker.bind(color=self.on_color_change)
        color_picker.color = self.draw_color
        self.color_popup.open()

    def on_color_change(self, instance, value):
        self.draw_color = value
        self.annotation_widget.line_color = value

    def confirm_color(self, instance):
        if self.color_popup:
            self.color_popup.dismiss()
            self.color_popup = None

    def clear_annotations(self, instance):
        self.annotation_widget.clear()
        if self.filepath:
            self.save_annotations_for_page()

    def on_touch_down(self, touch):
        # Navigatie en togglen button bar (enkel als niet in tekenmodus)
        if self.scatter.collide_point(*touch.pos) and not self.annotation_widget.drawing:
            local_x, local_y = self.scatter.to_widget(*touch.pos, relative=True)
            if self.img_widget.texture:
                img_x = local_x - self.img_widget.x
                img_y = local_y - self.img_widget.y
                if not (0 <= img_x <= self.img_widget.width and 0 <= img_y <= self.img_widget.height):
                    return super().on_touch_down(touch)
                x_rel = img_x / self.img_widget.width
                y_rel = img_y / self.img_widget.height
                center_x0, center_x1 = 0.425, 0.575
                center_y0, center_y1 = 0.425, 0.575
                if center_x0 < x_rel < center_x1 and center_y0 < y_rel < center_y1:
                    self.toggle_button_bar()
                    return True
                elif x_rel < 0.1:
                    page = self.page_navigator.prev_page()
                    self.show_page(page)
                    return True
                elif x_rel > 0.9:
                    page = self.page_navigator.next_page()
                    self.show_page(page)
                    return True
        return super().on_touch_down(touch)
