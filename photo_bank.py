from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QFileDialog, QProgressDialog,
                             QComboBox, QLabel, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os
from PIL import Image
from PIL.ExifTags import TAGS
from navigation_menu import NavigationMenu
from ultralytics import YOLO
from datetime import datetime, timedelta
import uuid

class PhotoBankPage(QWidget):
    def __init__(self, db, show_processing_page):
        super().__init__()
        self.db = db
        self.show_processing_page = show_processing_page
        self.model = YOLO('yolov8n.pt')
        self.items_per_page = 15
        self.init_ui()
        self.animal_ids = {}
        self.current_page = 1
        self.total_pages = 1
        self.current_folder = None

    def init_ui(self):
        layout = QVBoxLayout()

        self.nav_menu = NavigationMenu(self)
        layout.addWidget(self.nav_menu)

        # Add folder selection combo box
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Выберите папку:")
        self.folder_combo = QComboBox()
        self.folder_combo.currentTextChanged.connect(self.on_folder_changed)
        folder_layout.addWidget(folder_label)
        folder_layout.addWidget(self.folder_combo)
        layout.addLayout(folder_layout)

        self.photo_table = QTableWidget()
        self.photo_table.setColumnCount(7)
        self.photo_table.setHorizontalHeaderLabels(["Фото", "Дата загрузки", "Папка", "Обработано", "Кол-во животных", "Уникальных животных", "ID сцены"])
        self.photo_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.photo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.photo_table)

        # Add pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Предыдущая")
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button = QPushButton("Следующая")
        self.next_button.clicked.connect(self.next_page)
        self.page_label = QLabel()
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.valueChanged.connect(self.on_page_changed)
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.page_spin)
        pagination_layout.addWidget(self.next_button)
        layout.addLayout(pagination_layout)

        button_layout = QHBoxLayout()
        self.upload_folder_button = QPushButton("Загрузить папку")
        button_layout.addWidget(self.upload_folder_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.upload_folder_button.clicked.connect(self.upload_folder)
        self.photo_table.cellDoubleClicked.connect(self.open_photo)

        self.load_folders()
        self.load_photos()

        self.current_scene_id = None
        self.last_photo_time = None

    def load_folders(self):
        folders = self.db.get_unique_folders()
        self.folder_combo.clear()
        self.folder_combo.addItem("Все папки")
        self.folder_combo.addItems(folders)

    def on_folder_changed(self, folder):
        self.current_folder = None if folder == "Все папки" else folder
        self.current_page = 1
        self.load_photos()

    def load_photos(self):
        photos = self.db.get_photos(folder=self.current_folder)
        self.total_pages = (len(photos) - 1) // self.items_per_page + 1
        self.page_spin.setMaximum(self.total_pages)
        self.update_pagination_controls()

        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_photos = photos[start_idx:end_idx]

        self.photo_table.setRowCount(len(page_photos))
        for row, photo in enumerate(page_photos):
            photo_id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp = photo
            
            pixmap = QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            thumbnail_item = QTableWidgetItem()
            thumbnail_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.photo_table.setItem(row, 0, thumbnail_item)
            
            # Используем timestamp вместо upload_date
            self.photo_table.setItem(row, 1, QTableWidgetItem(timestamp if timestamp else "Нет данных"))
            self.photo_table.setItem(row, 2, QTableWidgetItem(folder))
            self.photo_table.setItem(row, 3, QTableWidgetItem("Да" if processed else "Нет"))
            self.photo_table.setItem(row, 4, QTableWidgetItem(str(animal_count) if animal_count is not None else ""))
            self.photo_table.setItem(row, 5, QTableWidgetItem(str(unique_animal_count) if unique_animal_count is not None else ""))
            self.photo_table.setItem(row, 6, QTableWidgetItem(str(scene_id) if scene_id is not None else ""))

    def update_pagination_controls(self):
        self.page_label.setText(f"Страница {self.current_page} из {self.total_pages}")
        self.page_spin.setValue(self.current_page)
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < self.total_pages)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_photos()

    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_photos()

    def on_page_changed(self, page):
        if page != self.current_page:
            self.current_page = page
            self.load_photos()

    def upload_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Выберите папку с фотографиями")
        if folder_name:
            image_files = [f for f in os.listdir(folder_name) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            image_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_name, x)))  # Сортировка по времени изменения
            
            progress = QProgressDialog("Загрузка и обработка фотографий...", "Отмена", 0, len(image_files), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс загрузки и обработки")
            
            self.current_scene_id = None  # Сбрасываем ID сцены перед обработкой новой папки
            self.last_photo_time = None
            
            for i, image_file in enumerate(image_files):
                if progress.wasCanceled():
                    break
                
                file_path = os.path.join(folder_name, image_file)
                self.process_single_photo(file_path)
                progress.setValue(i + 1)
            
            progress.setValue(len(image_files))
            self.load_folders()
            self.load_photos()

    def process_single_photo(self, file_path):
        timestamp = self.get_photo_timestamp(file_path)
        photo_id = self.db.add_photo(file_path, timestamp)
        
        if self.current_scene_id is None or self.is_new_scene(timestamp):
            self.current_scene_id = self.db.create_new_scene()
            self.animal_ids = {}
        
        results = self.model(file_path)
        
        bounding_boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            category = results[0].names[int(box.cls)]
            animal_id = self.get_or_create_animal_id((int(x1), int(y1), int(x2), int(y2)))
            bounding_boxes.append((int(x1), int(y1), int(x2), int(y2), animal_id, category))
        
        animal_count = len(bounding_boxes)
        unique_animal_count = len(set(animal_id for _, _, _, _, animal_id, _ in bounding_boxes))
        
        self.db.update_photo_processing(photo_id, self.current_scene_id, animal_count, unique_animal_count, bounding_boxes, timestamp)
        
        self.last_photo_time = timestamp
    
    def get_or_create_animal_id(self, bbox):
        # This is a simplistic approach. In a real scenario, you'd use more sophisticated
        # tracking or feature matching to determine if it's the same animal.
        for existing_bbox, animal_id in self.animal_ids.items():
            if self.is_same_animal(existing_bbox, bbox):
                return animal_id
        
        new_id = str(uuid.uuid4())
        self.animal_ids[bbox] = new_id
        return new_id
    
    def is_same_animal(self, bbox1, bbox2):
        # This is a very basic comparison. In reality, you'd use more advanced
        # techniques like feature matching or tracking algorithms.
        x1, y1, x2, y2 = bbox1
        x3, y3, x4, y4 = bbox2
        center1 = ((x1 + x2) / 2, (y1 + y2) / 2)
        center2 = ((x3 + x4) / 2, (y3 + y4) / 2)
        distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
        return distance < 50  # Arbitrary threshold, adjust as needed

    def get_photo_timestamp(self, file_path):
        try:
            with Image.open(file_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'DateTimeOriginal':
                            return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    
                    for tag_id, value in exif.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ['DateTime', 'DateTimeDigitized']:
                            return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        except Exception as e:
            print(f"Ошибка при чтении EXIF данных: {e}")
        
        return datetime.fromtimestamp(os.path.getmtime(file_path))

    def is_new_scene(self, current_time):
        if self.last_photo_time is None:
            return True
        time_difference = current_time - self.last_photo_time
        return time_difference > timedelta(minutes=30)  # Adjust this threshold as needed

    def open_photo(self, row, column):
        start_idx = (self.current_page - 1) * self.items_per_page
        photo_id = self.db.get_photos(folder=self.current_folder)[start_idx + row][0]
        self.show_processing_page(photo_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_folders()
        self.load_photos()