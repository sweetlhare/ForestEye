import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea, QSizePolicy
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
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)  # Отступы от края окна
        main_layout.setSpacing(15)  # Увеличенное расстояние между элементами

        self.nav_menu = NavigationMenu(self)
        main_layout.addWidget(self.nav_menu)

        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.photo_label)

        self.scroll_area = QScrollArea()
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        self.scroll_area.setWidget(self.info_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        main_layout.addWidget(self.scroll_area)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # Отступ сверху
        self.back_button = QPushButton("Назад")
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #525252;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.back_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

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
            font.setPointSize(12)  # Увеличенный размер шрифта
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
            
            info_text = f"<h2>Информация о фото</h2>"
            info_text += f"<p><b>ID фото:</b> {id}</p>"
            info_text += f"<p><b>Путь:</b> {path}</p>"
            info_text += f"<p><b>Папка:</b> {folder}</p>"
            info_text += f"<p><b>Дата загрузки:</b> {upload_date}</p>"
            info_text += f"<p><b>Обработано:</b> {'Да' if processed else 'Нет'}</p>"
            info_text += f"<p><b>ID сцены:</b> {scene_id}</p>"
            info_text += f"<p><b>Количество животных:</b> {animal_count}</p>"
            info_text += f"<p><b>Уникальных животных:</b> {unique_animal_count}</p>"
            info_text += f"<p><b>Временная метка:</b> {timestamp}</p>"
            info_text += f"<h3>Bounding Boxes:</h3>"
            
            if bbox_string:
                info_text += "<ul>"
                for bbox in bbox_string.split(";"):
                    x1, y1, x2, y2, animal_id, category = bbox.split(",")
                    info_text += f"<li>{category} {animal_id}: ({x1}, {y1}, {x2}, {y2})</li>"
                info_text += "</ul>"
            else:
                info_text += "<p>Нет данных о bounding boxes</p>"

            self.info_label.setText(info_text)
        else:
            self.info_label.setText("<h2>Фото не найдено</h2>")
            self.photo_label.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.display_photo(self.original_pixmap)