import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton)


class NavigationMenu(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.photo_bank_button = QPushButton("Фотобанк")
        # self.photo_processing_button = QPushButton("Обработка фото")
        self.map_button = QPushButton("Карта")

        self.layout.addWidget(self.photo_bank_button)
        # self.layout.addWidget(self.photo_processing_button)
        self.layout.addWidget(self.map_button)