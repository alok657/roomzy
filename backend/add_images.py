import sqlite3
import json
import random

conn = sqlite3.connect("roomzy.db")
cur = conn.cursor()

def generate_images(pg_id):
    base_keywords = [
        "pg room", "hostel room", "student room",
        "bedroom interior", "shared room", "living room"
    ]

    images = []

    for i in range(4):
        keyword = random.choice(base_keywords)
        img = f"https://source.unsplash.com/400x300/?{keyword}&sig={pg_id}{i}"
        images.append(img)

    return images


cur.execute("SELECT id FROM pgs")
rows = cur.fetchall()

for row in rows:
    pg_id = row[0]
    imgs = generate_images(pg_id)

    cur.execute(
        "UPDATE pgs SET images=? WHERE id=?",
        (json.dumps(imgs), pg_id)
    )

conn.commit()
conn.close()

print("🔥 ALL PGs got UNIQUE images")