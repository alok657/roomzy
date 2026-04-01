from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import json

app = Flask(__name__, static_folder="static")
CORS(app)

# 🔥 DATABASE CONNECT
def get_db():
    DATABASE_URL = "postgresql://roomzy_db_user:pJTpwafq3fNUQT9XNeRGM76T5mncgx65@dpg-d76i815m5p6s73bnfsc0-a/roomzy_db"
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ================= DB SETUP =================
@app.route("/setupdb")
def setupdb():

    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # PGS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pgs(
        id SERIAL PRIMARY KEY,
        pg_name TEXT,
        city TEXT,
        rent INTEGER,
        description TEXT,
        image TEXT,
        owner_name TEXT,
        owner_phone TEXT,
        images TEXT,
        owner_id INTEGER
    )
    """)

    conn.commit()
    conn.close()

    return "Database Ready ✅"


# ================= AUTH =================
@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
        (data["name"], data["email"], data["password"], "")
    )

    conn.commit()
    conn.close()

    return {"message": "Signup success"}


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (data["email"], data["password"])
    )

    user = cur.fetchone()

    conn.close()

    if user:
        return {
            "status": "success",
            "name": user[1],
            "email": user[2],
            "role": user[4]
        }
    else:
        return {"status": "error", "message": "Invalid login"}


# ================= ADD PG =================
@app.route("/add_pg", methods=["POST"])
def add_pg():

    data = request.json

    conn = get_db()
    cur = conn.cursor()

    owner_id = data.get("owner_id")
    images = json.dumps(data.get("images", []))

    cur.execute("""
    INSERT INTO pgs (pg_name, city, rent, description, image, owner_name, owner_phone, images, owner_id)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["pg_name"],
        data["city"],
        data["rent"],
        data["description"],
        data["image"],
        data["owner_name"],
        data["owner_phone"],
        images,
        owner_id
    ))

    conn.commit()
    conn.close()

    return {"message": "PG added"}


# ================= DEMO DATA =================
@app.route("/add_demo_pgs")
def add_demo_pgs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM pgs")

    cities = ["Delhi","Noida","Ghaziabad","Gurgaon","Faridabad"]

    for i in range(1,41):

        city = cities[i % len(cities)]

        cur.execute("""
        INSERT INTO pgs(pg_name,city,rent,description,image,owner_name,owner_phone)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            f"PG {i}",
            city,
            5000 + (i*100),
            f"Nice PG {i}",
            f"https://source.unsplash.com/400x300/?room,bedroom&sig={i}",
            f"Owner {i}",
            f"98765432{i:02d}"
        ))

    conn.commit()
    conn.close()

    return "40 PGs Added 🔥"


# ================= GET ALL =================
@app.route("/get_pgs")
def get_pgs():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pgs")
    rows = cur.fetchall()

    conn.close()

    pgs = []
    base_url = "https://roomzy-backend-phb5.onrender.com"

    for r in rows:

        images = []

        if r[8]:
            try:
                images = json.loads(r[8])
            except:
                images = [r[5]]
        else:
            images = [r[5]]

        image = r[5].replace("http://127.0.0.1:5000", base_url)

        fixed_images = [
            img.replace("http://127.0.0.1:5000", base_url)
            for img in images
        ]

        pgs.append({
            "id": r[0],
            "pg_name": r[1],
            "city": r[2],
            "rent": r[3],
            "description": r[4],
            "image": image,
            "images": fixed_images
        })

    return jsonify(pgs)


# ================= GET SINGLE =================
@app.route("/get_pg/<int:id>")
def get_pg(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM pgs WHERE id=%s", (id,))
    row = cur.fetchone()

    conn.close()

    if not row:
        return {"error": "PG not found"}

    base_url = "https://roomzy-backend-phb5.onrender.com"

    if row[8]:
        try:
            images = json.loads(row[8])
        except:
            images = [row[5]]
    else:
        images = [row[5]]

    image = row[5].replace("http://127.0.0.1:5000", base_url)

    fixed_images = [
        img.replace("http://127.0.0.1:5000", base_url)
        for img in images
    ]

    return {
        "id": row[0],
        "pg_name": row[1],
        "city": row[2],
        "rent": row[3],
        "description": row[4],
        "image": image,
        "images": fixed_images,
        "owner_name": row[6],
        "owner_phone": row[7]
    }


# ================= DELETE =================
@app.route('/delete_pg/<int:id>', methods=['DELETE'])
def delete_pg(id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM pgs WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return {"message": "PG deleted successfully"}

@app.route("/")
def home():
    return "Backend Running ✅"

@app.route("/test")
def test():
    return "Test OK 🚀"