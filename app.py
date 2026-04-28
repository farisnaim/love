from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"  # change later!

def get_db():
    return sqlite3.connect("mydatabase.db")

# Create tables
with get_db() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        status TEXT
    )
    """)

# -------- AUTH --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except:
            return "User already exists!"

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/")
        else:
            return "Invalid login!"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------- TASKS --------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()
    conn.close()

    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    task = request.form["task"]

    conn = get_db()
    
    conn.execute(
        "INSERT INTO tasks (user_id, name, status) VALUES (?, ?, ?)",
        (session["user_id"], task, "pending")
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/done/<int:id>")
def done(id):
    conn = get_db()
    conn.execute("UPDATE tasks SET status='done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))