import sqlite3

def save_all_to_db(departments, deputies, images_data):
    print("\n--- ЗАВДАННЯ 6: Збереження даних у базу SQLite ---")
    conn = sqlite3.connect("uzhgorod_rada.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, url TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Deputies (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, department_url TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Images (
        id INTEGER PRIMARY KEY AUTOINCREMENT, person_name TEXT, url TEXT, local_path TEXT
    )""")

    cursor.execute("DELETE FROM Departments")
    cursor.execute("DELETE FROM Deputies")
    cursor.execute("DELETE FROM Images")

    for dep in departments:
        cursor.execute("INSERT INTO Departments (name, url) VALUES (?, ?)", (dep['name'], dep['url']))

    for person in deputies:
        cursor.execute("INSERT INTO Deputies (name, department_url) VALUES (?, ?)", (person['name'], person['department_url']))

    for img in images_data:
        cursor.execute("INSERT INTO Images (person_name, url, local_path) VALUES (?, ?, ?)", (img['name'], img['url'], img['local_path']))

    conn.commit()
    conn.close()
    print("Дані успішно перезаписані в 'uzhgorod_rada.db'.")