from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__,static_folder="static")
CORS(app)


def get_db():
    conn = sqlite3.connect("roomzy.db")
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return "Roomzy Backend Running ✅"


# ================= DB SETUP =================
@app.route("/setupdb")
def setupdb():

    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        password TEXT,
        role TEXT
    )
    """)

    # PGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pgs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pg_name TEXT,
        city TEXT,
        rent INTEGER,
        description TEXT,
        image TEXT,
        owner_name TEXT,
        owner_phone TEXT
    )
    """)

    conn.commit()
    return "Database Ready ✅"


# ================= AUTH =================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
        (data["name"], data["email"], data["password"], "")
    )

    conn.commit()
    return {"message": "Signup success"}


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (data["email"], data["password"])
    )

    user = cur.fetchone()

    if user:
        return {
            "status": "success",
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    else:
        return {"status": "error", "message": "Invalid login"}


# ================= ADD PG =================
@app.route("/add_pg", methods=["POST"])
def add_pg():

    data = request.json

    conn = get_db()
    cur = conn.cursor()

    # 🔥 NEW
    owner_id = data.get("owner_id")
    images = json.dumps(data.get("images", []))  # list → string

    cur.execute("""
    INSERT INTO pgs (pg_name, city, rent, description, image, owner_name, owner_phone, images, owner_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["pg_name"],
        data["city"],
        data["rent"],
        data["description"],
        data["image"],
        data["owner_name"],
        data["owner_phone"],
        images,          # 🔥 added
        owner_id         # 🔥 added
    ))

    conn.commit()
    return {"message": "PG added"}


# ================= DEMO DATA =================
@app.route("/add_demo_pgs")
def add_demo_pgs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM pgs")

    demo = []

    cities = ["Delhi","Noida","Ghaziabad","Gurgaon","Faridabad"]

    for i in range(1,41):

        city = cities[i % len(cities)]

        demo.append((
            f"PG {i}",
            city,
            5000 + (i*100),
            f"Nice PG {i}",
            f"https://source.unsplash.com/400x300/?room,bedroom&sig={i}",
            f"Owner {i}",
            f"98765432{i:02d}"
        ))

    for pg in demo:
        cur.execute("""
        INSERT INTO pgs(pg_name,city,rent,description,image,owner_name,owner_phone)
        VALUES (?,?,?,?,?,?,?)
        """, pg)

    conn.commit()
    return "40 PGs Added 🔥"

    

# ================= GET =================
@app.route("/get_pgs")
def get_pgs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pgs")
    rows = cur.fetchall()

    pgs = []

    import json

    for r in rows:

        images = []

        # 🔥 SAFE IMAGE HANDLING
        if "images" in r.keys() and r["images"]:
            try:
                images = json.loads(r["images"])
            except:
                images = [r["image"]]
        else:
            images = [r["image"]]

        pgs.append({
            "id": r["id"],
            "pg_name": r["pg_name"],
            "city": r["city"],
            "rent": r["rent"],
            "description": r["description"],
            "image": r["image"],
            "images": images   # 🔥 IMPORTANT
        })

    return jsonify(pgs)


import json

@app.route("/get_pg/<int:id>")
def get_pg(id):

    conn = sqlite3.connect("roomzy.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM pgs WHERE id=?", (id,))
    row = cur.fetchone()

    if not row:
        return {"error": "PG not found"}

    # 🔥 SAFE IMAGE HANDLING
    images = []

    if "images" in row.keys() and row["images"]:
        try:
            images = json.loads(row["images"])
        except:
            images = [row["image"]]
    else:
        images = [row["image"]]

    return {
        "id": row["id"],
        "pg_name": row["pg_name"],
        "city": row["city"],
        "rent": row["rent"],
        "description": row["description"],
        "image": row["image"],
        "images": images,
        "owner_name": row["owner_name"],
        "owner_phone": row["owner_phone"]
    }

@app.route('/delete_pg/<int:id>', methods=['DELETE'])
def delete_pg(id):
    import sqlite3
    conn = sqlite3.connect("roomzy.db")
    cur = conn.cursor()

    # 🔥 delete PG
    cur.execute("DELETE FROM pgs WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return {"message": "PG deleted successfully"}
