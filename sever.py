from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# tạo database lần đầu
def init_db():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT, password TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY, email TEXT, total TEXT)")
    db.commit()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        db.execute("INSERT INTO users(email,password) VALUES(?,?)",(email,password))
        db.commit()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=? AND password=?",(email,password)).fetchone()
        if user:
            session["user"] = email
            return redirect("/")
    return render_template("login.html")

@app.route("/checkout", methods=["POST"])
def checkout():
    if "user" not in session:
        return redirect("/login")
    total = request.form["total"]
    db = get_db()
    db.execute("INSERT INTO orders(email,total) VALUES(?,?)",(session["user"], total))
    db.commit()
    return render_template("checkout.html", total=total)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

app.run(host="0.0.0.0", port=5000)