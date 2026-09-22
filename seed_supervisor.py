import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = "internflow.db"

connection = sqlite3.connect(DATABASE)

name = "InternFlow Supervisor"
email = "supervisor@internflow.com"
password = "super123"

hashed_password = generate_password_hash(password)

cursor = connection.execute("""
    INSERT INTO users
    (name, email, password, role)
    VALUES (?, ?, ?, ?)
""", (
    name,
    email,
    hashed_password,
    "supervisor"
))

user_id = cursor.lastrowid

connection.execute("""
    INSERT INTO supervisors
    (user_id, phone)
    VALUES (?, ?)
""", (
    user_id,
    "+251933333333"
))

connection.commit()
connection.close()

print("Supervisor account created successfully!")