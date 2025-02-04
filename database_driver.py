import sqlite3
from datetime import datetime

class DatabaseDriver:
    def __init__(self, db_name='main_db.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_optimization (
                optimization_name TEXT,
                change_datetime DATETIME,
                user_id INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_variant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_name TEXT,
                variant_name TEXT,
                change_datetime DATETIME,
                user_id INTEGER
            )
        ''')
        self.conn.commit()

    def add_optimization(self, optimization_name, user_id):
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
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime 
            FROM user_optimization 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
        return self.cursor.fetchall()
    
    def get_all_optimizations(self):
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, user_id
            FROM user_optimization
            '''
        )
        return self.cursor.fetchall()
    
    def add_variant(self, optimization_name, variant_name, user_id):
        change_datetime = datetime.now()
        self.cursor.execute(
            '''
            INSERT INTO optimization_variant (optimization_name, variant_name, change_datetime, user_id)
            VALUES (?, ?, ?, ?)
            ''',
            (optimization_name, variant_name, change_datetime, user_id)
        )
        self.conn.commit()
    
    def get_variants(self, optimization_name, user_id):
        self.cursor.execute(
            '''
            SELECT variant_name, change_datetime
            FROM optimization_variant
            WHERE optimization_name = ? AND user_id = ?
            ''',
            (optimization_name, user_id)
        )
        return self.cursor.fetchall()
    
    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseDriver()
    print("Optimizations:", db.get_all_optimizations())
    db.close()

