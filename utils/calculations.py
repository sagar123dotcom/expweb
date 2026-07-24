"""Pure calculation utilities for savings engine and affordability."""

from datetime import datetime
from calendar import monthrange


def _add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, monthrange(year, month)[1])
    return start_date.replace(year=year, month=month, day=day)


def goal_progress(saved_amount, target_amount):
    if target_amount <= 0:
        return 0.0
    return min((saved_amount / target_amount) * 100, 100.0)


def remaining_amount(target_amount, saved_amount):
    return max(target_amount - saved_amount, 0.0)


def months_required(remaining, monthly_free_savings):
    if monthly_free_savings <= 0:
        return None
    return remaining / monthly_free_savings


def months_until_target(target_date_str):
    target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    if target <= today:
        return 0.0
    months = (target.year - today.year) * 12 + (target.month - today.month)
    if target.day < today.day:
        months -= 1
    days_in_month = monthrange(target.year, target.month)[1]
    day_fraction = (target.day - today.day) / days_in_month if months >= 0 else 0
    return max(months + day_fraction, 0.0)


def goal_achievable(months_req, months_until):
    if months_req is None:
        return False
    return months_req <= months_until


def estimated_completion_date(months_req):
    if months_req is None:
        return None
    months_to_add = max(int(months_req + 0.999), 1)
    completion = _add_months(datetime.now().date(), months_to_add)
    return completion.isoformat()


def affordability_months(product_price, monthly_free_savings):
    if monthly_free_savings <= 0:
        return None
    return product_price / monthly_free_savings


def affordability_message(product_name, months_to_afford):
    name = product_name or "this product"
    if months_to_afford is None:
        return (
            "Your monthly free savings is zero or negative. "
            "Increase income or reduce needs before purchasing."
        )
    if months_to_afford <= 1:
        return f"At your current savings rate, you can afford {name} within a month."
    return (
        f"At your current savings rate, you can afford {name} "
        f"in {months_to_afford:.1f} months."
    )


def savings_impact(monthly_free_savings, product_price):
    if monthly_free_savings <= 0 or product_price <= 0:
        return "Purchase would require cutting other spending or increasing income."
    pct = min((product_price / monthly_free_savings) * 100, 999)
    return f"This purchase equals about {pct:.0f}% of one month of free savings."
