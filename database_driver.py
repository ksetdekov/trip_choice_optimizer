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
        # Users table using telegram_user_id as the primary key
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id INTEGER PRIMARY KEY
            )
        ''')

        # User Optimization table linked to users table by telegram_user_id
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_optimization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_name TEXT NOT NULL,
                change_datetime TEXT DEFAULT (datetime('now')),
                telegram_user_id INTEGER,
                FOREIGN KEY (telegram_user_id) REFERENCES users(telegram_user_id) ON DELETE CASCADE            
            )
        ''')

        # Optimization Variant table linked to user_optimization (user info can be derived via join)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_variant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                change_datetime TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE
            )
        ''')

        # Optimization Samples table linked to user_optimization and optimization_variant
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                option_value NUMERIC,
                change_datetime TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE,
                FOREIGN KEY (variant_id) REFERENCES optimization_variant(id) ON DELETE CASCADE
            )
        ''')

        # Add indexes on foreign key columns for improved query performance
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_optimization_user ON user_optimization(telegram_user_id)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_optimization_variant_opt ON optimization_variant(optimization_id)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_optimization_samples_opt ON optimization_samples(optimization_id)
        ''')
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_optimization_samples_variant ON optimization_samples(variant_id)
        ''')

        self.conn.commit()


    def add_optimization(self, optimization_name, telegram_user_id):
        # Ensure the user exists or insert them
        self.cursor.execute(
            "SELECT telegram_user_id FROM users WHERE telegram_user_id = ?",
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

        self.cursor.execute(
            '''
            INSERT INTO user_optimization (optimization_name, telegram_user_id)
            VALUES (?, ?)
            ''',
            (optimization_name, user_id)
        )
        self.conn.commit()

    def get_optimizations(self, user_id):
        # Get all optimizations for a specific user by telegram_user_id

        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, id 
            FROM user_optimization 
            WHERE telegram_user_id = ?
            ''',
            (user_id,)
        )
        return self.cursor.fetchall()
    
    def get_all_optimizations(self):
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, telegram_user_id
            FROM user_optimization
            '''
        )
        return self.cursor.fetchall()
    
    def add_variant(self, optimization_name, variant_name, user_id):
        '''
        optimization_variant and user_optimization tables are used
        to store the optimization name and its variants.
        '''
        # get optimization_id from optimization_name and user_id
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        print(optimization_id)

        self.cursor.execute(
            '''
            INSERT INTO optimization_variant (optimization_id, variant_name)
            VALUES (?, ?)
            ''',
            (optimization_id, variant_name)
        )
        self.conn.commit()
    
    def get_variants(self, optimization_name, user_id):
        # get optimization_id from optimization_name and user_id
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        self.cursor.execute(
            '''
            SELECT variant_name, change_datetime
            FROM optimization_variant
            WHERE optimization_id = ?
            ''',
            (optimization_id,)
        )
        return self.cursor.fetchall()

    def retrieve_optimization_id(self, optimization_name, user_id):
        self.cursor.execute(
            '''
            SELECT id
            FROM user_optimization
            WHERE optimization_name = ? AND telegram_user_id = ?
            ''',
            (optimization_name, user_id)
        )
        optimization_id = int(self.cursor.fetchone()[0])
        return optimization_id

    def get_optimization_name(self, optimization_id) -> str:
        """
        Retrieve the optimization name based on the optimization_id.
        """
        self.cursor.execute(
            '''
            SELECT optimization_name
            FROM user_optimization
            WHERE id = ?
            ''',
            (optimization_id,)
        )
        optimization_name = self.cursor.fetchone()[0]
        return optimization_name
    
    def remove_optimization(self, optimization_name, user_id):
        """
        Remove a specific optimization by its name and user ID,
        and also remove all associated variants and samples.
        """
        self.cursor.execute(
            '''
            SELECT id, telegram_user_id
            FROM user_optimization
            WHERE optimization_name = ? AND telegram_user_id = ?
            ''',
            (optimization_name, user_id)
        )
        optimization_id, telegram_user_id = self.cursor.fetchone()
        self.cursor.execute(
            '''
            DELETE FROM user_optimization
            WHERE id = ? AND telegram_user_id = ?
            ''',
            (optimization_id, telegram_user_id)
        )
        self.conn.commit()
    
    def remove_variant(self, optimization_name, variant_name, user_id):
        """
        Remove a specific variant from an optimization.
        """
        # Find optimization by user and optimization name
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)

        # Remove the variant itself.
        self.cursor.execute(
            '''
            DELETE FROM optimization_variant
            WHERE optimization_id = ? AND variant_name = ?
            ''',
            (optimization_id, variant_name)
        )
        self.conn.commit()
    
    def add_option(self, optimization_name, variant_name, option_value, user_id):
        """
        Add a sample (option value) for a given optimization and variant.
        Uses the normalized schema:
          - Retrieves optimization_id from user_optimization using optimization_name and user_id.
          - Retrieves variant_id from optimization_variant using optimization_id and variant_name.
          - Inserts a record into optimization_samples with optimization_id, variant_id,
            the provided option_value, and the current datetime.
        """
        # Retrieve the optimization id
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        
        # Retrieve the variant_id from optimization_variant
        self.cursor.execute(
            '''
            SELECT id 
            FROM optimization_variant
            WHERE optimization_id = ? AND variant_name = ?
            ''',
            (optimization_id, variant_name)
        )
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError(f"No variant '{variant_name}' found for optimization '{optimization_name}'.")
        variant_id = int(row[0])
        
        # Insert into optimization_samples table with optimization_id, variant_id, option_value.
        self.cursor.execute(
            '''
            INSERT INTO optimization_samples (optimization_id, variant_id, option_value)
            VALUES (?, ?, ?)
            ''',
            (optimization_id, variant_id, option_value)
        )
        self.conn.commit()
    
    def get_all_samples_for_optimization(self, user_id, optimization_name):
        """
        Retrieve all samples (observations) for the given user and optimization_name.
        Expected tuple format: (optimization_name, option_value, change_datetime)
        returns a list of tuples.
        Each tuple contains:
        optimization_name, variant_name, option_value, change_datetime
        """
        # get optimization_id from optimization_name and user_id
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        

        self.cursor.execute(
            '''
            SELECT 
            u.optimization_name, 
            v.variant_name, 
            s.option_value, 
            s.change_datetime
            FROM 
            optimization_samples as s
            JOIN optimization_variant as v
            on s.variant_id=v.id
            join user_optimization u
            on s.optimization_id=u.id
            WHERE 
            s.optimization_id = ?
            ''',
            (optimization_id, )
        )
        return self.cursor.fetchall() # optimization_name, variant_name, option_value, change_datetime
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseDriver()
    print("Optimizations:", db.get_all_optimizations())
    db.close()

