import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QFileDialog, QCheckBox, QProgressDialog,
                             QLabel, QMainWindow, QStackedWidget)
from PyQt6.QtGui import QScreen
from PyQt6.QtCore import Qt
from database import Database
from photo_bank import PhotoBankPage
from photo_processing import PhotoProcessingPage
from map_page import MapPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Фото Анализатор")
        
        # Получаем размер основного экрана
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(screen)
        
        # Устанавливаем максимальный размер окна равным размеру экрана
        self.setMaximumSize(screen.width(), screen.height())

        # Инициализация базы данных
        self.db = Database()

        # Создание и настройка стека виджетов
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Создание страниц
        self.photo_bank_page = PhotoBankPage(self.db, self.show_processing_page)
        self.photo_processing_page = PhotoProcessingPage(self.db, self.show_photo_bank_page)
        self.map_page = MapPage(self.db)

        # Добавление страниц в стек
        self.stacked_widget.addWidget(self.photo_bank_page)
        self.stacked_widget.addWidget(self.photo_processing_page)
        self.stacked_widget.addWidget(self.map_page)

        # Подключение сигналов кнопок навигации
        self.photo_bank_page.nav_menu.photo_bank_button.clicked.connect(self.show_photo_bank_page)
        self.photo_bank_page.nav_menu.map_button.clicked.connect(self.show_map_page)
        self.photo_processing_page.nav_menu.photo_bank_button.clicked.connect(self.show_photo_bank_page)
        self.photo_processing_page.nav_menu.map_button.clicked.connect(self.show_map_page)
        self.map_page.nav_menu.photo_bank_button.clicked.connect(self.show_photo_bank_page)
        self.map_page.nav_menu.map_button.clicked.connect(self.show_map_page)

        # Установка начальной страницы
        self.show_photo_bank_page()

        # Применение стилей
        self.apply_styles()

    def show_photo_bank_page(self):
        self.stacked_widget.setCurrentWidget(self.photo_bank_page)

    def show_processing_page(self, photo_id):
        self.photo_processing_page.load_photo(photo_id)
        self.stacked_widget.setCurrentWidget(self.photo_processing_page)

    def show_map_page(self):
        self.stacked_widget.setCurrentWidget(self.map_page)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #525252;
                color: white;
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #a6a6a6;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())