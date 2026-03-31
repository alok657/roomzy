import sqlite3

conn = sqlite3.connect("roomzy.db")
cur = conn.cursor()

# saare data le lo
cur.execute("SELECT * FROM pgs")
rows = cur.fetchall()

# table clear karo
cur.execute("DELETE FROM pgs")

# dobara insert karo correct ids ke sath
new_id = 1

for row in rows:
    cur.execute("""
    INSERT INTO pgs (id, pg_name, city, rent, description, image, owner_name, owner_phone)
    VALUES (?,?,?,?,?,?,?,?)
    """, (
        new_id,
        row[1],
        row[2],
        row[3],
        row[4],
        row[5],
        row[6],
        row[7]
    ))
    new_id += 1

conn.commit()
conn.close()

print("🔥 IDs fixed from 1 to N")