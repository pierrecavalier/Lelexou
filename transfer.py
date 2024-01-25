import sqlite3
import json
import os

with open("pictures.json", "r") as file:
    data = json.load(file)

conn = sqlite3.connect('lelexou.db')
c = conn.cursor()

for path, weight in data.items():
    file = os.path.basename(path)
    c.execute("UPDATE pictures SET weight = ? WHERE path = ?", (weight, file))

conn.commit()
conn.close()
