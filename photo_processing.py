import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QRect
from PIL import Image
from navigation_menu import NavigationMenu

class PhotoProcessingPage(QWidget):
    def __init__(self, db, show_photo_bank_page):
        super().__init__()
        self.db = db
        self.show_photo_bank_page = show_photo_bank_page
        self.current_photo_id = None
        self.original_pixmap = None
        self.bboxes = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.nav_menu = NavigationMenu(self)
        layout.addWidget(self.nav_menu)

        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.photo_label)

        self.scroll_area = QScrollArea()
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.scroll_area.setWidget(self.info_label)
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        self.back_button = QPushButton("Назад")
        button_layout.addWidget(self.back_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.back_button.clicked.connect(self.show_photo_bank_page)

    def load_photo(self, photo_id):
        self.current_photo_id = photo_id
        photo_data = self.db.get_photo(photo_id)
        if photo_data:
            self.original_pixmap = QPixmap(photo_data[1])  # path is at index 1
            self.bboxes = self.parse_bbox_string(photo_data[9])  # bbox_string is at index 9
            self.display_photo(self.original_pixmap)
            self.update_info_label(photo_data)
        else:
            self.info_label.setText("Фото не найдено")
            self.photo_label.clear()

    def parse_bbox_string(self, bbox_string):
        if not bbox_string:
            return []
        bboxes = []
        for bbox in bbox_string.split(";"):
            parts = bbox.split(",")
            if len(parts) >= 6:
                x1, y1, x2, y2 = map(int, parts[:4])
                animal_id, category = parts[4], parts[5]
                bboxes.append((x1, y1, x2, y2, animal_id, category))
        return bboxes

    def display_photo(self, pixmap):
        scaled_width = int(self.width() * 0.8)
        scaled_height = int(self.height() * 0.6)
        scaled_pixmap = pixmap.scaled(scaled_width, scaled_height,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        if self.bboxes:
            drawing_pixmap = scaled_pixmap.copy()
            painter = QPainter(drawing_pixmap)
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            scale_x = scaled_pixmap.width() / pixmap.width()
            scale_y = scaled_pixmap.height() / pixmap.height()
            
            for bbox in self.bboxes:
                x1, y1, x2, y2, animal_id, category = bbox
                x1, y1, x2, y2 = map(int, [x1 * scale_x, y1 * scale_y, x2 * scale_x, y2 * scale_y])
                painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                painter.drawText(x1, y1 - 5, f"{category} {animal_id}")
            
            painter.end()
            self.photo_label.setPixmap(drawing_pixmap)
        else:
            self.photo_label.setPixmap(scaled_pixmap)

    def update_info_label(self, photo_data):
        if photo_data:
            id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp, bbox_string = photo_data
            
            info_text = f"<b>ID фото:</b> {id}<br>"
            info_text += f"<b>Путь:</b> {path}<br>"
            info_text += f"<b>Папка:</b> {folder}<br>"
            info_text += f"<b>Дата загрузки:</b> {upload_date}<br>"
            info_text += f"<b>Обработано:</b> {'Да' if processed else 'Нет'}<br>"
            info_text += f"<b>ID сцены:</b> {scene_id}<br>"
            info_text += f"<b>Количество животных:</b> {animal_count}<br>"
            info_text += f"<b>Уникальных животных:</b> {unique_animal_count}<br>"
            info_text += f"<b>Временная метка:</b> {timestamp}<br>"
            info_text += f"<b>Bounding Boxes:</b><br>"
            
            if bbox_string:
                for bbox in bbox_string.split(";"):
                    x1, y1, x2, y2, animal_id, category = bbox.split(",")
                    info_text += f"  {category} {animal_id}: ({x1}, {y1}, {x2}, {y2})<br>"
            else:
                info_text += "  Нет данных о bounding boxes<br>"

            self.info_label.setText(info_text)
        else:
            self.info_label.setText("Фото не найдено")
            self.photo_label.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.display_photo(self.original_pixmap)