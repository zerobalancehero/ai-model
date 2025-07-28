import os
import sqlite3
from datetime import datetime
from PIL import Image

DB_FILE = 'database.db'

def setup_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS images (
            prompt TEXT,
            filename TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def generate_image(prompt, output_dir):
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(output_dir, filename)

    # Generates a placeholder image; replace with real model integration
    img = Image.new("RGB", (512, 512), color=(127, 127, 127))
    img.save(filepath)

    return filename

def save_metadata(prompt, filename):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO images VALUES (?, ?, ?)', (prompt, filename, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT prompt, filename FROM images ORDER BY timestamp DESC')
    data = c.fetchall()
    conn.close()
    return data