from flask import Flask, render_template, request, redirect, session
import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change later

# ---------------- DATABASE ----------------
def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# Create tables (run once on startup)
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        name TEXT,
        status TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()

# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )

            conn.commit()
            cur.close()
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
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s",
            (username,)
        )

        user = cur.fetchone()

        cur.close()
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


# ---------------- TASKS ----------------
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM tasks WHERE user_id=%s",
        (session["user_id"],)
    )

    tasks = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("index.html", tasks=tasks)


@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")

    task = request.form["task"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO tasks (user_id, name, status) VALUES (%s, %s, %s)",
        (session["user_id"], task, "pending")
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


@app.route("/done/<int:id>")
def done(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE tasks SET status='done' WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM tasks WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))