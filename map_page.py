from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QComboBox, QLabel
from PyQt6.QtCore import QDateTime
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
from folium.plugins import MarkerCluster
import io
from navigation_menu import NavigationMenu
from datetime import datetime, date

folder_coordinates = {
    "1": [55.7558, 37.6173],  # Москва (центр)
    "2": [55.9716, 37.4107],  # Химки
    "3": [55.7587, 37.8629],  # Реутов
    "4": [55.7950, 37.9297],  # Балашиха
    "5": [55.5674, 37.8601],  # Дзержинский
    "6": [55.5529, 37.7133],  # Видное
    "7": [55.4255, 37.5445],  # Подольск
    "8": [55.5980, 38.1223],  # Люберцы
    "9": [55.9130, 37.7373],  # Мытищи
    "10": [55.8204, 37.3320], # Красногорск
    "11": [55.7950, 38.4416], # Электросталь
    "12": [55.6555, 37.1823], # Одинцово
    "13": [56.0104, 37.4770], # Долгопрудный
    "14": [55.9191, 37.8234], # Королев
    "15": [55.6701, 37.4829], # Внуково
    "16": [55.5785, 38.2030], # Жуковский
    "17": [55.8313, 37.2981], # Митино
    "18": [55.7016, 37.3591], # Солнцево
    "19": [55.5583, 37.0796], # Апрелевка
    "20": [55.9243, 38.0155], # Щелково
    "21": [55.8740, 37.6178], # Медведково
    "22": [55.7021, 37.8593], # Люблино
    "23": [55.8862, 37.4447], # Тушино
    "24": [55.6679, 37.7481], # Марьино
    "25": [55.9170, 37.6180], # Северный
    "26": [55.7533, 38.0441], # Железнодорожный
    "27": [55.8943, 37.2909], # Куркино
    "28": [55.6105, 37.3869], # Тропарево-Никулино
    "29": [55.7064, 37.5975], # Хамовники
    "30": [55.6165, 37.6073], # Чертаново
    "31": [55.8608, 37.7398], # Лосиноостровский
    "32": [55.7250, 37.6711], # Таганский
    "33": [55.7522, 37.5982], # Пресненский
    "34": [55.7667, 37.7681], # Перово
    "35": [55.6427, 37.5195], # Черемушки
    "36": [55.8534, 37.4862], # Савеловский
    "37": [55.7058, 37.7624], # Кузьминки
    "38": [55.7893, 37.5490], # Беговой
    "39": [55.8751, 37.6588], # Бабушкинский
    "40": [55.7123, 37.4537], # Фили-Давыдково
    "41": [55.6711, 37.5515], # Зюзино
    "42": [55.8089, 37.6355], # Марьина Роща
    "43": [55.7909, 37.7487], # Богородское
    "44": [55.7293, 37.4442], # Кунцево
    "45": [55.6802, 37.6635], # Даниловский
    "46": [55.8100, 37.8397], # Гольяново
    "47": [55.6755, 37.7618], # Текстильщики
    "48": [55.7154, 37.8146], # Выхино-Жулебино
    "49": [55.8940, 37.5529], # Алтуфьевский
    "50": [55.6227, 37.6801]  # Царицыно
}

class MapPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)  # Добавляем отступы
        self.layout.setSpacing(15)  # Увеличиваем расстояние между элементами

        # Navigation menu
        self.nav_menu = NavigationMenu(self)
        self.layout.addWidget(self.nav_menu)

        # Создаем контейнер для элементов управления
        self.controls_widget = QWidget()
        self.controls_layout = QVBoxLayout(self.controls_widget)
        self.controls_layout.setContentsMargins(0, 10, 0, 10)  # Добавляем отступы сверху и снизу
        
        # Folder selection
        self.folder_layout = QHBoxLayout()
        self.folder_combo = QComboBox()
        self.folder_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 5px;
                min-width: 200px;
            }
        """)
        self.folder_combo.currentTextChanged.connect(self.update_date_time_options)
        self.folder_layout.addWidget(self.folder_combo)
        self.folder_layout.addStretch(1)  # Добавляем растягивающийся элемент справа
        self.controls_layout.addLayout(self.folder_layout)

        # Date and Time selection
        self.date_time_layout = QHBoxLayout()
        self.date_label = QLabel("Дата:")
        self.date_label.setStyleSheet("font-size: 16px;")
        self.date_combo = QComboBox()
        self.date_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 5px;
                min-width: 150px;
            }
        """)
        self.time_label = QLabel("Время:")
        self.time_label.setStyleSheet("font-size: 16px;")
        self.time_combo = QComboBox()
        self.time_combo.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 5px;
                min-width: 100px;
            }
        """)
        self.update_button = QPushButton("Обновить карту")
        self.update_button.setStyleSheet("""
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
        self.update_button.clicked.connect(self.update_map)
        self.date_time_layout.addWidget(self.date_label)
        self.date_time_layout.addWidget(self.date_combo)
        self.date_time_layout.addWidget(self.time_label)
        self.date_time_layout.addWidget(self.time_combo)
        self.date_time_layout.addStretch(1)  # Добавляем растягивающийся элемент
        self.date_time_layout.addWidget(self.update_button)
        self.controls_layout.addLayout(self.date_time_layout)

        self.layout.addWidget(self.controls_widget)

        # Map view
        self.map_view = QWebEngineView()
        self.map_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.map_view)

        # Set the stretch factor for the map view to make it take all available space
        self.layout.setStretch(0, 0)  # Navigation menu
        self.layout.setStretch(1, 0)  # Controls widget
        self.layout.setStretch(2, 1)  # Map view (will take all available space)

        # Hardcoded coordinates for folders (near Moscow)
        self.folder_coordinates = folder_coordinates

        # Initial data load
        self.load_folders()
        self.load_map()

    def load_folders(self):
        folders = self.db.get_unique_folders()
        self.folder_combo.addItems(folders)

    def update_date_time_options(self):
        selected_folder = self.folder_combo.currentText()
        timestamps = self.db.get_timestamps_for_folder(selected_folder)
        
        self.date_combo.clear()
        self.time_combo.clear()
        
        if timestamps:
            # Update date options
            unique_dates = sorted(set(ts.date() for ts in timestamps))
            self.date_combo.addItems([date.strftime('%Y-%m-%d') for date in unique_dates])
            
            # Update time options for the first date
            if unique_dates:
                self.update_time_options(unique_dates[0])
            
            # Connect date change to time update
            self.date_combo.currentTextChanged.connect(lambda x: self.update_time_options(x))
        else:
            print(f"No timestamps found for folder: {selected_folder}")

    def update_time_options(self, selected_date):
        if not selected_date:
            print("No date selected")
            return

        selected_folder = self.folder_combo.currentText()
        timestamps = self.db.get_timestamps_for_folder(selected_folder)
        
        if isinstance(selected_date, str):
            try:
                selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            except ValueError:
                print(f"Invalid date format: {selected_date}")
                return
        elif not isinstance(selected_date, date):
            print(f"Unexpected date type: {type(selected_date)}")
            return

        times_for_date = [ts.time() for ts in timestamps if ts.date() == selected_date]
        
        self.time_combo.clear()
        self.time_combo.addItems([time.strftime('%H:%M:%S') for time in sorted(times_for_date)])

    def load_map(self):
        selected_folder = self.folder_combo.currentText()
        if not selected_folder:
            print("No folder selected")
            return

        selected_date = self.date_combo.currentText()
        selected_time = self.time_combo.currentText()

        if not selected_date or not selected_time:
            print("Date or time not selected")
            return

        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            selected_time = datetime.strptime(selected_time, '%H:%M:%S').time()
            selected_datetime = datetime.combine(selected_date, selected_time)
        except ValueError as e:
            print(f"Error parsing date or time: {e}")
            return

        # Create a map centered on Moscow
        m = folium.Map(location=[55.7558, 37.6173], zoom_start=10)

        # Create a MarkerCluster
        marker_cluster = MarkerCluster().add_to(m)

        # Get photo data for the selected folder and datetime
        photos = self.db.get_photos_for_map(selected_folder, selected_datetime)
        print(f"Photos for {selected_folder} at {selected_datetime}: {photos}")

        for photo in photos:
            folder = photo['folder'].split('/')[-1]
            if folder in self.folder_coordinates:
                lat, lon = self.folder_coordinates[folder]
                print(f"Adding marker for folder {folder} at {lat}, {lon}")
                popup_text = f"Folder: {folder}<br>Animals: {photo['animal_count']}<br>Unique animals: {photo['unique_animal_count']}"
                folium.Marker(
                    [lat, lon], 
                    popup=popup_text,
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(marker_cluster)
            else:
                print(f"Warning: No coordinates found for folder {folder}")
        
        if not photos:
            print(f"No photos found for {selected_folder} at {selected_datetime}")

        # Save map to data string
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())
        
        # Устанавливаем стиль для расширения карты на всю доступную область
        self.map_view.page().runJavaScript("""
            document.body.style.margin = '0';
            document.body.style.padding = '0';
            document.body.style.height = '100vh';
            document.getElementsByTagName('div')[0].style.height = '100%';
        """)

    def update_map(self):
        self.load_map()