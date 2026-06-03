from flask import Flask, render_template, request, redirect, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = "secret123"


DATABASE_URL = "your_copied_url_here"

def get_db():
    return psycopg2.connect(DATABASE_URL)

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

        
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            conn.close()
            return "Username already exists"

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
        )

        conn.commit()
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

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM houses WHERE username=%s", (session["user"],))
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

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO houses (username, name, location) VALUES (%s, %s, %s)",
            (session["user"], name, location)
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_house.html")

@app.route("/delete_house/<int:id>")
def delete_house(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM houses WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/edit_house/<int:id>", methods=["GET", "POST"])
def edit_house(id):
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


if __name__ == "__main__":
    app.run(debug=True)