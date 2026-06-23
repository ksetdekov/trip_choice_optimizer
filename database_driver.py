import sqlite3


class DatabaseDriver:
    def __init__(self, db_name='main_db.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id INTEGER PRIMARY KEY
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_optimization (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_name TEXT NOT NULL,
                change_datetime TEXT DEFAULT (datetime('now')),
                telegram_user_id INTEGER,
                metric_type TEXT DEFAULT 'number',
                objective TEXT DEFAULT 'minimize',
                recency_days INTEGER DEFAULT 360,
                rho REAL DEFAULT 1.0,
                FOREIGN KEY (telegram_user_id) REFERENCES users(telegram_user_id) ON DELETE CASCADE
            )
        ''')

        self._ensure_user_optimization_columns()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimization_variant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                optimization_id INTEGER NOT NULL,
                variant_name TEXT NOT NULL,
                change_datetime TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE
            )
        ''')

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

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                telegram_user_id INTEGER PRIMARY KEY,
                active_optimization_id INTEGER,
                FOREIGN KEY (telegram_user_id) REFERENCES users(telegram_user_id) ON DELETE CASCADE,
                FOREIGN KEY (active_optimization_id) REFERENCES user_optimization(id) ON DELETE SET NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_recommendation (
                telegram_user_id INTEGER PRIMARY KEY,
                optimization_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                recommended_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (telegram_user_id) REFERENCES users(telegram_user_id) ON DELETE CASCADE,
                FOREIGN KEY (optimization_id) REFERENCES user_optimization(id) ON DELETE CASCADE,
                FOREIGN KEY (variant_id) REFERENCES optimization_variant(id) ON DELETE CASCADE
            )
        ''')

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

    def _ensure_user_optimization_columns(self):
        self.cursor.execute("PRAGMA table_info(user_optimization)")
        existing_columns = {row[1] for row in self.cursor.fetchall()}
        columns = {
            'metric_type': "TEXT DEFAULT 'number'",
            'objective': "TEXT DEFAULT 'minimize'",
            'recency_days': "INTEGER DEFAULT 360",
            'rho': "REAL DEFAULT 1.0",
        }
        for column_name, column_definition in columns.items():
            if column_name not in existing_columns:
                self.cursor.execute(
                    f"ALTER TABLE user_optimization ADD COLUMN {column_name} {column_definition}"
                )

    def _ensure_user(self, telegram_user_id):
        self.cursor.execute(
            "SELECT telegram_user_id FROM users WHERE telegram_user_id = ?",
            (telegram_user_id,)
        )
        if self.cursor.fetchone() is None:
            self.cursor.execute(
                "INSERT INTO users (telegram_user_id) VALUES (?)",
                (telegram_user_id,)
            )
            self.conn.commit()

    def add_optimization(
        self,
        optimization_name,
        telegram_user_id,
        metric_type='number',
        objective='minimize',
        recency_days=360,
        rho=1.0,
    ):
        self._ensure_user(telegram_user_id)

        self.cursor.execute(
            '''
            INSERT INTO user_optimization (
                optimization_name,
                telegram_user_id,
                metric_type,
                objective,
                recency_days,
                rho
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (
                optimization_name,
                telegram_user_id,
                metric_type,
                objective,
                int(recency_days),
                float(rho),
            )
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_optimizations(self, user_id):
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, id
            FROM user_optimization
            WHERE telegram_user_id = ?
            ORDER BY id
            ''',
            (user_id,)
        )
        return self.cursor.fetchall()

    def get_all_optimizations(self):
        self.cursor.execute(
            '''
            SELECT optimization_name, change_datetime, telegram_user_id
            FROM user_optimization
            ORDER BY id
            '''
        )
        return self.cursor.fetchall()

    def get_optimization_config(self, optimization_id, user_id=None):
        params = [optimization_id]
        user_filter = ""
        if user_id is not None:
            user_filter = " AND telegram_user_id = ?"
            params.append(user_id)

        self.cursor.execute(
            f'''
            SELECT
                id,
                optimization_name,
                change_datetime,
                telegram_user_id,
                metric_type,
                objective,
                recency_days,
                rho
            FROM user_optimization
            WHERE id = ?{user_filter}
            ''',
            tuple(params)
        )
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            'id': row[0],
            'optimization_name': row[1],
            'change_datetime': row[2],
            'telegram_user_id': row[3],
            'metric_type': row[4],
            'objective': row[5],
            'recency_days': row[6],
            'rho': row[7],
        }

    def update_optimization_config(
        self,
        optimization_id,
        metric_type=None,
        objective=None,
        recency_days=None,
        rho=None,
    ):
        updates = []
        params = []
        if metric_type is not None:
            updates.append("metric_type = ?")
            params.append(metric_type)
        if objective is not None:
            updates.append("objective = ?")
            params.append(objective)
        if recency_days is not None:
            updates.append("recency_days = ?")
            params.append(int(recency_days))
        if rho is not None:
            updates.append("rho = ?")
            params.append(float(rho))

        if not updates:
            return

        params.append(optimization_id)
        self.cursor.execute(
            f'''
            UPDATE user_optimization
            SET {", ".join(updates)}
            WHERE id = ?
            ''',
            tuple(params)
        )
        self.conn.commit()

    def add_variant(self, optimization_name, variant_name, user_id):
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        return self.add_variant_by_id(optimization_id, variant_name)

    def add_variant_by_id(self, optimization_id, variant_name):
        self.cursor.execute(
            '''
            INSERT INTO optimization_variant (optimization_id, variant_name)
            VALUES (?, ?)
            ''',
            (optimization_id, variant_name)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_variants(self, optimization_name, user_id):
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        self.cursor.execute(
            '''
            SELECT variant_name, change_datetime
            FROM optimization_variant
            WHERE optimization_id = ?
            ORDER BY id
            ''',
            (optimization_id,)
        )
        return self.cursor.fetchall()

    def get_variants_by_optimization_id(self, optimization_id):
        self.cursor.execute(
            '''
            SELECT id, variant_name, change_datetime
            FROM optimization_variant
            WHERE optimization_id = ?
            ORDER BY id
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
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError(f"No optimization '{optimization_name}' found for user {user_id}.")
        return int(row[0])

    def get_optimization_name(self, optimization_id) -> str:
        self.cursor.execute(
            '''
            SELECT optimization_name
            FROM user_optimization
            WHERE id = ?
            ''',
            (optimization_id,)
        )
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError(f"No optimization with id '{optimization_id}' found.")
        return row[0]

    def get_variant(self, variant_id, optimization_id=None):
        params = [variant_id]
        optimization_filter = ""
        if optimization_id is not None:
            optimization_filter = " AND optimization_id = ?"
            params.append(optimization_id)

        self.cursor.execute(
            f'''
            SELECT id, optimization_id, variant_name, change_datetime
            FROM optimization_variant
            WHERE id = ?{optimization_filter}
            ''',
            tuple(params)
        )
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            'id': row[0],
            'optimization_id': row[1],
            'variant_name': row[2],
            'change_datetime': row[3],
        }

    def remove_optimization(self, optimization_name, user_id):
        self.cursor.execute(
            '''
            SELECT id, telegram_user_id
            FROM user_optimization
            WHERE optimization_name = ? AND telegram_user_id = ?
            ''',
            (optimization_name, user_id)
        )
        row = self.cursor.fetchone()
        if row is None:
            return

        optimization_id, telegram_user_id = row
        self.cursor.execute(
            '''
            DELETE FROM user_optimization
            WHERE id = ? AND telegram_user_id = ?
            ''',
            (optimization_id, telegram_user_id)
        )
        self.conn.commit()

    def remove_variant(self, optimization_name, variant_name, user_id):
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        self.cursor.execute(
            '''
            DELETE FROM optimization_variant
            WHERE optimization_id = ? AND variant_name = ?
            ''',
            (optimization_id, variant_name)
        )
        self.conn.commit()

    def remove_variant_by_id(self, optimization_id, variant_id):
        self.cursor.execute(
            '''
            DELETE FROM optimization_variant
            WHERE optimization_id = ? AND id = ?
            ''',
            (optimization_id, variant_id)
        )
        self.conn.commit()

    def add_option(self, optimization_name, variant_name, option_value, user_id, change_datetime=None):
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)

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

        return self.add_sample_by_ids(
            optimization_id=optimization_id,
            variant_id=variant_id,
            option_value=option_value,
            change_datetime=change_datetime,
        )

    def add_sample_by_ids(self, optimization_id, variant_id, option_value, change_datetime=None):
        if change_datetime is None:
            self.cursor.execute(
                '''
                INSERT INTO optimization_samples (optimization_id, variant_id, option_value)
                VALUES (?, ?, ?)
                ''',
                (optimization_id, variant_id, option_value)
            )
        else:
            self.cursor.execute(
                '''
                INSERT INTO optimization_samples (
                    optimization_id,
                    variant_id,
                    option_value,
                    change_datetime
                )
                VALUES (?, ?, ?, ?)
                ''',
                (optimization_id, variant_id, option_value, change_datetime)
            )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_samples_for_optimization(self, user_id, optimization_name):
        optimization_id = self.retrieve_optimization_id(optimization_name, user_id)
        self.cursor.execute(
            '''
            SELECT
                u.optimization_name,
                v.variant_name,
                s.option_value,
                s.change_datetime
            FROM optimization_samples AS s
            JOIN optimization_variant AS v
                ON s.variant_id = v.id
            JOIN user_optimization AS u
                ON s.optimization_id = u.id
            WHERE s.optimization_id = ?
            ORDER BY s.change_datetime, s.id
            ''',
            (optimization_id,)
        )
        return self.cursor.fetchall()

    def get_samples_for_optimization_id(self, optimization_id):
        self.cursor.execute(
            '''
            SELECT
                s.id,
                s.optimization_id,
                s.variant_id,
                v.variant_name,
                s.option_value,
                s.change_datetime
            FROM optimization_samples AS s
            JOIN optimization_variant AS v
                ON s.variant_id = v.id
            WHERE s.optimization_id = ?
            ORDER BY s.change_datetime, s.id
            ''',
            (optimization_id,)
        )
        return self.cursor.fetchall()

    def set_active_optimization(self, telegram_user_id, optimization_id):
        self._ensure_user(telegram_user_id)
        self.cursor.execute(
            '''
            INSERT INTO user_settings (telegram_user_id, active_optimization_id)
            VALUES (?, ?)
            ON CONFLICT(telegram_user_id)
            DO UPDATE SET active_optimization_id = excluded.active_optimization_id
            ''',
            (telegram_user_id, optimization_id)
        )
        self.conn.commit()

    def get_active_optimization_id(self, telegram_user_id):
        self.cursor.execute(
            '''
            SELECT active_optimization_id
            FROM user_settings
            WHERE telegram_user_id = ?
            ''',
            (telegram_user_id,)
        )
        row = self.cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def set_pending_recommendation(self, telegram_user_id, optimization_id, variant_id):
        self._ensure_user(telegram_user_id)
        self.cursor.execute(
            '''
            INSERT INTO pending_recommendation (
                telegram_user_id,
                optimization_id,
                variant_id,
                recommended_at
            )
            VALUES (?, ?, ?, datetime('now'))
            ON CONFLICT(telegram_user_id)
            DO UPDATE SET
                optimization_id = excluded.optimization_id,
                variant_id = excluded.variant_id,
                recommended_at = datetime('now')
            ''',
            (telegram_user_id, optimization_id, variant_id)
        )
        self.conn.commit()

    def get_pending_recommendation(self, telegram_user_id):
        self.cursor.execute(
            '''
            SELECT
                p.optimization_id,
                p.variant_id,
                p.recommended_at,
                u.optimization_name,
                v.variant_name
            FROM pending_recommendation AS p
            JOIN user_optimization AS u
                ON p.optimization_id = u.id
            JOIN optimization_variant AS v
                ON p.variant_id = v.id
            WHERE p.telegram_user_id = ?
            ''',
            (telegram_user_id,)
        )
        row = self.cursor.fetchone()
        if row is None:
            return None
        return {
            'optimization_id': row[0],
            'variant_id': row[1],
            'recommended_at': row[2],
            'optimization_name': row[3],
            'variant_name': row[4],
        }

    def clear_pending_recommendation(self, telegram_user_id):
        self.cursor.execute(
            '''
            DELETE FROM pending_recommendation
            WHERE telegram_user_id = ?
            ''',
            (telegram_user_id,)
        )
        self.conn.commit()

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    db = DatabaseDriver()
    print("Optimizations:", db.get_all_optimizations())
    db.close()
