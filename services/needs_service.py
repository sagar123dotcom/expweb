"""Needs CRUD and first-time setup."""

from datetime import datetime

from constants.default_needs import DEFAULT_NEED_TEMPLATES


def row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "default_amount": float(row["default_amount"]),
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_templates():
    return DEFAULT_NEED_TEMPLATES


def list_needs(conn, user_id, active_only=False):
    query = "SELECT * FROM needs WHERE user_id = ?"
    params = [user_id]
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY name ASC"
    rows = conn.execute(query, params).fetchall()
    return [row_to_dict(r) for r in rows]


def get_need(conn, need_id, user_id):
    row = conn.execute(
        "SELECT * FROM needs WHERE id = ? AND user_id = ?",
        (need_id, user_id),
    ).fetchone()
    return row_to_dict(row) if row else None


def create_need(conn, user_id, name, default_amount):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            """
            INSERT INTO needs (user_id, name, default_amount, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (user_id, name, default_amount, now, now),
        )
        conn.commit()
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return None, "A need with this name already exists"
        raise
    row = conn.execute(
        "SELECT * FROM needs WHERE user_id = ? AND name = ?",
        (user_id, name),
    ).fetchone()
    return row_to_dict(row), None


def setup_needs(conn, user_id, selected):
    created = []
    for item in selected:
        need, err = create_need(
            conn, user_id, item["name"], item.get("default_amount", 0)
        )
        if need:
            created.append(need)
        elif err and "already exists" not in err:
            return None, err
    mark_setup_completed(conn, user_id)
    return created, None


def update_need(conn, need_id, user_id, name=None, default_amount=None):
    existing = conn.execute(
        "SELECT * FROM needs WHERE id = ? AND user_id = ?",
        (need_id, user_id),
    ).fetchone()
    if not existing:
        return None, "Need not found"

    new_name = name if name is not None else existing["name"]
    new_amount = (
        default_amount if default_amount is not None else existing["default_amount"]
    )
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            """
            UPDATE needs SET name = ?, default_amount = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (new_name, new_amount, now, need_id, user_id),
        )
        conn.commit()
    except Exception as exc:
        if "UNIQUE" in str(exc):
            return None, "A need with this name already exists"
        raise
    return get_need(conn, need_id, user_id), None


def toggle_need(conn, need_id, user_id, is_active):
    existing = conn.execute(
        "SELECT id FROM needs WHERE id = ? AND user_id = ?",
        (need_id, user_id),
    ).fetchone()
    if not existing:
        return None, "Need not found"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE needs SET is_active = ?, updated_at = ? WHERE id = ? AND user_id = ?",
        (1 if is_active else 0, now, need_id, user_id),
    )
    conn.commit()
    return get_need(conn, need_id, user_id), None


def delete_need(conn, need_id, user_id):
    existing = conn.execute(
        "SELECT id FROM needs WHERE id = ? AND user_id = ?",
        (need_id, user_id),
    ).fetchone()
    if not existing:
        return False, "Need not found"
    conn.execute("DELETE FROM needs WHERE id = ? AND user_id = ?", (need_id, user_id))
    conn.commit()
    return True, None


def get_setup_status(conn, user_id):
    row = conn.execute(
        "SELECT needs_setup_completed FROM user_preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    needs_count = conn.execute(
        "SELECT COUNT(*) AS c FROM needs WHERE user_id = ?",
        (user_id,),
    ).fetchone()["c"]
    completed = bool(row["needs_setup_completed"]) if row else False
    return {
        "needs_setup_completed": completed,
        "needs_count": needs_count,
        "show_setup": needs_count == 0 and not completed,
    }


def mark_setup_completed(conn, user_id):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO user_preferences (user_id, needs_setup_completed, updated_at)
        VALUES (?, 1, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            needs_setup_completed = 1,
            updated_at = excluded.updated_at
        """,
        (user_id, now),
    )
    conn.commit()
