import fitz  # PyMuPDF
import os
import json
import io
from kivy.core.image import Image as CoreImage
import math

PAGE_SETUP_FOLDER = "page_setups"
if not os.path.exists(PAGE_SETUP_FOLDER):
    os.makedirs(PAGE_SETUP_FOLDER)

class PDFObject:
    def __init__(self):
        self.doc = None
        self.rel_filepath = None

    def open_pdf(self, filepath):
        self.doc = fitz.open(filepath)
        self.rel_filepath = os.path.split(filepath)[-1]
        print("Opened PDF:", filepath, self.rel_filepath)
        if os.path.exists(os.path.join(PAGE_SETUP_FOLDER, self.rel_filepath.replace(".pdf", ".json"))):
            print("Loading page setups from", os.path.join(PAGE_SETUP_FOLDER, self.rel_filepath.replace(".pdf", "json")))
            with open(os.path.join(PAGE_SETUP_FOLDER, self.rel_filepath.replace(".pdf", ".json")), 'r') as f:
                self.page_setups = json.load(f)
        else:
            print("No existing page setups found.")
            self.page_setups = {}

    def get_page_count(self):
        return self.doc.page_count if self.doc else 0

    def render_page(self, page_number):
        if not self.doc or not (0 <= page_number < self.doc.page_count):
            return None, None
        if str(page_number) not in self.page_setups:
            self.page_setups[str(page_number)] = {'zoom': 1.0, 'rotation': 0, 'annotations': []}
        
        zoom = self.get_value(page_number, 'zoom', 1.0)
        rotation = self.get_value(page_number, 'rotation', 0)
        page = self.doc.load_page(page_number)
        
        mat = fitz.Matrix(zoom, zoom).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat)

        data = io.BytesIO(pix.tobytes("png"))
        texture = CoreImage(data, ext='png').texture

        return texture, (texture.width, texture.height)
    
    def set_value(self, page_number, key, value):
        page_number = str(page_number)
        if page_number in self.page_setups:
            self.page_setups[page_number][key] = value
    
    def set_annotations(self, page_number, annotations):
        page_number = str(page_number)
        if self.get_value(page_number, 'rotation', 0) != 0:
            # Rotate annotations to match original file orientation
            rotated_annotations = []
            rotation = self.get_value(page_number, 'rotation', 0)
            for ann in annotations:
                if 'points' in ann:
                    rotated_points = []
                    for i in range(0, len(ann['points']), 2):
                        x, y = ann['points'][i]-0.5, ann['points'][i + 1]-0.5  # Center around (0,0)
                        # Rotate point
                        angle = math.radians(rotation)
                        # Rotate around (0,0)
                        x_rot = x * math.cos(angle) - y * math.sin(angle) + 0.5
                        y_rot = x * math.sin(angle) + y * math.cos(angle) + 0.5
                        rotated_points.extend([x_rot, y_rot])
                    ann_copy = ann.copy()
                    ann_copy['points'] = rotated_points
                    rotated_annotations.append(ann_copy)
                else:
                    rotated_annotations.append(ann)
            annotations = rotated_annotations
        if page_number in self.page_setups:
            self.page_setups[page_number]['annotations'] = annotations
    
    def get_value(self, page_number, key, default=None):
        return self.page_setups.get(str(page_number), {}).get(key, default)
    
    def get_annotations(self, page_number):
        anns = self.page_setups.get(str(page_number), {}).get('annotations', [])
        rotation = self.get_value(page_number, 'rotation', 0)
        if rotation == 0:
            return anns
        # Rotate annotations back to match current rotation
        anns_rotated = []
        for ann in anns:
            if 'points' in ann:
                rotated_points = []
                for i in range(0, len(ann['points']), 2):
                    x, y = ann['points'][i]-0.5, ann['points'][i + 1]-0.5  # Center around (0,0)
                    # Rotate point
                    angle = -math.radians(rotation)
                    # Rotate around (0,0)
                    x_rot = x * math.cos(angle) - y * math.sin(angle) + 0.5
                    y_rot = x * math.sin(angle) + y * math.cos(angle) + 0.5
                    rotated_points.extend([x_rot, y_rot])
                ann_copy = ann.copy()
                ann_copy['points'] = rotated_points
                anns_rotated.append(ann_copy)
            else:
                anns_rotated.append(ann)
        return anns_rotated
    
    def adjust_zoom(self, page_number, factor):
        if not self.doc:
            return
        
        current_zoom = self.get_value(page_number, 'zoom', 1.0)
        new_zoom = max(0.1, min(10, current_zoom * factor))
        self.set_value(page_number, 'zoom', new_zoom)
    
    def adjust_rotation(self, page_number, delta):
        if not self.doc:
            return
        current_rotation = self.get_value(page_number, 'rotation', 0)
        new_rotation = (current_rotation + delta) % 360
        self.set_value(page_number, 'rotation', new_rotation)
    
    def save(self):
        if self.rel_filepath:
            with open(os.path.join(PAGE_SETUP_FOLDER, self.rel_filepath.replace(".pdf", ".json")), 'w') as f:
                json.dump(self.page_setups, f)
