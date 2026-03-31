import sqlite3
import json

conn = sqlite3.connect("roomzy.db")
cur = conn.cursor()

# 🔥 PURANI IMAGES CLEAR
cur.execute("UPDATE pgs SET images=NULL")

# 🔥 NEW IMAGES ADD
for i in range(1,16):

    images = [
        f"http://127.0.0.1:5000/static/images/pg{i}_1.jpg",
        f"http://127.0.0.1:5000/static/images/pg{i}_2.jpg",
        f"http://127.0.0.1:5000/static/images/pg{i}_3.jpg"
    ]

    cur.execute(
        "UPDATE pgs SET images=? WHERE id=?",
        (json.dumps(images), i)
    )

conn.commit()
conn.close()

print("🔥 ALL IMAGES RESET & ADDED")