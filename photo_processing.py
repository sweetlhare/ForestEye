import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
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

        self.info_label = QLabel()
        layout.addWidget(self.info_label)

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
            self.original_pixmap = QPixmap(photo_data[1])  # Assuming path is at index 1
            self.bboxes = self.db.get_bounding_boxes(photo_id)
            self.display_photo(self.original_pixmap)
            self.update_info_label(photo_data)

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
                x1 = int(x1 * scale_x)
                y1 = int(y1 * scale_y)
                x2 = int(x2 * scale_x)
                y2 = int(y2 * scale_y)
                painter.drawRect(QRect(x1, y1, x2 - x1, y2 - y1))
                painter.drawText(x1, y1 - 5, category)
            
            painter.end()
            self.photo_label.setPixmap(drawing_pixmap)
        else:
            self.photo_label.setPixmap(scaled_pixmap)

    def update_info_label(self, photo_data):
        if photo_data:
            photo_id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp = photo_data
            info_text = f"ID фото: {photo_id}\n"
            info_text += f"Путь: {path}\n"
            info_text += f"Папка: {folder}\n"
            info_text += f"Дата загрузки: {upload_date}\n"
            info_text += f"Обработано: {'Да' if processed else 'Нет'}\n"
            info_text += f"ID сцены: {scene_id}\n"
            info_text += f"Количество животных: {animal_count}\n"
            info_text += f"Уникальных животных: {unique_animal_count}\n"
            info_text += f"Временная метка: {timestamp}"
            self.info_label.setText(info_text)

            # Удалите эти две строки, так как фото уже отображается в методе display_photo
            # pixmap = QPixmap(path)
            # self.photo_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.info_label.setText("Фото не найдено")
            self.photo_label.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.display_photo(self.original_pixmap)