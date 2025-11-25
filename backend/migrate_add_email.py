#!/usr/bin/env python3
import sqlite3
import os

BASE = os.path.abspath(os.path.dirname(__file__))
DB = os.path.join(BASE, 'instance', 'hlphuis.sqlite')

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols

def main():
    if not os.path.exists(DB):
        print('DB not found at', DB)
        return
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    if not column_exists(cur, 'users', 'email'):
        print('Adding email column to users...')
        cur.execute("ALTER TABLE users ADD COLUMN email TEXT")
        conn.commit()
    else:
        print('email column already exists')

    # ensure admin user has an email so they can login
    cur.execute("SELECT id, username, email FROM users WHERE username = 'admin' OR id=1 LIMIT 1")
    row = cur.fetchone()
    if row:
        uid, uname, uemail = row[0], row[1], row[2]
        if not uemail:
            admin_email = 'admin@example.com'
            print('Setting admin email to', admin_email)
            cur.execute('UPDATE users SET email = ? WHERE id = ?', (admin_email, uid))
            conn.commit()
    conn.close()
    print('Migration done')

if __name__ == '__main__':
    main()
