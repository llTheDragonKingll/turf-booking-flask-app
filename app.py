from flask import Flask, jsonify, request, render_template
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

ADMIN_PHONE = "8928486398"


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            is_booked INTEGER DEFAULT 0,
            booked_by TEXT,
            UNIQUE(date, time)
        )
        """)
    
    times = ["5:00 PM","6:00 PM","7:00 PM","8:00 PM"]

    today = datetime.today()

    for i in range(7):

        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")

        for t in times:

            cursor.execute(
                "INSERT OR IGNORE INTO slots(date,time) VALUES(?,?)",
                (date,t)
            )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/admin")
def admin_page():

    phone = request.args.get("phone")

    if phone != ADMIN_PHONE:
        return "Unauthorized"

    return render_template("admin.html")


@app.route("/slots/<date>")
def get_slots(date):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id,time,is_booked FROM slots WHERE date=?",
        (date,)
    )

    rows = cursor.fetchall()
    conn.close()

    result = []

    for row in rows:
        result.append({
            "id":row["id"],
            "time":row["time"],
            "is_booked":row["is_booked"]
        })

    return jsonify(result)


@app.route("/book/<int:slot_id>", methods=["POST"])
def book_slot(slot_id):

    data = request.json
    phone = data.get("phone")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT is_booked FROM slots WHERE id=?",
        (slot_id,)
    )

    slot = cursor.fetchone()

    if slot["is_booked"] == 1:
        return jsonify({"message":"Slot already booked"})

    cursor.execute(
        "UPDATE slots SET is_booked=1, booked_by=? WHERE id=?",
        (phone,slot_id)
    )

    conn.commit()
    conn.close()

    return jsonify({"message":"Slot booked"})


@app.route("/signup", methods=["POST"])
def signup():

    data = request.json

    name = data.get("name")
    phone = data.get("phone")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "INSERT INTO users(name,phone,password) VALUES(?,?,?)",
            (name,phone,password)
        )

        conn.commit()

    except:

        conn.close()
        return jsonify({"message":"User already exists"})

    conn.close()

    return jsonify({"message":"Signup successful"})


@app.route("/login", methods=["POST"])
def login():

    data = request.json

    phone = data.get("phone")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE phone=? AND password=?",
        (phone,password)
    )

    user = cursor.fetchone()

    conn.close()

    if user:

        is_admin = False

        if user["phone"] == ADMIN_PHONE:
            is_admin = True

        return jsonify({
            "message":"Login successful",
            "name":user["name"],
            "phone":user["phone"],
            "admin":is_admin
        })

    return jsonify({"message":"Invalid login"})


@app.route("/admin_data")
def admin_data():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT slots.date, slots.time, slots.is_booked,
           users.name, users.phone
    FROM slots
    LEFT JOIN users
    ON slots.booked_by = users.phone
    ORDER BY slots.date
    """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)