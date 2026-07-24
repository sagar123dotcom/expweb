"""Database migrations for needs, personal goals, and user preferences."""

FEATURE_MIGRATIONS = [
    """CREATE TABLE IF NOT EXISTS needs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        default_amount REAL NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(user_id, name)
    )""",
    """CREATE INDEX IF NOT EXISTS idx_needs_user_active ON needs(user_id, is_active)""",
    """CREATE TABLE IF NOT EXISTS personal_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        saved_amount REAL NOT NULL DEFAULT 0,
        target_date TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 3,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
    """CREATE INDEX IF NOT EXISTS idx_personal_goals_user_status ON personal_goals(user_id, status)""",
    """CREATE TABLE IF NOT EXISTS user_preferences (
        user_id INTEGER PRIMARY KEY,
        needs_setup_completed INTEGER NOT NULL DEFAULT 0,
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
]


def run_feature_migrations(conn):
    cursor = conn.cursor()
    for sql in FEATURE_MIGRATIONS:
        cursor.execute(sql)
    conn.commit()
