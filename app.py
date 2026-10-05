from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3

app = Flask(__name__)

app.secret_key = "studymate-secret-key"


def init_db():
    conn = sqlite3.connect("database.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            topic_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        topic_id INTEGER NOT NULL,
        study_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        duration INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (topic_id) REFERENCES topics(id)
    )
""")

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered"

        conn.close()

        return "Registration successful!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    subject_count = conn.execute(
    "SELECT COUNT(*) FROM subjects WHERE user_id = ?",
    (session["user_id"],)
    ).fetchone()[0]

    topic_count = conn.execute(
    "SELECT COUNT(*) FROM topics WHERE user_id = ?",
    (session["user_id"],)
    ).fetchone()[0]

    completed_count = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Completed'",
    (session["user_id"],)
    ).fetchone()[0]

    pending_count = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Pending'",
    (session["user_id"],)
    ).fetchone()[0]

    if pending_count > 0:
        recommendation = f"You have {pending_count} pending task(s). Focus on completing them today!"
    elif completed_count > 0:
        recommendation = "Great job! You have completed all your current tasks."
    else:
        recommendation = "Add your first task to start tracking your study progress."
    conn.close()

    return render_template(
    "dashboard.html",
    name=session["user_name"],
    subject_count=subject_count,
    topic_count=topic_count,
    completed_count=completed_count,
    pending_count=pending_count,
    recommendation=recommendation
)

@app.route("/subjects", methods=["GET", "POST"])
def subjects():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        subject_name = request.form["subject_name"]

        conn = sqlite3.connect("database.db")

        conn.execute(
            "INSERT INTO subjects (user_id, subject_name) VALUES (?, ?)",
            (session["user_id"], subject_name)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("subjects"))

    conn = sqlite3.connect("database.db")

    subjects = conn.execute(
        "SELECT id, subject_name FROM subjects WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template("subjects.html", subjects=subjects)
@app.route("/edit_subject/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        subject_name = request.form["subject_name"]

        conn.execute(
            "UPDATE subjects SET subject_name = ? WHERE id = ? AND user_id = ?",
            (subject_name, subject_id, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect(url_for("subjects"))

    subject = conn.execute(
        "SELECT id, subject_name FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, session["user_id"])
    ).fetchone()

    conn.close()

    if subject is None:
        return "Subject not found"

    return render_template("edit_subject.html", subject=subject)
@app.route("/delete_subject/<int:subject_id>")
def delete_subject(subject_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    conn.execute(
        "DELETE FROM subjects WHERE id = ? AND user_id = ?",
        (subject_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("subjects"))

@app.route("/topics", methods=["GET", "POST"])
def topics():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        topic_name = request.form["topic_name"]

        conn.execute(
            "INSERT INTO topics (user_id, subject_id, topic_name) VALUES (?, ?, ?)",
            (session["user_id"], subject_id, topic_name)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("topics"))

    subjects = conn.execute(
        "SELECT id, subject_name FROM subjects WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    topics = conn.execute("""
        SELECT topics.id, topics.subject_id, subjects.subject_name, topics.topic_name
        FROM topics
        JOIN subjects ON topics.subject_id = subjects.id
        WHERE topics.user_id = ?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "topics.html",
        subjects=subjects,
        topics=topics
    )

@app.route("/edit_topic/<int:topic_id>", methods=["GET", "POST"])
def edit_topic(topic_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        topic_name = request.form["topic_name"]

        conn.execute(
            "UPDATE topics SET topic_name = ? WHERE id = ? AND user_id = ?",
            (topic_name, topic_id, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect(url_for("topics"))

    topic = conn.execute("""
        SELECT topics.id, topics.subject_id, subjects.subject_name, topics.topic_name
        FROM topics
        JOIN subjects ON topics.subject_id = subjects.id
        WHERE topics.id = ? AND topics.user_id = ?
    """, (topic_id, session["user_id"])).fetchone()

    conn.close()

    if topic is None:
        return "Topic not found"

    return render_template("edit_topic.html", topic=topic)
@app.route("/delete_topic/<int:topic_id>")
def delete_topic(topic_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    conn.execute(
        "DELETE FROM topics WHERE id = ? AND user_id = ?",
        (topic_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("topics"))
@app.route("/tasks", methods=["GET", "POST"])
def tasks():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        task_name = request.form["task_name"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        conn.execute(
            """
            INSERT INTO tasks
            (user_id, subject_id, task_name, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["user_id"],
                subject_id,
                task_name,
                due_date,
                priority,
                "Pending"
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("tasks"))

    subjects = conn.execute(
        "SELECT id, subject_name FROM subjects WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()

    tasks = conn.execute("""
        SELECT
            tasks.id,
            tasks.subject_id,
            subjects.subject_name,
            tasks.task_name,
            tasks.due_date,
            tasks.priority,
            tasks.status
        FROM tasks
        JOIN subjects ON tasks.subject_id = subjects.id
        WHERE tasks.user_id = ?
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template(
        "tasks.html",
        subjects=subjects,
        tasks=tasks
    )
@app.route("/complete_task/<int:task_id>")
def complete_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    conn.execute(
        "UPDATE tasks SET status = 'Completed' WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))  
@app.route("/edit_task/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        task_name = request.form["task_name"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        conn.execute(
            """
            UPDATE tasks
            SET task_name = ?, due_date = ?, priority = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                task_name,
                due_date,
                priority,
                task_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("tasks"))

    task = conn.execute(
        """
        SELECT id, task_name, due_date, priority, status
        FROM tasks
        WHERE id = ? AND user_id = ?
        """,
        (task_id, session["user_id"])
    ).fetchone()

    conn.close()

    if task is None:
        return "Task not found"

    return render_template("edit_task.html", task=task)
@app.route("/delete_task/<int:task_id>")
def delete_task(task_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    conn.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("tasks"))
@app.route("/study-planner", methods=["GET", "POST"])
def study_planner():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        topic_id = request.form["topic_id"]
        study_date = request.form["study_date"]
        start_time = request.form["start_time"]
        duration = request.form["duration"]

        existing_plan = conn.execute(
            """
            SELECT id FROM study_plans
            WHERE user_id = ?
            AND subject_id = ?
            AND topic_id = ?
            AND study_date = ?
            AND start_time = ?
            AND duration = ?
            """,
            (
                session["user_id"],
                subject_id,
                topic_id,
                study_date,
                start_time,
                duration
            )
        ).fetchone()

        if existing_plan is None:

            conn.execute(
                """
                INSERT INTO study_plans
                (user_id, subject_id, topic_id, study_date, start_time, duration)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    subject_id,
                    topic_id,
                    study_date,
                    start_time,
                    duration
                )
            )

            conn.commit()

        conn.close()

        return redirect(url_for("study_planner"))

    subjects = conn.execute(
        """
        SELECT id, subject_name
        FROM subjects
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    topics = conn.execute(
        """
        SELECT id, subject_id, topic_name
        FROM topics
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    study_plans = conn.execute(
        """
        SELECT
            study_plans.id,
            subjects.subject_name,
            topics.topic_name,
            study_plans.study_date,
            study_plans.start_time,
            study_plans.duration
        FROM study_plans
        JOIN subjects
            ON study_plans.subject_id = subjects.id
        JOIN topics
            ON study_plans.topic_id = topics.id
        WHERE study_plans.user_id = ?
        ORDER BY study_plans.study_date, study_plans.start_time
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "study_planner.html",
        subjects=subjects,
        topics=topics,
        study_plans=study_plans
    )
@app.route("/edit_study_plan/<int:plan_id>", methods=["GET", "POST"])
def edit_study_plan(plan_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    if request.method == "POST":

        subject_id = request.form["subject_id"]
        topic_id = request.form["topic_id"]
        study_date = request.form["study_date"]
        start_time = request.form["start_time"]
        duration = request.form["duration"]

        conn.execute(
            """
            UPDATE study_plans
            SET subject_id = ?, topic_id = ?, study_date = ?,
                start_time = ?, duration = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                subject_id,
                topic_id,
                study_date,
                start_time,
                duration,
                plan_id,
                session["user_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("study_planner"))

    plan = conn.execute(
        """
        SELECT id, subject_id, topic_id, study_date, start_time, duration
        FROM study_plans
        WHERE id = ? AND user_id = ?
        """,
        (plan_id, session["user_id"])
    ).fetchone()

    subjects = conn.execute(
        """
        SELECT id, subject_name
        FROM subjects
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    topics = conn.execute(
        """
        SELECT id, subject_id, topic_name
        FROM topics
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    if plan is None:
        return "Study plan not found"

    return render_template(
        "edit_study_plan.html",
        plan=plan,
        subjects=subjects,
        topics=topics
    )
@app.route("/delete_study_plan/<int:plan_id>", methods=["POST"])
def delete_study_plan(plan_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")

    conn.execute(
        "DELETE FROM study_plans WHERE id = ? AND user_id = ?",
        (plan_id, session["user_id"])
    )

    conn.commit()
    conn.close()

    return redirect(url_for("study_planner"))
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run()