import os
import random
import sqlite3
from utils import log


def create_tables():
    conn = sqlite3.connect('lelexou.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                (id INTEGER PRIMARY KEY, path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pictures
                (path TEXT PRIMARY KEY, weight REAL, coefficient REAL)''')
    conn.commit()
    conn.close()

def check_for_new_pictures():
    conn = sqlite3.connect('lelexou.db')
    c = conn.cursor()
    
    # Get the maximum weight from the database to set for new pictures
    c.execute("SELECT MAX(weight) FROM pictures")
    max_weight = c.fetchone()[0] or 1  # Use 1 if the table is empty

    # Scan the directory for pictures
    directory = 'pictures'
    
    # Gather all file paths from the directory
    directory_files = {file for _, _, files in os.walk(directory) for file in files}
    
    # Retrieve all file paths from the database
    c.execute("SELECT path FROM pictures")
    db_paths = {row[0] for row in c.fetchall()}
    
    # Identify new and deleted files
    new_files = directory_files - db_paths
    deleted_files = db_paths - directory_files
    
    # Insert new files in a batch
    if new_files:
        c.executemany(
            "INSERT INTO pictures (path, weight, coefficient) VALUES (?, ?, ?)",
            [(new_file, max_weight, 1) for new_file in new_files]
        )
    
    # Delete removed files in a batch
    if deleted_files:
        c.executemany(
            "DELETE FROM pictures WHERE path = ?",
            [(deleted_file,) for deleted_file in deleted_files]
        )
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    log(f"Found {len(new_files)} new pictures and {len(deleted_files)} deleted pictures.")


def save_message(message, image):
    conn = sqlite3.connect('lelexou.db')
    c = conn.cursor()
    c.execute("INSERT INTO messages VALUES (?, ?)", (message.id, image))
    conn.commit()
    conn.close()

def select_image_and_update_weights():
    conn = sqlite3.connect('lelexou.db')
    c = conn.cursor()

    # Fetch all images and their weights from the database
    c.execute("SELECT * FROM pictures")
    rows = c.fetchall()

    if not rows:
        conn.close()
        return None

    # Choose an image randomly, weighted by the weight values
    image, _, _ = random.choices(rows, weights=[row[1] for row in rows])[0]

    # Reset the weight of the chosen image and increment the weight of all other images
    c.execute("UPDATE pictures SET weight = 0 WHERE path = ?", (image,))
    c.execute("UPDATE pictures SET weight = weight + coefficient WHERE path != ?", (image,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return image