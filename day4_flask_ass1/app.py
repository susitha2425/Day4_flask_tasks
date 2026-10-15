
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Used to protect the login session.
# Change this to a secure random secret for real projects.
app.secret_key = "change-this-to-a-random-secret-key"

DATABASE = Path(__file__).resolve().parent / "users.db"


# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create the users table automatically
def create_table():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_table()


# Registration page
@app.route("/")
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Check whether all fields are filled
        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return render_template("register.html")

        # Basic email validation
        if "@" not in email or "." not in email.split("@")[-1]:
            flash("Please enter a valid email address.", "danger")
            return render_template("register.html")

        # Password validation
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return render_template("register.html")

        # Hash the password before saving it
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            flash("This email is already registered. Please log in.", "danger")
            return render_template("register.html")

        finally:
            conn.close()

        # Redirect after successful registration
        return redirect(url_for("success"))

    return render_template("register.html")


# Registration success page
@app.route("/success")
def success():
    return render_template("success.html")


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required!", "danger")
            return render_template("login.html")

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        # Check the email and password
        if user and check_password_hash(user["password"], password):

            session.clear()
            session["user_id"] = user["id"]

            return redirect(url_for("profile"))

        flash("Invalid email or password!", "danger")

    return render_template("login.html")


# Logged-in user's profile
@app.route("/profile")
def profile():

    # Do not allow access without login
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()

    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    if user is None:
        session.clear()
        flash("Please log in again.", "warning")
        return redirect(url_for("login"))

    return render_template("profile.html", user=user)


# Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
