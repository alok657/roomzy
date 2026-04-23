from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import json
import os
import uuid 

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if not os.path.exists("uploads"):
    os.makedirs("uploads")

from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder="static")
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'roomzy.support@gmail.com'
app.config['MAIL_PASSWORD'] = 'pjndzqwwnjwaiwjb'

mail = Mail(app)

# ================= DB CONNECT =================
def get_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise Exception("DATABASE_URL not set ❌")

    return psycopg2.connect(DATABASE_URL)


# ================= DB SETUP =================
@app.route("/setupdb")
def setupdb():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        is_verified BOOLEAN DEFAULT FALSE,
        verify_token TEXT
    )
    """)

    # 🔥 ADD NEW COLUMNS (if not exist)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN verify_token TEXT")
    except:
        pass

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

# ================= SIGNUP =================
from werkzeug.security import generate_password_hash
import re

@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        # 🔥 NAME VALIDATION
        if len(name) < 3 or not re.match(r'^[a-zA-Z\s]+$', name):
            return {"status":"error","message":"Invalid name"}

        # 🔥 EMAIL VALIDATION
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return {"status":"error","message":"Invalid Email"}

        # 🔥 PASSWORD VALIDATION
        if len(password) < 8:
            return {"status":"error","message":"Password too short"}

        if not re.search("[A-Z]", password):
            return {"status":"error","message":"Add uppercase"}

        if not re.search("[a-z]", password):
            return {"status":"error","message":"Add lowercase"}

        if not re.search("[0-9]", password):
            return {"status":"error","message":"Add number"}

        if not re.search("[!@#$%^&*]", password):
            return {"status":"error","message":"Add special char"}

        conn = get_db()
        cur = conn.cursor()

        # 🔍 CHECK EXISTING USER
        cur.execute("SELECT is_verified, verify_token FROM users WHERE email=%s", (email,))
        existing = cur.fetchone()

        if existing:
            is_verified = existing[0]
            token = existing[1]

            if not is_verified:
                # 🔥 RESEND EMAIL
                try:
                    print("RESENDING EMAIL")

                    msg = Message(
                        "Verify your Roomzy Account",
                        sender=("Roomzy Support", "roomzy.noreply@gmail.com"),
                        recipients=[email]
                    )

                    msg.html = f"""
                    <h2>Welcome Back 👋</h2>
                    <p>Please verify your account:</p>
                    <a href="https://roomzy-czyc.onrender.com/verify/{token}">
                        Verify Now
                    </a>
                    """

                    mail.send(msg)

                    print("RESEND SUCCESS")

                except Exception as e:
                    print("RESEND ERROR:", e)

                conn.close()
                return {
                    "status":"pending",
                    "message":"Email already registered but not verified. Verification mail resent 📩"
                }

            else:
                conn.close()
                return {"status":"error","message":"Email already exists"}

        # 🆕 NEW USER
        token = str(uuid.uuid4())
        hashed_password = generate_password_hash(password)

        cur.execute(
            """INSERT INTO users 
            (name,email,password,role,is_verified,verify_token) 
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (name, email, hashed_password, "student", False, token)
        )

        # 🔥 SEND EMAIL
        try:
            print("EMAIL SENDING START")

            msg = Message(
                "Verify your Roomzy Account",
                sender=("Roomzy Support", "roomzy.noreply@gmail.com"),
                recipients=[email]
            )

            msg.html = f"""
            <h2>Welcome to Roomzy 🏠</h2>
            <p>Click below to verify your account:</p>
            <a href="https://roomzy-czyc.onrender.com/verify/{token}">
                Verify Now
            </a>
            """

            mail.send(msg)

            print("EMAIL SENT SUCCESS")

        except Exception as e:
            print("EMAIL ERROR:", e)

        conn.commit()
        conn.close()

        return {"status":"success","message":"Signup successful. Check your email 📩"}

    except Exception as e:
        print("ERROR:", e)
        return {"status":"error","message":"Server error"}
    
# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, email, password, role, is_verified FROM users WHERE email=%s",
        (data["email"],)
    )

    user = cur.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "message": "User not found"}

    if not user[5]:
        return {"status":"error","message":"Email not verified ❌"}
    
    stored_password = user[3]

    print("ENTERED:", data["password"])
    print("STORED:", stored_password)

    if check_password_hash(stored_password, data["password"]):

        role = "admin" if data["email"] == "kushwah.al2020@gmail.com" else "student"

        return {
            "status": "success",
            "name": user[1],
            "email": user[2],
            "role": role
        }

    else:
        return {"status": "error", "message": "Wrong password"}
    

from flask import redirect

@app.route("/verify/<token>")
def verify(token):

    conn = get_db()
    cur = conn.cursor()

    # 🔍 check token
    cur.execute("SELECT id FROM users WHERE verify_token=%s", (token,))
    user = cur.fetchone()

    if not user:
        return "Invalid or expired link ❌"

    # ✅ mark verified
    cur.execute(
        "UPDATE users SET is_verified=TRUE WHERE verify_token=%s",
        (token,)
    )

    conn.commit()
    conn.close()

    # 🔥 REDIRECT TO LOGIN PAGE
    return redirect("https://roomzy-mocha.vercel.app/login.html?verified=true")

# ================= ADD PG =================
@app.route("/add_pg", methods=["POST"])
def add_pg():

    data = request.json

    conn = get_db()
    cur = conn.cursor()

    owner_id = data.get("owner_id")

    # 🔥 ensure images always list
    images = json.dumps(data.get("images", []))

    cur.execute("""
    INSERT INTO pgs (pg_name, city, rent, description, image, owner_name, owner_phone, images, owner_id)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["pg_name"],
        data["city"],
        data["rent"],
        data["description"],
        data["image"],   # should be "/static/images/pg1.jpg"
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
            f"https://source.unsplash.com/400x300/?room&sig={i}",
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

    base_url = request.host_url.rstrip("/")
    pgs = []

    for r in rows:

        # 🔥 images parse
        try:
            images = json.loads(r[8]) if r[8] else []
        except:
            images = []

        # 🔥 main image fix
        if r[5] and r[5].startswith("/"):
            image = base_url + r[5]
        else:
            image = r[5]

        # 🔥 gallery images fix
        fixed_images = [
            base_url + img if img.startswith("/") else img
            for img in images
        ]

        # fallback
        if not image:
            image = base_url + "/static/images/default.jpg"

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

    base_url = request.host_url.rstrip("/")

    try:
        images = json.loads(row[8]) if row[8] else []
    except:
        images = []

    if row[5] and row[5].startswith("/"):
        image = base_url + row[5]
    else:
        image = row[5]

    fixed_images = [
        base_url + img if img.startswith("/") else img
        for img in images
    ]

    if not image:
        image = base_url + "/static/images/default.jpg"

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


@app.route("/add_test_pg")
def add_test_pg():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO pgs 
        (pg_name, rent, city, owner_name, owner_phone, description, image) 
        VALUES (%s,%s,%s,%s,%s,%s)""",
        (
            "Demo PG",
            6000,
            "Delhi",
            "Avi",
            "9999999999",
            "Nice PG",
            ""
        )
    )

    conn.commit()
    conn.close()

    return "PG Added ✅"


@app.route("/check_tables")
def check_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='pgs'")
    columns = cur.fetchall()

    conn.close()
    return str(columns)

@app.route("/add_bulk_pgs")
def add_bulk_pgs():
    conn = get_db()
    cur = conn.cursor()

    names = [
    "Sunrise PG","Urban Nest","Royal Stay","Green View","City Comfort",
    "Elite Stay","Happy Homes","Skyline PG","Comfort Zone","Dream Stay",
    "Peaceful PG","Golden Nest","Blue Haven","Smart Living","Royal Comfort"
    ]

    for i in range(15):
        cur.execute(
            """INSERT INTO pgs 
            (pg_name, rent, city, owner_name, owner_phone, description, image, images) 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                names[i],
                4000 + i*500,   # rent auto vary
                "Delhi",
                "Owner "+str(i+1),
                "99999999"+str(i).zfill(2),
                "Nice PG with good facilities",

                # main image
                f"https://roomzy-czyc.onrender.com/static/images/pg{i+1}.jpg",

                # multiple images array
                [
                    f"https://roomzy-czyc.onrender.com/static/images/pg{i+1}_1.jpg",
                    f"https://roomzy-czyc.onrender.com/static/images/pg{i+1}_2.jpg",
                    f"https://roomzy-czyc.onrender.com/static/images/pg{i+1}_3.jpg"
                ]
            )
        )

    conn.commit()
    conn.close()

    return "15 PGs Added Successfully ✅🔥"

@app.route("/delete_demo")
def delete_demo():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM pgs WHERE pg_name='Demo PG'")

    conn.commit()
    conn.close()

    return "Demo PG deleted ✅"


@app.route("/create-admin")
def create_admin():
    conn = get_db()
    cur = conn.cursor()

    from werkzeug.security import generate_password_hash

    cur.execute(
        "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
        (
            "Alok Admin",
            "admin@roomzy.com",
            generate_password_hash("admin123"),
            "admin"
        )
    )

    conn.commit()
    conn.close()

    return "Admin created ✅"

@app.route("/all-users", methods=["GET"])
def all_users():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, email FROM users")
    users = cur.fetchall()

    conn.close()

    result = []
    for u in users:
        result.append({
            "name": u[0],
            "email": u[1]
        })

    return result

@app.route("/reset_users")
def reset_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users")
    conn.commit()
    conn.close()
    return "All users deleted"

@app.route("/ocr-test")
def ocr_test():
    try:
        from PIL import Image
        import pytesseract

        img = Image.open("uploads/test.jpg")  # 👈 apni image ka naam
        text = pytesseract.image_to_string(img)

        return {"text": text}

    except Exception as e:
        return {"error": str(e)}
    
@app.route("/update_db")
def update_db():
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("ALTER TABLE users ADD COLUMN profile_data TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN id_card TEXT")
    except:
        pass

    try:
        cur.execute("ALTER TABLE users ADD COLUMN approval_status TEXT DEFAULT 'pending'")
    except:
        pass

    conn.commit()
    conn.close()

    return "DB Updated ✅"

# ================= TEST =================
@app.route("/")
def home():
    return "Backend Running ✅"

@app.route("/test")
def test():
    return " OK 🚀"

if __name__ == "__main__":
    app.run(debug=True)