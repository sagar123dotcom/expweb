"""Smart financial insights."""

from utils.calculations import months_required, remaining_amount


def needs_income_insight(snapshot):
    ratio = snapshot["needs_income_ratio"]
    income = snapshot["monthly_income"]
    if income <= 0:
        return None
    return {
        "type": "needs_ratio",
        "severity": "warning" if ratio > 50 else "info",
        "message": f"Needs consume {ratio:.0f}% of your income.",
    }


def free_savings_insight(snapshot):
    if snapshot["monthly_free_savings"] >= 0:
        return None
    return {
        "type": "negative_free_savings",
        "severity": "danger",
        "message": (
            "Your needs exceed your monthly income. "
            "Review mandatory expenses or increase income."
        ),
    }


def goal_achievability_insight(projection):
    if projection["goal_status"] == "completed":
        return {
            "type": "goal_completed",
            "severity": "success",
            "message": f"Congratulations! You've reached your {projection['goal_name']} goal.",
        }
    if projection["goal_achievable"]:
        return {
            "type": "goal_on_track",
            "severity": "success",
            "message": "Current goal is achievable before target date.",
        }
    if projection["months_required"] is None:
        return {
            "type": "goal_blocked",
            "severity": "danger",
            "message": (
                f"Goal '{projection['goal_name']}' needs more monthly free savings to be reachable."
            ),
        }
    return {
        "type": "goal_at_risk",
        "severity": "warning",
        "message": (
            f"Goal '{projection['goal_name']}' may miss its target date "
            f"at your current savings rate."
        ),
    }


def wants_reduction_insight(snapshot, top_goal_row):
    if not top_goal_row:
        return None
    wants = snapshot["wants_spending"]
    free = snapshot["monthly_free_savings"]
    if wants <= 0 or free <= 0:
        return None

    remaining = remaining_amount(
        float(top_goal_row["target_amount"]),
        float(top_goal_row["saved_amount"]),
    )
    current_months = months_required(remaining, free)
    improved_free = free + wants * 0.2
    improved_months = months_required(remaining, improved_free)
    if current_months is None or improved_months is None:
        return None

    months_saved = current_months - improved_months
    if months_saved < 0.5:
        return None

    return {
        "type": "wants_reduction",
        "severity": "info",
        "message": (
            f"Reducing wants spending by 20% could help you achieve your "
            f"{top_goal_row['goal_name']} goal {months_saved:.0f} months earlier."
        ),
    }


def actual_vs_free_insight(snapshot):
    actual = snapshot["actual_savings"]
    free = snapshot["monthly_free_savings"]
    if snapshot["monthly_income"] <= 0:
        return None
    if actual >= free:
        return {
            "type": "actual_savings",
            "severity": "success",
            "message": (
                f"You're saving ₹{actual:.0f} this month — "
                f"above your free savings baseline of ₹{free:.0f}."
            ),
        }
    gap = free - actual
    if gap <= 0:
        return None
    return {
        "type": "actual_savings",
        "severity": "warning",
        "message": (
            f"Discretionary spending is ₹{gap:.0f} above your free savings target this month."
        ),
    }


def generate_insights(snapshot, goals_with_projections):
    insights = []

    for fn in (needs_income_insight, free_savings_insight, actual_vs_free_insight):
        item = fn(snapshot)
        if item:
            insights.append(item)

    active = [g for g in goals_with_projections if g["status"] == "active"]
    if active:
        top = min(active, key=lambda g: (g["priority"], g["target_date"]))
        top_row = {
            "goal_name": top["goal_name"],
            "target_amount": top["target_amount"],
            "saved_amount": top["saved_amount"],
        }
        wants_tip = wants_reduction_insight(snapshot, top_row)
        if wants_tip:
            insights.append(wants_tip)
        if "projection" in top:
            insights.append(goal_achievability_insight(top["projection"]))

    return insights
