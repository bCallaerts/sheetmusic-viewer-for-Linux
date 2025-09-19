from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty

class AnnotationWidget(Widget):
    drawing = BooleanProperty(False)
    line_color = ListProperty([1, 0, 0, 1])
    lines = ListProperty([])  # Altijd relatieve coordinaten opslaan

    def _rel_to_abs(self, points):
        # Zet relatieve (tussen 0 en 1) om naar actuele widget-pixels
        w, h = self.width, self.height
        abs_points = []
        for i in range(0, len(points), 2):
            x = points[i] * w
            y = points[i + 1] * h
            abs_points.extend([x, y])
        return abs_points

    def _abs_to_rel(self, points):
        w, h = self.width, self.height
        rel_points = []
        for i in range(0, len(points), 2):
            x = points[i] / w if w else 0
            y = points[i + 1] / h if h else 0
            rel_points.extend([x, y])
        return rel_points

    def on_touch_down(self, touch):
        if not self.drawing or not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        local_pos = self.to_local(*touch.pos)
        with self.canvas:
            Color(*self.line_color)
            touch.ud['line'] = Line(points=[local_pos[0], local_pos[1]], width=2)
        rel_points = self._abs_to_rel(touch.ud['line'].points)
        self.lines.append({'points': rel_points, 'color': self.line_color[:]})
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        local_pos = self.to_local(*touch.pos)
        touch.ud['line'].points += [local_pos[0], local_pos[1]]
        rel_points = self._abs_to_rel(touch.ud['line'].points)
        self.lines[-1]['points'] = rel_points
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        return True

    def clear(self):
        self.canvas.clear()
        self.lines.clear()

    def load_lines(self, lines):
        self.canvas.clear()
        self.lines = []
        if len(lines) == 0:
            return
        with self.canvas:
            for line in lines:
            
                Color(*line['color'])
                abs_points = self._rel_to_abs(line['points'])
                Line(points=abs_points, width=2)
            self.lines.append({'points': line['points'], 'color': line['color']})
