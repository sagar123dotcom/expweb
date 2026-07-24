"""Shared validation helpers for needs and personal goals."""

from datetime import datetime


def parse_positive_float(value, field_name, allow_zero=True):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, f"{field_name} is required"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None, f"{field_name} must be a valid number"
    if amount < 0 or (not allow_zero and amount <= 0):
        return None, f"{field_name} must be greater than {'0' if not allow_zero else 'or equal to 0'}"
    return amount, None


def parse_required_string(value, field_name, max_length=100):
    if value is None:
        return None, f"{field_name} is required"
    text = str(value).strip()
    if not text:
        return None, f"{field_name} is required"
    if len(text) > max_length:
        return None, f"{field_name} must be at most {max_length} characters"
    return text, None


def parse_date(value, field_name, allow_past=True):
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, f"{field_name} is required"
    try:
        parsed = datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, f"{field_name} must be in YYYY-MM-DD format"
    if not allow_past:
        today = datetime.now().date()
        if parsed < today:
            return None, f"{field_name} must be today or in the future"
    return parsed.isoformat(), None


def parse_priority(value, default=3):
    if value is None or (isinstance(value, str) and not str(value).strip()):
        return default, None
    try:
        priority = int(value)
    except (TypeError, ValueError):
        return None, "Priority must be an integer between 1 and 5"
    if priority < 1 or priority > 5:
        return None, "Priority must be between 1 and 5"
    return priority, None
