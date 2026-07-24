"""Shared SQLite connection helpers."""

import sqlite3

DB_PATH = "expenses.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
