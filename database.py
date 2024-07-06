import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('animal_counter.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                folder TEXT NOT NULL,
                upload_date TEXT NOT NULL,
                processed BOOLEAN DEFAULT 0,
                scene_id INTEGER,
                animal_count INTEGER,
                unique_animal_count INTEGER,
                timestamp TEXT,
                bbox_string TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_animal_count INTEGER
            )
        ''')
        self.conn.commit()

    def get_photo(self, photo_id):
        self.cursor.execute("""
            SELECT id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp, bbox_string
            FROM photos 
            WHERE id = ?
        """, (photo_id,))
        return self.cursor.fetchone()

    def add_photo(self, path, timestamp):
        upload_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        folder = os.path.dirname(path)
        self.cursor.execute('''
            INSERT INTO photos (path, folder, upload_date, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (path, folder, upload_date, timestamp))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_photo_processing(self, photo_id, scene_id, animal_count, unique_animal_count, bbox_string, timestamp):
        self.cursor.execute('''
            UPDATE photos
            SET processed = 1, scene_id = ?, animal_count = ?, unique_animal_count = ?, bbox_string = ?, timestamp = ?
            WHERE id = ?
        ''', (scene_id, animal_count, unique_animal_count, bbox_string, timestamp.strftime("%Y-%m-%d %H:%M:%S"), photo_id))
        self.conn.commit()

    def get_unique_folders(self):
        self.cursor.execute("SELECT DISTINCT folder FROM photos")
        return [row[0] for row in self.cursor.fetchall()]

    def get_photos(self, folder=None):
        if folder:
            self.cursor.execute("""
                SELECT id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp
                FROM photos 
                WHERE folder = ? 
                ORDER BY timestamp DESC
            """, (folder,))
        else:
            self.cursor.execute("""
                SELECT id, path, folder, upload_date, processed, scene_id, animal_count, unique_animal_count, timestamp
                FROM photos 
                ORDER BY timestamp DESC
            """)
        return self.cursor.fetchall()

    def get_bounding_boxes(self, photo_id):
        self.cursor.execute('SELECT x1, y1, x2, y2, animal_id, category FROM bounding_boxes WHERE photo_id = ?', (photo_id,))
        return self.cursor.fetchall()

    def update_scene_unique_count(self, scene_id, unique_count):
        self.cursor.execute('''
            INSERT OR REPLACE INTO scenes (id, unique_animal_count)
            VALUES (?, ?)
        ''', (scene_id, unique_count))
        self.conn.commit()

    def get_scene_unique_count(self, scene_id):
        self.cursor.execute('SELECT unique_animal_count FROM scenes WHERE id = ?', (scene_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_last_photo_in_scene(self, scene_id):
        self.cursor.execute('''
            SELECT * FROM photos 
            WHERE scene_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''', (scene_id,))
        return self.cursor.fetchone()

    def create_new_scene(self):
        self.cursor.execute('INSERT INTO scenes (unique_animal_count) VALUES (0)')
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_timestamps_for_folder(self, folder):
        self.cursor.execute("""
            SELECT timestamp
            FROM photos
            WHERE folder = ?
            ORDER BY timestamp
        """, (folder,))
        return [datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') for row in self.cursor.fetchall()]

    def get_photos_for_map(self, folder, selected_datetime):
        self.cursor.execute("""
            SELECT folder, animal_count, unique_animal_count
            FROM photos
            WHERE folder = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (folder, selected_datetime.strftime('%Y-%m-%d %H:%M:%S')))
        result = self.cursor.fetchone()
        if result:
            return [{
                'folder': result[0],
                'animal_count': result[1],
                'unique_animal_count': result[2]
            }]
        return []
    
    def get_export_data(self, folder=None):
        query = """
            SELECT 
                p.folder,
                p.bbox_string,
                MIN(p.timestamp) as date_registration_start,
                MAX(p.timestamp) as date_registration_end,
                s.unique_animal_count as count
            FROM 
                photos p
            JOIN 
                scenes s ON p.scene_id = s.id
            WHERE 
                p.bbox_string IS NOT NULL AND p.bbox_string != ''
        """
        
        if folder:
            query += " AND p.folder = ?"
            query += " GROUP BY p.folder, p.scene_id"
            self.cursor.execute(query, (folder,))
        else:
            query += " GROUP BY p.folder, p.scene_id"
            self.cursor.execute(query)
        
        results = self.cursor.fetchall()
        
        processed_results = []
        for row in results:
            folder, bbox_string, start, end, count = row
            
            # Extract class from bbox_string
            bboxes = bbox_string.split(";")
            if bboxes:
                # Take the class from the first bounding box
                class_name = bboxes[0].split(",")[5] if len(bboxes[0].split(",")) > 5 else "Unknown"
            else:
                class_name = "Unknown"
            
            processed_results.append((
                folder,
                class_name,
                datetime.strptime(start, '%Y-%m-%d %H:%M:%S'),
                datetime.strptime(end, '%Y-%m-%d %H:%M:%S'),
                count
            ))
        
        return processed_results

    def __del__(self):
        self.conn.close()
