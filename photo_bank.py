from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QFileDialog, QCheckBox, QProgressDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from navigation_menu import NavigationMenu

class PhotoBankPage(QWidget):
    def __init__(self, db, show_processing_page):
        super().__init__()
        self.db = db
        self.show_processing_page = show_processing_page
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.nav_menu = NavigationMenu(self)
        layout.addWidget(self.nav_menu)

        self.photo_table = QTableWidget()
        self.photo_table.setColumnCount(6)
        self.photo_table.setHorizontalHeaderLabels(["", "Фото", "Дата загрузки", "Широта", "Долгота", "Обработано"])
        self.photo_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.photo_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.photo_table)

        button_layout = QHBoxLayout()
        self.upload_button = QPushButton("Загрузить фото")
        self.upload_folder_button = QPushButton("Загрузить папку")
        self.process_button = QPushButton("Обработать выбранные")
        button_layout.addWidget(self.upload_button)
        button_layout.addWidget(self.upload_folder_button)
        button_layout.addWidget(self.process_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.upload_button.clicked.connect(self.upload_photo)
        self.upload_folder_button.clicked.connect(self.upload_folder)
        self.process_button.clicked.connect(self.process_selected)
        self.photo_table.cellDoubleClicked.connect(self.open_photo)

        self.load_photos()

    def load_photos(self):
        photos = self.db.get_photos()
        self.photo_table.setRowCount(len(photos))
        for row, photo in enumerate(photos):
            photo_id, path, upload_date, latitude, longitude, processed = photo
            
            checkbox = QCheckBox()
            self.photo_table.setCellWidget(row, 0, checkbox)
            
            pixmap = QPixmap(path).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            thumbnail_item = QTableWidgetItem()
            thumbnail_item.setData(Qt.ItemDataRole.DecorationRole, pixmap)
            self.photo_table.setItem(row, 1, thumbnail_item)
            
            self.photo_table.setItem(row, 2, QTableWidgetItem(upload_date))
            self.photo_table.setItem(row, 3, QTableWidgetItem(str(latitude)))
            self.photo_table.setItem(row, 4, QTableWidgetItem(str(longitude)))
            self.photo_table.setItem(row, 5, QTableWidgetItem("Да" if processed else "Нет"))

    def upload_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите фото", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            self.process_single_photo(file_name)

    def upload_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Выберите папку с фотографиями")
        if folder_name:
            image_files = [f for f in os.listdir(folder_name) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            progress = QProgressDialog("Загрузка фотографий...", "Отмена", 0, len(image_files), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс загрузки")
            
            for i, image_file in enumerate(image_files):
                if progress.wasCanceled():
                    break
                
                file_path = os.path.join(folder_name, image_file)
                self.process_single_photo(file_path)
                progress.setValue(i + 1)
            
            progress.setValue(len(image_files))
            self.load_photos()

    def process_single_photo(self, file_path):
        latitude, longitude = self.get_gps_data(file_path)
        self.db.add_photo(file_path, latitude, longitude)

    def get_gps_data(self, file_name):
        image = Image.open(file_name)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_tag = GPSTAGS.get(t, t)
                        gps_data[sub_tag] = value[t]
                    
                    lat = self.convert_to_degrees(gps_data.get('GPSLatitude', (0, 0, 0)))
                    lon = self.convert_to_degrees(gps_data.get('GPSLongitude', (0, 0, 0)))
                    
                    if gps_data.get('GPSLatitudeRef', 'N') != 'N':
                        lat = -lat
                    if gps_data.get('GPSLongitudeRef', 'E') != 'E':
                        lon = -lon
                    
                    return lat, lon
        return None, None

    def convert_to_degrees(self, value):
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)

    def process_selected(self):
        selected_photo_ids = []
        for row in range(self.photo_table.rowCount()):
            checkbox = self.photo_table.cellWidget(row, 0)
            if checkbox.isChecked():
                photo_id = self.db.get_photos()[row][0]
                selected_photo_ids.append(photo_id)

        if selected_photo_ids:
            progress = QProgressDialog("Обработка фотографий...", "Отмена", 0, len(selected_photo_ids), self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Прогресс обработки")
            
            for i, photo_id in enumerate(selected_photo_ids):
                if progress.wasCanceled():
                    break
                
                self.process_photo(photo_id)
                progress.setValue(i + 1)
            
            progress.setValue(len(selected_photo_ids))
            self.load_photos()

    def process_photo(self, photo_id):
        photo_data = self.db.get_photo(photo_id)
        if photo_data:
            image_path = photo_data[1]
            image = Image.open(image_path)
            width, height = image.size

            # Здесь должен быть код обработки фотографии нейросетью
            # Для примера, мы просто создаем случайный bounding box и маску
            x1 = int(width * 0.1)
            y1 = int(height * 0.1)
            x2 = int(width * 0.9)
            y2 = int(height * 0.9)

            # Создаем случайную маску
            mask = Image.new('L', (width, height), 0)
            for x in range(width):
                for y in range(height):
                    mask.putpixel((x, y), int(((x-width/2)**2 + (y-height/2)**2) < (min(width,height)/3)**2) * 255)
            
            if not os.path.exists('masks'):
                os.makedirs('masks')
            mask.save(f'masks/mask_{photo_id}.png')

            # Обновляем информацию в базе данных
            self.db.update_photo_processing(photo_id, x1, y1, x2, y2)

    def open_photo(self, row, column):
        photo_id = self.db.get_photos()[row][0]
        self.show_processing_page(photo_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_photos()