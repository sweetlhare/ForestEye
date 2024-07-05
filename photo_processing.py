import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt6.QtCore import Qt, QRect
import numpy as np
from PIL import Image, ImageQt
from navigation_menu import NavigationMenu

class PhotoProcessingPage(QWidget):
    def __init__(self, db, show_photo_bank_page):
        super().__init__()
        self.db = db
        self.show_photo_bank_page = show_photo_bank_page
        self.current_photo_id = None
        self.original_pixmap = None
        self.processed_mask = None
        self.bbox = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.nav_menu = NavigationMenu(self)
        layout.addWidget(self.nav_menu)

        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.photo_label)

        button_layout = QHBoxLayout()
        self.process_button = QPushButton("Обработать")
        self.back_button = QPushButton("Назад")
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.back_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.process_button.clicked.connect(self.process_photo)
        self.back_button.clicked.connect(self.show_photo_bank_page)

    def load_photo(self, photo_id):
        self.current_photo_id = photo_id
        photo_data = self.db.get_photo(photo_id)
        if photo_data:
            self.original_pixmap = QPixmap(photo_data[1])
            self.display_photo(self.original_pixmap)
            
            if photo_data[5]:  # если фото уже обработано
                self.bbox = photo_data[6:10]
                self.load_mask()
                self.display_processed_photo()
            else:
                self.bbox = None
                self.processed_mask = None

    def display_photo(self, pixmap):
        scaled_width = int(self.width() * 0.8)
        scaled_height = int(self.height() * 0.8)
        
        scaled_pixmap = pixmap.scaled(scaled_width, scaled_height, 
                                      Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
        self.photo_label.setPixmap(scaled_pixmap)

    def process_photo(self):
        if self.current_photo_id is None:
            return

        # Симуляция обработки фотографии нейросетью
        self.simulate_neural_network_processing()

        # Сохранение результатов
        self.save_processing_results()

        # Отображение результатов
        self.display_processed_photo()

    def simulate_neural_network_processing(self):
        width = self.original_pixmap.width()
        height = self.original_pixmap.height()
        
        # Создаем случайную маску сегментации
        self.processed_mask = np.random.randint(0, 2, (height, width), dtype=np.uint8)

        # Создаем случайный bounding box
        x1 = np.random.randint(0, width // 2)
        y1 = np.random.randint(0, height // 2)
        x2 = np.random.randint(width // 2, width)
        y2 = np.random.randint(height // 2, height)
        self.bbox = (x1, y1, x2, y2)

    def save_processing_results(self):
        # Сохранение маски
        if not os.path.exists('masks'):
            os.makedirs('masks')
        mask_path = f'masks/mask_{self.current_photo_id}.png'
        Image.fromarray(self.processed_mask * 255).save(mask_path)

        # Сохранение результатов в БД
        self.db.update_photo_processing(self.current_photo_id, *self.bbox)

    def load_mask(self):
        mask_path = f'masks/mask_{self.current_photo_id}.png'
        if os.path.exists(mask_path):
            self.processed_mask = np.array(Image.open(mask_path)) // 255

    def display_processed_photo(self):
        if self.processed_mask is None or self.bbox is None:
            return

        image = self.original_pixmap.toImage()
        painter = QPainter(image)

        # Наложение маски сегментации
        mask_image = Image.fromarray(self.processed_mask * 255).convert("RGBA")
        mask_qt_image = ImageQt.ImageQt(mask_image)
        painter.setOpacity(0.5)
        painter.drawImage(0, 0, mask_qt_image)

        # Рисование bounding box
        painter.setOpacity(1.0)
        painter.setPen(QPen(QColor(255, 0, 0), 100))
        painter.drawRect(QRect(*self.bbox))

        painter.end()

        processed_pixmap = QPixmap.fromImage(image)
        self.display_photo(processed_pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap:
            self.display_photo(self.original_pixmap)