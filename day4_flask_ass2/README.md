# Task Manager

A small Flask task manager with a session-based demo login and SQLite storage.

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000/> and sign in with:

- Username: `admin`
- Password: `1234`

The `tasks.db` SQLite database and its `tasks` table are created automatically
when the application starts. The task form submits with JavaScript and updates
the list without reloading the page. Click a task's circle to mark it Completed;
click it again to return it to Pending. You can also edit task titles, assign
Low, Medium, or High priority, and delete tasks. These changes are saved in the
database; deleting a task asks for confirmation.

For deployment, set a strong `SECRET_KEY` environment variable. The included
credentials and fallback secret key are for local demonstration only.
