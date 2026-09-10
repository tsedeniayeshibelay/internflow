import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "internflow.db"

connection = sqlite3.connect(DATABASE)

name = "InternFlow Coordinator"
email = "coordinator@internflow.com"
password = "admin123"

hashed_password = generate_password_hash(password)

connection.execute("""
    INSERT INTO users
    (name, email, password, role)
    VALUES (?, ?, ?, ?)
""", (
    name,
    email,
    hashed_password,
    "coordinator"
))

connection.commit()
connection.close()

print("Coordinator account created successfully!")