import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('photo_analyzer.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                processed BOOLEAN DEFAULT 0,
                x1 INTEGER,
                y1 INTEGER,
                x2 INTEGER,
                y2 INTEGER
            )
        ''')
        self.conn.commit()

    def add_photo(self, path, latitude, longitude):
        cursor = self.conn.cursor()
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO photos (path, upload_date, latitude, longitude)
            VALUES (?, ?, ?, ?)
        ''', (path, upload_date, latitude, longitude))
        self.conn.commit()
        return cursor.lastrowid

    def get_photos(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, path, upload_date, latitude, longitude, processed FROM photos')
        return cursor.fetchall()

    def get_photo(self, photo_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM photos WHERE id = ?', (photo_id,))
        return cursor.fetchone()

    def update_photo_processing(self, photo_id, x1, y1, x2, y2):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE photos
            SET processed = 1, x1 = ?, y1 = ?, x2 = ?, y2 = ?
            WHERE id = ?
        ''', (x1, y1, x2, y2, photo_id))
        self.conn.commit()

    def __del__(self):
        self.conn.close()