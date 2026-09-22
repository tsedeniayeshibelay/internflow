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

            if user["role"] == "supervisor":
                return redirect(url_for("supervisor_dashboard"))

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    student = connection.execute("""
        SELECT
            users.name,
            users.email,
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
        SELECT
            applications.*,
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

    reports = []

    if application:

        reports = connection.execute("""
            SELECT
                id,
                title,
                content,
                submitted_at,
                supervisor_feedback,
                feedback_at,
                status
            FROM progress_reports
            WHERE application_id = ?
            ORDER BY submitted_at DESC
        """, (application["id"],)).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        student=student,
        application=application,
        reports=reports
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

    # Get the selected status from the URL.
    # If no status is provided, show all applications.
    selected_status = request.args.get("status", "all")

    connection = get_db_connection()

    # Base query for applications
    query = """
        SELECT
            applications.id,
            applications.position,
            applications.start_date,
            applications.end_date,
            applications.description,
            applications.status,
            applications.supervisor_id,
            applications.created_at,

            users.name AS student_name,
            students.student_id,
            students.department,

            companies.name AS company_name,

            supervisor_users.name AS supervisor_name

        FROM applications

        JOIN students
            ON applications.student_id = students.id

        JOIN users
            ON students.user_id = users.id

        JOIN companies
            ON applications.company_id = companies.id

        LEFT JOIN supervisors
            ON applications.supervisor_id = supervisors.id

        LEFT JOIN users AS supervisor_users
            ON supervisors.user_id = supervisor_users.id
    """

    # Parameters used by the SQL query
    parameters = ()

    # Apply a status filter if one was selected
    if selected_status in ["pending", "approved", "rejected"]:

        query += """
            WHERE applications.status = ?
        """

        parameters = (selected_status,)

    query += """
        ORDER BY applications.created_at DESC
    """

    applications = connection.execute(
        query,
        parameters
    ).fetchall()

    # Dashboard statistics

    total_applications = connection.execute("""
        SELECT COUNT(*) AS count
        FROM applications
    """).fetchone()["count"]

    approved_applications = connection.execute("""
        SELECT COUNT(*) AS count
        FROM applications
        WHERE status = 'approved'
    """).fetchone()["count"]

    pending_applications = connection.execute("""
        SELECT COUNT(*) AS count
        FROM applications
        WHERE status = 'pending'
    """).fetchone()["count"]

    rejected_applications = connection.execute("""
        SELECT COUNT(*) AS count
        FROM applications
        WHERE status = 'rejected'
    """).fetchone()["count"]

    connection.close()

    return render_template(
        "coordinator.html",
        applications=applications,
        total_applications=total_applications,
        approved_applications=approved_applications,
        pending_applications=pending_applications,
        rejected_applications=rejected_applications,
        selected_status=selected_status
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
            companies.email AS company_email,

            supervisor_users.name AS supervisor_name

        FROM applications

        JOIN students
            ON applications.student_id = students.id

        JOIN users
            ON students.user_id = users.id

        JOIN companies
            ON applications.company_id = companies.id

        LEFT JOIN supervisors
            ON applications.supervisor_id = supervisors.id

        LEFT JOIN users AS supervisor_users
            ON supervisors.user_id = supervisor_users.id

        WHERE applications.id = ?
    """, (application_id,)).fetchone()

    supervisors = connection.execute("""
        SELECT
            supervisors.id,
            users.name,
            users.email,
            supervisors.phone
        FROM supervisors
        JOIN users
            ON supervisors.user_id = users.id
        ORDER BY users.name
    """).fetchall()

    connection.close()

    if not application:
        return "Application not found"

    return render_template(
        "review_application.html",
        application=application,
        supervisors=supervisors
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

@app.route("/supervisor")
def supervisor_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "supervisor":
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    supervisor = connection.execute("""
        SELECT
            users.name,
            users.email,
            supervisors.id AS supervisor_id,
            supervisors.phone
        FROM users
        JOIN supervisors
            ON users.id = supervisors.user_id
        WHERE users.id = ?
    """, (session["user_id"],)).fetchone()

    applications = connection.execute("""
        SELECT
            applications.id,
            applications.position,
            applications.start_date,
            applications.end_date,
            applications.status,
            users.name AS student_name,
            students.student_id,
            companies.name AS company_name
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        JOIN companies
            ON applications.company_id = companies.id
        WHERE applications.supervisor_id = ?
        ORDER BY applications.created_at DESC
    """, (supervisor["supervisor_id"],)).fetchall()

    reports = connection.execute("""
        SELECT
            progress_reports.id,
            progress_reports.title,
            progress_reports.content,
            progress_reports.submitted_at,
            progress_reports.supervisor_feedback,
            progress_reports.feedback_at,
            progress_reports.status,
            users.name AS student_name,
            students.student_id,
            applications.position,
            companies.name AS company_name
        FROM progress_reports
        JOIN applications
            ON progress_reports.application_id = applications.id
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        JOIN companies
            ON applications.company_id = companies.id
        WHERE applications.supervisor_id = ?
        ORDER BY progress_reports.submitted_at DESC
    """, (supervisor["supervisor_id"],)).fetchall()

    connection.close()

    return render_template(
        "supervisor.html",
        supervisor=supervisor,
        applications=applications,
        reports=reports
    )

@app.route(
    "/coordinator/application/<int:application_id>/assign-supervisor",
    methods=["POST"]
)
def assign_supervisor(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "coordinator":
        return redirect(url_for("dashboard"))

    supervisor_id = request.form["supervisor_id"]

    connection = get_db_connection()

    supervisor = connection.execute("""
        SELECT id
        FROM supervisors
        WHERE id = ?
    """, (supervisor_id,)).fetchone()

    if not supervisor:
        connection.close()
        return "Supervisor not found"

    application = connection.execute("""
        SELECT id, status
        FROM applications
        WHERE id = ?
    """, (application_id,)).fetchone()

    if not application:
        connection.close()
        return "Application not found"

    if application["status"] != "approved":
        connection.close()
        return "Only approved applications can be assigned to a supervisor"

    connection.execute("""
        UPDATE applications
        SET supervisor_id = ?
        WHERE id = ?
    """, (supervisor_id, application_id))

    connection.commit()
    connection.close()

    return redirect(
        url_for(
            "review_application",
            application_id=application_id
        )
    )

@app.route(
    "/student/application/<int:application_id>/report",
    methods=["GET", "POST"]
)
def submit_report(application_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    application = connection.execute("""
        SELECT
            applications.*,
            companies.name AS company_name
        FROM applications
        JOIN students
            ON applications.student_id = students.id
        JOIN companies
            ON applications.company_id = companies.id
        WHERE applications.id = ?
        AND students.user_id = ?
    """, (
        application_id,
        session["user_id"]
    )).fetchone()

    if not application:
        connection.close()
        return "Application not found"

    if application["status"] != "approved":
        connection.close()
        return "You can only submit reports for approved applications"

    if request.method == "POST":

        title = request.form["title"]
        content = request.form["content"]

        connection.execute("""
            INSERT INTO progress_reports
            (application_id, title, content)
            VALUES (?, ?, ?)
        """, (
            application_id,
            title,
            content
        ))

        connection.commit()
        connection.close()

        return redirect(url_for("dashboard"))

    connection.close()

    return render_template(
        "submit_report.html",
        application=application
    )

@app.route(
    "/supervisor/report/<int:report_id>",
    methods=["GET", "POST"]
)
def review_report(report_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "supervisor":
        return redirect(url_for("dashboard"))

    connection = get_db_connection()

    supervisor = connection.execute("""
        SELECT id
        FROM supervisors
        WHERE user_id = ?
    """, (session["user_id"],)).fetchone()

    if not supervisor:
        connection.close()
        return "Supervisor profile not found"

    report = connection.execute("""
        SELECT
            progress_reports.*,
            users.name AS student_name,
            students.student_id,
            companies.name AS company_name,
            applications.position
        FROM progress_reports
        JOIN applications
            ON progress_reports.application_id = applications.id
        JOIN students
            ON applications.student_id = students.id
        JOIN users
            ON students.user_id = users.id
        JOIN companies
            ON applications.company_id = companies.id
        WHERE progress_reports.id = ?
        AND applications.supervisor_id = ?
    """, (
        report_id,
        supervisor["id"]
    )).fetchone()

    if not report:
        connection.close()
        return "Report not found or you are not assigned to this internship"

    if request.method == "POST":

        feedback = request.form["feedback"]

        connection.execute("""
            UPDATE progress_reports
            SET
                supervisor_feedback = ?,
                feedback_at = CURRENT_TIMESTAMP,
                status = 'reviewed'
            WHERE id = ?
        """, (
            feedback,
            report_id
        ))

        connection.commit()
        connection.close()

        return redirect(
            url_for(
                "review_report",
                report_id=report_id
            )
        )

    connection.close()

    return render_template(
        "review_report.html",
        report=report
    )