import sqlite3

DATABASE = "internflow.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            student_id TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            year INTEGER NOT NULL,
            phone TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            contact_person TEXT,
            phone TEXT,
            email TEXT
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            company_id INTEGER NOT NULL,
            position TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS supervisors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            company_id INTEGER,
            phone TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    """)

    try:
        connection.execute("""
            ALTER TABLE applications
            ADD COLUMN supervisor_id INTEGER
        """)
    except sqlite3.OperationalError:
        pass

        connection.execute("""
        CREATE TABLE IF NOT EXISTS progress_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            supervisor_feedback TEXT,
            feedback_at TIMESTAMP,
            status TEXT DEFAULT 'submitted',
            FOREIGN KEY (application_id) REFERENCES applications (id)
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications (id)
        )
    """)

    connection.execute("""
    CREATE TABLE IF NOT EXISTS final_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER NOT NULL,
        supervisor_id INTEGER NOT NULL,
        technical_skills INTEGER NOT NULL,
        communication INTEGER NOT NULL,
        teamwork INTEGER NOT NULL,
        problem_solving INTEGER NOT NULL,
        professionalism INTEGER NOT NULL,
        overall_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (application_id) REFERENCES applications (id),
        FOREIGN KEY (supervisor_id) REFERENCES supervisors (id)
    )
""")
    
    connection.commit()
    connection.close()