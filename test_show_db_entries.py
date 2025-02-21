import os
import sqlite3
import tempfile
import unittest
import io
from contextlib import redirect_stdout

from show_db_entries import show_db_entries  # Import the function to test

class TestShowDBEntries(unittest.TestCase):
    def test_db_file_not_exist(self):
        # Use a filename that does not exist
        fake_db = "non_existent_db.db"
        f = io.StringIO()
        with redirect_stdout(f):
            show_db_entries(fake_db)
        output = f.getvalue()
        self.assertIn(f"Database file '{fake_db}' does not exist.", output)

    def test_no_tables_in_db(self):
        # Create a temporary database file with no tables
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            temp_db_path = tmp.name

        try:
            # Create an empty SQLite database (no tables are created)
            conn = sqlite3.connect(temp_db_path)
            conn.close()

            f = io.StringIO()
            with redirect_stdout(f):
                show_db_entries(temp_db_path)
            output = f.getvalue()
            self.assertIn("No tables found in the database.", output)
        finally:
            os.remove(temp_db_path)

    def test_with_tables_and_entries(self):
        # Create a temporary database with one table and some entries
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            temp_db_path = tmp.name

        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            # Create a test table and insert some rows
            cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            cursor.execute("INSERT INTO test_table (name) VALUES ('Alice')")
            cursor.execute("INSERT INTO test_table (name) VALUES ('Bob')")
            conn.commit()
            conn.close()

            f = io.StringIO()
            with redirect_stdout(f):
                show_db_entries(temp_db_path)
            output = f.getvalue()
            # Check that the table name and entries are in the output
            self.assertIn("Entries in table 'test_table':", output)
            self.assertIn("(1, 'Alice')", output)
            self.assertIn("(2, 'Bob')", output)
        finally:
            os.remove(temp_db_path)

if __name__ == "__main__":
    unittest.main()