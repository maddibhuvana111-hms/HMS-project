from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"

DATABASE_URL ="postgresql://houses_user:J0zPCJ7niaz8MJpIbQhmlFVzwo3yRDQi@dpg-d8g55ud7vvec739r53vg-a.oregon-postgres.render.com/houses_iarb"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def create_tables():
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
    CREATE TABLE IF NOT EXISTS houses (
        id SERIAL PRIMARY KEY,
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
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
        except:
            conn.rollback()
            return "Username already exists"

        conn.close()
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()

        conn.close()

        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            return "Invalid login"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    username = session["user"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM houses WHERE username=%s", (username,))
    houses = cur.fetchall()

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
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO houses (username, name, location, image) VALUES (%s, %s, %s, %s)",
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
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["house_name"]
        location = request.form["location"]

        cur.execute(
            "UPDATE houses SET name=%s, location=%s WHERE id=%s",
            (name, location, id)
        )
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cur.execute("SELECT * FROM houses WHERE id=%s", (id,))
    house = cur.fetchone()
    conn.close()

    return render_template("edit_house.html", house=house)


@app.route("/delete_house/<int:id>")
def delete_house(id):
    if "user" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM houses WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)