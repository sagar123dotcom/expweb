"""Financial snapshot and savings calculations."""

from datetime import datetime

from utils.calculations import (
    goal_achievable,
    goal_progress,
    estimated_completion_date,
    months_required,
    months_until_target,
    remaining_amount,
    affordability_months,
    affordability_message,
    savings_impact,
)


def _month_key(dt=None):
    return (dt or datetime.now()).strftime("%Y-%m")


def _sum_for_month(conn, user_id, sql_extra, month_key):
    row = conn.execute(
        f"""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = ?
          AND strftime('%Y-%m', date) = ?
          {sql_extra}
        """,
        (user_id, month_key),
    ).fetchone()
    return float(row["total"])


def get_monthly_income(conn, user_id, month_key=None):
    month_key = month_key or _month_key()
    income = _sum_for_month(
        conn, user_id, "AND LOWER(category) = 'income'", month_key
    )
    if income > 0:
        return income, month_key

    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total
        FROM expenses
        WHERE user_id = ? AND LOWER(category) = 'income'
        GROUP BY month
        ORDER BY month DESC
        LIMIT 3
        """,
        (user_id,),
    ).fetchall()
    if not rows:
        return 0.0, month_key
    avg = sum(float(r["total"]) for r in rows) / len(rows)
    return avg, month_key


def get_monthly_expenses(conn, user_id, month_key):
    return _sum_for_month(
        conn, user_id, "AND LOWER(category) != 'income'", month_key
    )


def get_needs_total(conn, user_id):
    row = conn.execute(
        """
        SELECT COALESCE(SUM(default_amount), 0) AS total
        FROM needs
        WHERE user_id = ? AND is_active = 1
        """,
        (user_id,),
    ).fetchone()
    return float(row["total"])


def get_financial_snapshot(conn, user_id):
    monthly_income, month_key = get_monthly_income(conn, user_id)
    monthly_expenses = get_monthly_expenses(conn, user_id, month_key)
    needs_total = get_needs_total(conn, user_id)
    monthly_free_savings = monthly_income - needs_total
    actual_savings = monthly_income - monthly_expenses
    wants_spending = max(monthly_expenses - needs_total, 0.0)

    return {
        "month_key": month_key,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "needs_total": needs_total,
        "monthly_free_savings": monthly_free_savings,
        "actual_savings": actual_savings,
        "wants_spending": wants_spending,
        "needs_income_ratio": (
            (needs_total / monthly_income * 100) if monthly_income > 0 else 0.0
        ),
    }


def project_goal(goal_row, snapshot):
    target = float(goal_row["target_amount"])
    saved = float(goal_row["saved_amount"])
    remaining = remaining_amount(target, saved)
    progress = goal_progress(saved, target)
    months_req = months_required(remaining, snapshot["monthly_free_savings"])
    months_until = months_until_target(goal_row["target_date"])
    achievable = goal_achievable(months_req, months_until)
    completion = estimated_completion_date(months_req)

    if saved >= target:
        status_label = "completed"
    elif achievable:
        status_label = "on_track"
    elif months_req is None:
        status_label = "blocked"
    else:
        status_label = "at_risk"

    return {
        "goal_id": goal_row["id"],
        "goal_name": goal_row["goal_name"],
        "target_amount": target,
        "saved_amount": saved,
        "target_date": goal_row["target_date"],
        "priority": goal_row["priority"],
        "status": goal_row["status"],
        "progress_percent": round(progress, 1),
        "remaining_amount": round(remaining, 2),
        "months_required": round(months_req, 1) if months_req is not None else None,
        "months_until_target": round(months_until, 1),
        "goal_achievable": achievable,
        "estimated_completion_date": completion,
        "goal_status": status_label,
    }


def calculate_affordability(product_name, product_price, snapshot):
    months = affordability_months(product_price, snapshot["monthly_free_savings"])
    return {
        "product_name": product_name,
        "product_price": product_price,
        "months_required": round(months, 1) if months is not None else None,
        "affordability_message": affordability_message(product_name, months),
        "savings_impact": savings_impact(snapshot["monthly_free_savings"], product_price),
        "monthly_free_savings": round(snapshot["monthly_free_savings"], 2),
    }
