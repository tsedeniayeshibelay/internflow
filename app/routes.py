from flask import render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from app.database import get_db_connection


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        student_id = request.form["student_id"]
        department = request.form["department"]
        year = request.form["year"]
        phone = request.form["phone"]

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()

        cursor = connection.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (name, email, hashed_password, "student"))

        user_id = cursor.lastrowid

        connection.execute("""
            INSERT INTO students
            (user_id, student_id, department, year, phone)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, student_id, department, year, phone))

        connection.commit()
        connection.close()

        return redirect(url_for("home"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "coordinator":
                return redirect(url_for("coordinator_dashboard"))

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    student = connection.execute("""
        SELECT users.name, users.email,
               students.student_id,
               students.department,
               students.year,
               students.phone
        FROM users
        JOIN students
        ON users.id = students.user_id
        WHERE users.id = ?
    """, (session["user_id"],)).fetchone()

    application = connection.execute("""
        SELECT applications.*,
               companies.name AS company_name
        FROM applications
        JOIN students
        ON applications.student_id = students.id
        JOIN companies
        ON applications.company_id = companies.id
        WHERE students.user_id = ?
        ORDER BY applications.created_at DESC
        LIMIT 1
    """, (session["user_id"],)).fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        student=student,
        application=application
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route("/apply", methods=["GET", "POST"])
def apply_internship():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        company_id = request.form["company_id"]
        position = request.form["position"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        description = request.form["description"]

        connection = get_db_connection()

        student = connection.execute(
            "SELECT id FROM students WHERE user_id = ?",
            (session["user_id"],)
        ).fetchone()

        connection.execute("""
            INSERT INTO applications
            (student_id, company_id, position, start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            student["id"],
            company_id,
            position,
            start_date,
            end_date,
            description
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    companies = connection.execute(
        "SELECT * FROM companies"
    ).fetchall()

    connection.close()

    return render_template(
        "apply.html",
        companies=companies
    )

@app.route("/coordinator")
def coordinator_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "coordinator":
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    applications = connection.execute("""
        SELECT
            applications.id,
            applications.position,
            applications.start_date,
            applications.end_date,
            applications.description,
            applications.status,
            applications.created_at,
            users.name AS student_name,
            students.student_id,
            students.department,
            companies.name AS company_name
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        JOIN companies
            ON applications.company_id = companies.id
        ORDER BY applications.created_at DESC
    """).fetchall()

    connection.close()

    return render_template(
        "coordinator.html",
        applications=applications
    )

@app.route("/coordinator/application/<int:application_id>")
def review_application(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "coordinator":
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    application = connection.execute("""
        SELECT
            applications.*,
            users.name AS student_name,
            users.email AS student_email,
            students.student_id,
            students.department,
            students.year,
            students.phone,
            companies.name AS company_name,
            companies.address AS company_address,
            companies.contact_person,
            companies.phone AS company_phone,
            companies.email AS company_email
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        JOIN companies
            ON applications.company_id = companies.id
        WHERE applications.id = ?
    """, (application_id,)).fetchone()

    connection.close()

    if not application:
        return "Application not found"

    return render_template(
        "review_application.html",
        application=application
    )

@app.route(
    "/coordinator/application/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "coordinator":
        return redirect(url_for("dashboard"))

    status = request.form["status"]

    if status not in ["approved", "rejected"]:
        return "Invalid status"

    connection = get_db_connection()

    connection.execute("""
        UPDATE applications
        SET status = ?
        WHERE id = ?
    """, (status, application_id))

    connection.commit()
    connection.close()

    return redirect(url_for("coordinator_dashboard"))