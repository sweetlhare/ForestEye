from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QDateEdit, QTimeEdit, QPushButton
from PyQt6.QtCore import QDateTime
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
import io
from navigation_menu import NavigationMenu
import os
from folium.plugins import MiniMap
from branca.colormap import LinearColormap
import sqlite3

class MapPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
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
        self.layout.addWidget(self.map_view)

        # Initial map load
        self.load_map()

    def load_map(self):
        map_file = 'pre_saved_map.html'
        if not os.path.exists(map_file):
            self.create_map(map_file)
        with open(map_file, 'r', encoding='utf-8') as f:
            html = f.read()
        self.map_view.setHtml(html)

    def create_map(self, filename):
        # Create a map centered on Moscow
        m = folium.Map(location=[55.7558, 37.6173], zoom_start=10, control_scale=True)

        # Add MBTiles layer
        mbtiles_path = 'maptiler-osm-2020-02-10-v3.11-russia.mbtiles'
        if os.path.exists(mbtiles_path):
            conn = sqlite3.connect(mbtiles_path)
            cur = conn.cursor()
            cur.execute('SELECT value FROM metadata WHERE name="json"')
            json_data = cur.fetchone()[0]
            conn.close()

            folium.TileLayer(
                tiles=f'http://localhost:8080/maptiler-osm-2020-02-10-v3.11-russia/{{z}}/{{x}}/{{y}}.png',
                attr='Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, '
                     'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
                name='MBTiles Map',
                overlay=False,
                control=True
            ).add_to(m)
        else:
            print(f"MBTiles file not found: {mbtiles_path}")

        # Add a marker for Moscow
        folium.Marker([55.7558, 37.6173], popup="Moscow").add_to(m)

        # Add a MiniMap
        minimap = MiniMap()
        m.add_child(minimap)

        # Add a ColorMap
        colormap = LinearColormap(colors=['green', 'yellow', 'red'], vmin=0, vmax=100)
        colormap.add_to(m)

        # Save map to file
        m.save(filename)

    def update_map(self):
        selected_date = self.date_edit.date().toPyDate()
        selected_time = self.time_edit.time().toPyTime()
        # Here you would update your data based on the selected date and time
        # Then recreate and reload the map
        self.create_map('pre_saved_map.html')
        self.load_map()