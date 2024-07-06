from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QTimeEdit, QPushButton, QSizePolicy
from PyQt6.QtCore import QDateTime
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
import io
from navigation_menu import NavigationMenu

class MapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Navigation menu
        self.nav_menu = NavigationMenu(self)
        self.layout.addWidget(self.nav_menu)
        
        # Date and Time selection
        self.date_time_layout = QHBoxLayout()
        self.date_edit = QDateEdit(QDateTime.currentDateTime().date())
        self.time_edit = QTimeEdit(QDateTime.currentDateTime().time())
        self.update_button = QPushButton("Update Map")
        self.update_button.clicked.connect(self.update_map)
        self.date_time_layout.addWidget(self.date_edit)
        self.date_time_layout.addWidget(self.time_edit)
        self.date_time_layout.addWidget(self.update_button)
        self.layout.addLayout(self.date_time_layout)
        
        # Map view
        self.map_view = QWebEngineView()
        self.map_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.map_view)
        
        # Set the stretch factor for the map view to make it 80% of the total height
        self.layout.setStretch(0, 1)  # Navigation menu
        self.layout.setStretch(1, 1)  # Date and time layout
        self.layout.setStretch(2, 8)  # Map view (80% of the total height)
        
        # Initial map load
        self.load_map()

    def load_map(self):
        # Create a map centered on a specific location
        m = folium.Map(location=[55.7558, 37.6173], zoom_start=10)  # Moscow coordinates
        
        # Here you would load and add your data to the map
        # For example:
        # folium.Marker([55.7558, 37.6173], popup="Moscow").add_to(m)
        
        # Save map to data string
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.map_view.setHtml(data.getvalue().decode())

    def update_map(self):
        selected_date = self.date_edit.date().toPyDate()
        selected_time = self.time_edit.time().toPyTime()
        # Here you would update your data based on the selected date and time
        # Then reload the map
        self.load_map()