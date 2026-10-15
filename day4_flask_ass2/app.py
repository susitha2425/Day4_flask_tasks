import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for


BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("TASKS_DATABASE", BASE_DIR / "tasks.db"))
TASK_PRIORITIES = {"Low", "Medium", "High"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-development-secret-key")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_db_connection()) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                priority TEXT NOT NULL DEFAULT 'Medium'
                    CHECK (priority IN ('Low', 'Medium', 'High'))
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(tasks)")
        }
        if "priority" not in columns:
            connection.execute(
                """
                ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'
                    CHECK (priority IN ('Low', 'Medium', 'High'))
                """
            )


@app.route("/", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("tasks"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "admin" and password == "1234":
            session["logged_in"] = True
            session["username"] = username
            return redirect(url_for("tasks"))
        flash("Incorrect username or password. Please try again.", "danger")

    return render_template("login.html")


@app.get("/tasks")
def tasks():
    if not session.get("logged_in"):
        flash("Please log in to view your tasks.", "warning")
        return redirect(url_for("login"))

    with closing(get_db_connection()) as connection, connection:
        task_rows = connection.execute(
            "SELECT id, title, status, priority FROM tasks ORDER BY id DESC"
        ).fetchall()
    return render_template("tasks.html", tasks=task_rows)


@app.post("/add_task")
def add_task():
    if not session.get("logged_in"):
        return jsonify({"error": "Please log in to add tasks."}), 401

    title = request.form.get("title", "").strip()
    if not title:
        return jsonify({"error": "Task title cannot be empty."}), 400

    priority = request.form.get("priority", "Medium")
    if priority not in TASK_PRIORITIES:
        return jsonify({"error": "Choose a valid task priority."}), 400

    with closing(get_db_connection()) as connection, connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, priority) VALUES (?, ?)",
            (title, priority),
        )
        task_id = cursor.lastrowid

    return jsonify(
        {"id": task_id, "title": title, "status": "Pending", "priority": priority}
    ), 201


@app.post("/edit_task/<int:task_id>")
def edit_task(task_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Please log in to edit tasks."}), 401

    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({"error": "Provide a task title and priority."}), 400

    title = data.get("title", "").strip() if isinstance(data.get("title"), str) else ""
    priority = data.get("priority")
    if not title:
        return jsonify({"error": "Task title cannot be empty."}), 400
    if not isinstance(priority, str) or priority not in TASK_PRIORITIES:
        return jsonify({"error": "Choose a valid task priority."}), 400

    with closing(get_db_connection()) as connection, connection:
        cursor = connection.execute(
            "UPDATE tasks SET title = ?, priority = ? WHERE id = ?",
            (title, priority, task_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found."}), 404
        task = connection.execute(
            "SELECT id, title, status, priority FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return jsonify(dict(task))


@app.post("/delete_task/<int:task_id>")
def delete_task(task_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Please log in to delete tasks."}), 401

    with closing(get_db_connection()) as connection, connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found."}), 404

    return jsonify({"id": task_id, "deleted": True})


@app.post("/toggle_task/<int:task_id>")
def toggle_task(task_id):
    if not session.get("logged_in"):
        return jsonify({"error": "Please log in to update tasks."}), 401

    with closing(get_db_connection()) as connection, connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET status = CASE WHEN status = 'Pending' THEN 'Completed' ELSE 'Pending' END
            WHERE id = ?
            """,
            (task_id,),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found."}), 404

        task = connection.execute(
            "SELECT status FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    return jsonify({"id": task_id, "status": task["status"]})


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


init_db()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
