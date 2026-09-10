import sqlite3

DATABASE = "internflow.db"

connection = sqlite3.connect(DATABASE)

companies = [
    (
        "Ethio Telecom",
        "Addis Ababa",
        "HR Department",
        "+251911000000",
        "hr@ethiotelecom.et"
    ),
    (
        "Ethiopian Airlines",
        "Bole, Addis Ababa",
        "HR Department",
        "+251911111111",
        "hr@ethiopianairlines.com"
    ),
    (
        "Tech Solutions Ethiopia",
        "Addis Ababa",
        "Software Engineering Team",
        "+251922222222",
        "info@techsolutions.et"
    )
]

for company in companies:

    connection.execute("""
        INSERT INTO companies
        (name, address, contact_person, phone, email)
        VALUES (?, ?, ?, ?, ?)
    """, company)

connection.commit()
connection.close()

print("Companies added successfully!")