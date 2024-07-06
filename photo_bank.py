import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QFileDialog, QProgressDialog,
                             QComboBox, QLabel, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PIL import Image
from PIL.ExifTags import TAGS
from navigation_menu import NavigationMenu
import cv2
import numpy as np
import onnxruntime

class PhotoBankPage(QWidget):
    def __init__(self, db, show_processing_page):
        super().__init__()
        self.db = db
        self.show_processing_page = show_processing_page
        self.items_per_page = 15
        self.init_ui()
        self.current_page = 1
        self.total_pages = 1
        self.current_folder = None
        self.onnx_session = onnxruntime.InferenceSession('last-2.onnx', providers=['CPUExecutionProvider'])
        self.labels = self.load_labels('labels.txt')

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

    def load_labels(self, labels_path):
        with open(labels_path, 'r') as f:
            return [line.strip() for line in f.readlines()]
        
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
            image_files.sort(key=lambda x: self.get_photo_timestamp(os.path.join(folder_name, x)))
            
            progress = QProgressDialog("Загрузка и обработка фотографий...", "Отмена", 0, len(image_files), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс загрузки и обработки")
            
            scenes = []
            current_scene = None
            last_photo_time = None
            
            for i, image_file in enumerate(image_files):
                if progress.wasCanceled():
                    break
                
                file_path = os.path.join(folder_name, image_file)
                timestamp = self.get_photo_timestamp(file_path)
                
                if current_scene is None or self.is_new_scene(timestamp, last_photo_time):
                    if current_scene is not None:
                        scenes.append(current_scene)
                    current_scene = {
                        'photos': [],
                        'animal_ids': set(),
                        'max_unique_animals': 0,
                        'bboxes': []  # Добавляем список для хранения всех bounding boxes сцены
                    }
                
                results = self.process_image_with_yolo(file_path)
                
                bbox_strings = []
                current_photo_animal_ids = set()
                for detection in results:
                    x1, y1, x2, y2 = map(int, detection['bbox'])
                    category = detection['class']
                    animal_id = self.get_or_create_animal_id(current_scene['bboxes'], current_scene['animal_ids'], (x1, y1, x2, y2))
                    bbox_strings.append(f"{x1},{y1},{x2},{y2},{animal_id},{category}")
                    current_photo_animal_ids.add(animal_id)
                    current_scene['bboxes'].append((x1, y1, x2, y2))
                
                bbox_string = ";".join(bbox_strings)
                
                animal_count = len(bbox_strings)
                unique_animal_count = len(current_photo_animal_ids)
                current_scene['max_unique_animals'] = max(current_scene['max_unique_animals'], unique_animal_count)
                
                current_scene['photos'].append({
                    'path': file_path,
                    'timestamp': timestamp,
                    'animal_count': animal_count,
                    'unique_animal_count': unique_animal_count,
                    'bbox_string': bbox_string
                })
                
                last_photo_time = timestamp
                progress.setValue(i + 1)
            
            if current_scene is not None:
                scenes.append(current_scene)
            
            progress.setLabelText("Сохранение данных в базу...")
            progress.setRange(0, len(scenes))
            progress.setValue(0)

            unique_animal_counts = []
            for i, scene in enumerate(scenes):
                unique_animal_count_ = 0
                for photo in scene['photos']:
                    unique_animal_count_ = max(unique_animal_count_, photo['unique_animal_count'])
                unique_animal_counts.append(unique_animal_count_)

            for i, scene in enumerate(scenes):
                scene_id = self.db.create_new_scene()
                for photo in scene['photos']:
                    photo_id = self.db.add_photo(photo['path'], photo['timestamp'])
                    self.db.update_photo_processing(
                        photo_id, 
                        scene_id, 
                        photo['animal_count'], 
                        unique_animal_counts[i], 
                        photo['bbox_string'], 
                        photo['timestamp']
                    )
                self.db.update_scene_unique_count(scene_id, unique_animal_counts[i])
                progress.setValue(i + 1)
            
            progress.setValue(len(scenes))
            self.load_folders()
            self.load_photos()

    def process_image_with_yolo(self, image_path):
        image = cv2.imread(image_path)
        original_height, original_width = image.shape[:2]
        input_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_image = cv2.resize(input_image, (1024, 1024))
        input_image = input_image.astype(np.float32) / 255.0
        input_image = np.transpose(input_image, (2, 0, 1))
        input_image = np.expand_dims(input_image, axis=0)
        
        input_name = self.onnx_session.get_inputs()[0].name
        output_name = self.onnx_session.get_outputs()[0].name
        
        outputs = self.onnx_session.run([output_name], {input_name: input_image})
        
        detections = outputs[0][0]
        
        confidence_threshold = 0.5
        filtered_detections = detections[detections[:, 4] > confidence_threshold]
        
        results = []
        for detection in filtered_detections:
            class_id = int(detection[5])
            confidence = detection[4]
            bbox = detection[:4]
            
            # Преобразование координат bbox обратно к оригинальному размеру изображения
            x1, y1, x2, y2 = bbox
            x1 = int(x1 * original_width / 1024)
            y1 = int(y1 * original_height / 1024)
            x2 = int(x2 * original_width / 1024)
            y2 = int(y2 * original_height / 1024)
            
            results.append({
                'class': self.labels[class_id],
                'confidence': float(confidence),
                'bbox': [x1, y1, x2, y2]
            })
        
        return results

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

    def is_new_scene(self, current_time, last_photo_time):
        if last_photo_time is None:
            return True
        time_difference = current_time - last_photo_time
        return time_difference > timedelta(minutes=30)

    def get_or_create_animal_id(self, scene_bboxes, animal_ids, new_bbox):
        for i, existing_bbox in enumerate(scene_bboxes):
            if self.is_same_animal(existing_bbox, new_bbox):
                return f"animal_{i+1}"
        
        new_id = f"animal_{len(animal_ids) + 1}"
        animal_ids.add(new_id)
        return new_id

    def is_same_animal(self, bbox1, bbox2):
        x1, y1, x2, y2 = bbox1
        x3, y3, x4, y4 = bbox2
        center1 = ((x1 + x2) / 2, (y1 + y2) / 2)
        center2 = ((x3 + x4) / 2, (y3 + y4) / 2)
        distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
        return distance < 50

    def open_photo(self, row, column):
        start_idx = (self.current_page - 1) * self.items_per_page
        photo_id = self.db.get_photos(folder=self.current_folder)[start_idx + row][0]
        self.show_processing_page(photo_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_folders()
        self.load_photos()