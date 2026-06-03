from flask import Flask, render_template, request, redirect, session
import sqlite3
import os  

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def get_db():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS houses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        name TEXT,
        location TEXT,
        image TEXT
    )
    """)

    conn.commit()
    conn.close()


create_tables()


@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if c.fetchone():
            error = "Username already exists"
        else:
            c.execute("INSERT INTO users VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")

        conn.close()

    return render_template("register.html", error=error)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid credentials"

    return render_template("login.html")



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]
    search = request.form.get("search")

    conn = get_db()
    c = conn.cursor()

    if search:
        c.execute("""
        SELECT * FROM houses 
        WHERE username=? AND (name LIKE ? OR location LIKE ?)
        """, (username, f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM houses WHERE username=?", (username,))

    houses = c.fetchall()
    conn.close()

    return render_template("dashboard.html", houses=houses)

@app.route("/add_house", methods=["GET", "POST"])
def add_house():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        name = request.form["house_name"]
        location = request.form["location"]
        image = request.files["image"]

        filename = ""
        if image and image.filename != "":
            filename = image.filename
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO houses (username, name, location, image) VALUES (?, ?, ?, ?)",
            (session["user"], name, location, filename)
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_house.html")


@app.route("/edit_house/<int:id>", methods=["GET", "POST"])
def edit_house(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM houses WHERE id=?", (id,))
    house = c.fetchone()

    if not house:
        return "House not found"

    if request.method == "POST":
        name = request.form["house_name"]
        location = request.form["location"]

        c.execute("UPDATE houses SET name=?, location=? WHERE id=?", (name, location, id))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    conn.close()
    return render_template("edit_house.html", house=house)


@app.route("/delete_house/<int:id>")
def delete_house(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM houses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)