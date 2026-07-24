"""Personal goals CRUD and progress."""

from datetime import datetime

from services.savings_engine import project_goal


def row_to_dict(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "goal_name": row["goal_name"],
        "target_amount": float(row["target_amount"]),
        "saved_amount": float(row["saved_amount"]),
        "target_date": row["target_date"],
        "priority": row["priority"],
        "notes": row["notes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_goals(conn, user_id, status="active"):
    query = "SELECT * FROM personal_goals WHERE user_id = ?"
    params = [user_id]
    if status and status != "all":
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY priority ASC, target_date ASC"
    rows = conn.execute(query, params).fetchall()
    return [row_to_dict(r) for r in rows]


def get_goal(conn, goal_id, user_id):
    row = conn.execute(
        "SELECT * FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    return row_to_dict(row) if row else None


def create_goal(conn, user_id, data):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO personal_goals (
            user_id, goal_name, target_amount, saved_amount,
            target_date, priority, notes, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """,
        (
            user_id,
            data["goal_name"],
            data["target_amount"],
            data.get("saved_amount", 0),
            data["target_date"],
            data.get("priority", 3),
            data.get("notes"),
            now,
            now,
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM personal_goals WHERE id = last_insert_rowid()"
    ).fetchone()
    return row_to_dict(row)


def update_goal(conn, goal_id, user_id, data):
    existing = conn.execute(
        "SELECT * FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    if not existing:
        return None, "Goal not found"

    fields = {
        "goal_name": data.get("goal_name", existing["goal_name"]),
        "target_amount": data.get("target_amount", existing["target_amount"]),
        "saved_amount": data.get("saved_amount", existing["saved_amount"]),
        "target_date": data.get("target_date", existing["target_date"]),
        "priority": data.get("priority", existing["priority"]),
        "notes": data.get("notes", existing["notes"]),
    }
    status = existing["status"]
    if float(fields["saved_amount"]) >= float(fields["target_amount"]):
        status = "completed"

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        UPDATE personal_goals SET
            goal_name = ?, target_amount = ?, saved_amount = ?,
            target_date = ?, priority = ?, notes = ?, status = ?, updated_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            fields["goal_name"],
            fields["target_amount"],
            fields["saved_amount"],
            fields["target_date"],
            fields["priority"],
            fields["notes"],
            status,
            now,
            goal_id,
            user_id,
        ),
    )
    conn.commit()
    return get_goal(conn, goal_id, user_id), None


def archive_goal(conn, goal_id, user_id):
    existing = conn.execute(
        "SELECT id FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    if not existing:
        return None, "Goal not found"
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE personal_goals SET status = 'archived', updated_at = ? WHERE id = ? AND user_id = ?",
        (now, goal_id, user_id),
    )
    conn.commit()
    return get_goal(conn, goal_id, user_id), None


def delete_goal(conn, goal_id, user_id):
    existing = conn.execute(
        "SELECT id FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    if not existing:
        return False, "Goal not found"
    conn.execute(
        "DELETE FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    )
    conn.commit()
    return True, None


def get_goal_with_projection(conn, goal_id, user_id, snapshot):
    row = conn.execute(
        "SELECT * FROM personal_goals WHERE id = ? AND user_id = ?",
        (goal_id, user_id),
    ).fetchone()
    if not row:
        return None
    result = row_to_dict(row)
    result["projection"] = project_goal(row, snapshot)
    return result


def list_goals_with_projections(conn, user_id, snapshot, status="active"):
    rows = conn.execute(
        """
        SELECT * FROM personal_goals
        WHERE user_id = ? AND status = ?
        ORDER BY priority ASC, target_date ASC
        """,
        (user_id, status),
    ).fetchall()
    goals = []
    for row in rows:
        item = row_to_dict(row)
        item["projection"] = project_goal(row, snapshot)
        goals.append(item)
    return goals
