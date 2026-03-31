import sqlite3
import json

conn = sqlite3.connect("roomzy.db")
cur = conn.cursor()

# 🔥 ADD COLUMN (agar na ho)
try:
    cur.execute("ALTER TABLE pgs ADD COLUMN images TEXT")
except:
    pass

# 🔥 PG NAMES
pg_names = [
"Sunrise PG","Urban Nest","Royal Stay","Green View","City Comfort",
"Elite Stay","Happy Homes","Skyline PG","Comfort Zone","Dream Stay",
"Peaceful PG","Golden Nest","Blue Haven","Smart Living","Royal Comfort"
]

# 🔥 OWNER NAMES
owners = [
"Rahul Sharma","Amit Verma","Priya Singh","Neha Gupta","Rohit Kumar",
"Ankit Yadav","Sneha Kapoor","Vikas Mehta","Pooja Jain","Karan Malhotra",
"Simran Kaur","Aditya Raj","Nisha Arora","Deepak Singh","Manish Patel"
]

# 🔥 DESCRIPTIONS
descs = [
"Comfortable and peaceful stay with modern facilities. Ideal for students.",
"Affordable PG with food and WiFi near metro station.",
"Spacious rooms with daily cleaning and good ventilation.",
"Premium PG with AC rooms and secure environment.",
"Budget-friendly PG with all essential amenities.",
"Well-maintained PG with modern interiors.",
"Perfect student stay with all facilities.",
"Safe and secure PG with friendly environment.",
"Fully furnished rooms with great connectivity.",
"Peaceful PG with hygiene and comfort.",
"Comfortable stay with all facilities included.",
"Modern PG with easy transport access.",
"Affordable and clean PG with good services.",
"Spacious and well-designed rooms.",
"Premium PG with top facilities and safety."
]

# 🔥 GET IDS
cur.execute("SELECT id FROM pgs")
ids = [row[0] for row in cur.fetchall()]

# 🔥 UPDATE LOOP
for i in range(len(ids)):
    index = i + 1

    cur.execute("""
    UPDATE pgs 
    SET pg_name=?, owner_name=?, description=?, image=?, images=? 
    WHERE id=?
    """, (
        pg_names[i % len(pg_names)],
        owners[i % len(owners)],
        descs[i % len(descs)],
        f"http://127.0.0.1:5000/static/images/pg{index}.jpg",
        json.dumps([
            f"http://127.0.0.1:5000/static/images/pg{index}_1.jpg",
            f"http://127.0.0.1:5000/static/images/pg{index}_2.jpg",
            f"http://127.0.0.1:5000/static/images/pg{index}_3.jpg"
        ]),
        ids[i]
    ))

conn.commit()
conn.close()

print("🔥 FULL DB UPDATED SUCCESSFULLY")