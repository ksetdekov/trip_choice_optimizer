import sqlite3
import os

def show_db_entries(db_file):
    if not os.path.exists(db_file):
        print(f"Database file '{db_file}' does not exist.")
        return

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Get all table names from the database.
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in the database.")
        return

    for table in tables:
        table_name = table[0]
        print(f"Entries in table '{table_name}':")
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        print("-" * 40)

    conn.close()

if __name__ == "__main__":
    db_path = "main_db.db"
    show_db_entries(db_path)