import sqlite3
import os
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), 'college.db')

def get_db():
    """
    Returns an active database connection.
    If called within a Flask application context, it stores the connection in 'g'.
    If called outside (e.g. CLI initialization scripts), it creates a standalone connection.
    """
    try:
        # Check if we are inside a Flask application context
        if 'db' not in g:
            g.db = sqlite3.connect(DATABASE)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    except RuntimeError:
        # Outside Flask application context
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def close_db(e=None):
    """
    Closes the database connection at the end of the Flask request lifecycle.
    """
    db = g.pop('db', None) if 'g' in globals() else None
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """
    Helper function to query the database easily with parameterized queries.
    Prevents SQL injection vulnerabilities.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """
    Helper function to execute INSERT, UPDATE, DELETE queries with auto-commit.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    last_row_id = cur.lastrowid
    cur.close()
    return last_row_id

