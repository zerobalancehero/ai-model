import os
import sqlite3
from datetime import datetime

DB_FILE = 'database.db'
IMAGE_DIR = 'static/images'

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

for filename in os.listdir(IMAGE_DIR):
    if filename.endswith(".png"):
        prompt = "Unknown (recovered)"
        timestamp = datetime.now().isoformat()
        c.execute('INSERT INTO images VALUES (?, ?, ?)', (prompt, filename, timestamp))

conn.commit()
conn.close()

print("Recovered previous images into database.")