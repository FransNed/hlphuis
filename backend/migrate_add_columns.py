import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'hlphuis.sqlite')

def has_column(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    cols = [row[1] for row in cur.fetchall()]
    return column in cols

def main():
    if not os.path.exists(DB_PATH):
        print('DB not found at', DB_PATH)
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        # users.name, users.description, users.is_admin
        if not has_column(conn, 'users', 'name'):
            print('Adding users.name')
            conn.execute("ALTER TABLE users ADD COLUMN name TEXT")
        if not has_column(conn, 'users', 'description'):
            print('Adding users.description')
            conn.execute("ALTER TABLE users ADD COLUMN description TEXT")
        if not has_column(conn, 'users', 'is_admin'):
            print('Adding users.is_admin')
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

        # lessons.user_id
        if not has_column(conn, 'lessons', 'user_id'):
            print('Adding lessons.user_id')
            conn.execute("ALTER TABLE lessons ADD COLUMN user_id INTEGER")

        conn.commit()
        print('Migration done')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
