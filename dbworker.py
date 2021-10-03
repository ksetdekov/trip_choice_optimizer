import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

conn.execute("""
CREATE TABLE IF NOT EXISTS "updates" (
    "id"	TEXT,
    "state"	NUMERIC
);
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS "updates" (
    "id"	TEXT,
    "state"	NUMERIC
);
""")


def get_current_state(user_id):
    with Vedis(config.db_file) as db:
        try:
            return db[user_id].decode()
        except KeyError:
            return config.States.S_START.value


def del_state(field):
    with Vedis(config.db_file) as db:
        try:
            del(db[field])
            return True
        except:
            return False


def set_state(user_id, value):
    with Vedis(config.db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            return False


def set_property(id, value):
    with Vedis(config.db_file) as db:
        try:
            db[id] = value
            return True
        except:
            return False
