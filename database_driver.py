import sqlite3
from datetime import datetime

class DatabaseDriver:
    def __init__(self, db_name='main_db.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")  # Enable foreign key enforcement
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL UNIQUE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_optimization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_name TEXT NOT NULL,
                change_datetime DATETIME,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE            
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_variant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                change_datetime DATETIME,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                option_value NUMERIC,
                change_datetime DATETIME,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE,
                FOREIGN KEY (variant_id) REFERENCES optimization_variant(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def add_optimization(self, optimization_name, telegram_user_id):
        # Ensure the user exists or insert them
        self.cursor.execute(
            "SELECT id FROM users WHERE telegram_user_id = ?",
            (telegram_user_id,)
        )
        user_row = self.cursor.fetchone()
        if user_row is None:
            self.cursor.execute(
                "INSERT INTO users (telegram_user_id) VALUES (?)",
                (telegram_user_id,)
            )
            self.conn.commit()
            user_id = self.cursor.lastrowid
        else:
            user_id = user_row[0]

        change_datetime = datetime.now()
        self.cursor.execute(
            '''
            INSERT INTO user_optimization (optimization_name, change_datetime, user_id)
            VALUES (?, ?, ?)
            ''',
            (optimization_name, change_datetime, user_id)
        )
        self.conn.commit()

    def get_optimizations(self, user_id):
        # get user id from user table

        self.cursor.execute(
            "SELECT id FROM users WHERE telegram_user_id = ?",
            (user_id,)
        )
        internal_user_id = self.cursor.fetchone()

        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime 
            FROM user_optimization 
            WHERE user_id = ?
            ''',
            (internal_user_id,)
        )
        return self.cursor.fetchall()
    
    def get_all_optimizations(self):
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, telegram_user_id
            FROM user_optimization
            join users on user_optimization.user_id = users.id
            '''
        )
        return self.cursor.fetchall()
    
    def add_variant(self, optimization_name, variant_name, user_id):
        '''
        user_optimization

                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                change_datetime DATETIME,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE 
        '''
        change_datetime = datetime.now()
        # get if of optimization based on optimization_name
        self.cursor.execute(
            '''
            SELECT id, user_id
            FROM user_optimization
            WHERE optimization_name = ? AND user_id = ?
            ''',
            (optimization_name, user_id)
        )
        optimization_id, internal_user_id = self.cursor.fetchone()


        self.cursor.execute(
            '''
            INSERT INTO optimization_variant (optimization_id, variant_name, change_datetime, user_id)
            VALUES (?, ?, ?, ?)
            ''',
            (optimization_id, variant_name, change_datetime, internal_user_id)
        )
        self.conn.commit()
    
    def get_variants(self, optimization_name, user_id):
        self.cursor.execute(
            '''
            SELECT id, user_id
            FROM user_optimization
            WHERE optimization_name = ? AND user_id = ?
            ''',
            (optimization_name, user_id)
        )
        optimization_id, internal_user_id = self.cursor.fetchone()
        self.cursor.execute(
            '''
            SELECT variant_name, change_datetime
            FROM optimization_variant
            WHERE optimization_id = ? AND user_id = ?
            ''',
            (optimization_id, internal_user_id)
        )
        return self.cursor.fetchall()
    
    def remove_optimization(self, optimization_name, user_id):
        """
        Remove a specific optimization by its name and user ID,
        and also remove all associated variants and samples.
        """
        self.cursor.execute(
            '''
            SELECT id, user_id
            FROM user_optimization
            WHERE optimization_name = ? AND user_id = ?
            ''',
            (optimization_name, user_id)
        )
        optimization_id, internal_user_id = self.cursor.fetchone()
        self.cursor.execute(
            '''
            DELETE FROM user_optimization
            WHERE id = ? AND user_id = ?
            ''',
            (optimization_id, internal_user_id)
        )
        self.conn.commit()
    
    def remove_variant(self, optimization_name, variant_name, user_id):
        """
        Remove a specific variant from an optimization.
        """
        # Also remove any samples associated with the variant.
        self.cursor.execute(
            '''
            DELETE FROM optimization_samples
            WHERE optimization_name = ? AND variant_name = ? AND user_id = ?
            ''',
            (optimization_name, variant_name, user_id)
        )
        # Remove the variant itself.
        self.cursor.execute(
            '''
            DELETE FROM optimization_variant
            WHERE optimization_name = ? AND variant_name = ? AND user_id = ?
            ''',
            (optimization_name, variant_name, user_id)
        )
        self.conn.commit()
    
    def add_option(self, optimization_name, variant_name, option_value, user_id):
        """
        Add a sample (option value) for a given optimization.
        """
        change_datetime = datetime.now()
        self.cursor.execute(
            '''
            INSERT INTO optimization_samples (optimization_name, variant_name, option_value, change_datetime, user_id)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (optimization_name, variant_name, option_value, change_datetime, user_id)
        )
        self.conn.commit()
    
    def get_all_samples_for_optimization(self, user_id, optimization_name):
        """
        Retrieve all samples (observations) for the given user and optimization_name.
        Expected tuple format: (optimization_name, option_value, change_datetime)
        """
        self.cursor.execute(
            '''
            SELECT optimization_name, variant_name, option_value, change_datetime
            FROM optimization_samples
            WHERE user_id = ? AND optimization_name = ?
            ''',
            (user_id, optimization_name)
        )
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseDriver()
    print("Optimizations:", db.get_all_optimizations())
    db.close()

