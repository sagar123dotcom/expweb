"""Shared transaction date filtering for dashboard and planning queries."""

from datetime import datetime


WEEKDAY_VALUES = {
    "sunday": "0",
    "monday": "1",
    "tuesday": "2",
    "wednesday": "3",
    "thursday": "4",
    "friday": "5",
    "saturday": "6",
}


def _valid_date(value, field_name):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None, f"{field_name} must be in YYYY-MM-DD format"
    return value, None


def _valid_month(value):
    try:
        datetime.strptime(value, "%Y-%m")
    except (TypeError, ValueError):
        return None, "Month must be in YYYY-MM format"
    return value, None


def _valid_year(value):
    if not value or not value.isdigit() or len(value) != 4:
        return None, "Year must be in YYYY format"
    return value, None


def build_date_conditions(args, column="date"):
    """Return SQL conditions and parameters for a date-filter argument mapping."""
    mode = (args.get("date_filter") or "").strip().lower()
    conditions = []
    params = []

    if mode in ("", "none"):
        return conditions, params, None

    if mode == "day":
        day = (args.get("filter_day") or "").strip().lower()
        if day not in WEEKDAY_VALUES:
            return [], [], "Select a valid weekday"
        conditions.append(f"strftime('%w', {column}) = ?")
        params.append(WEEKDAY_VALUES[day])
        return conditions, params, None

    if mode == "specific_date":
        date_value, error = _valid_date(
            (args.get("specific_date") or "").strip(), "Specific date"
        )
        if error:
            return [], [], error
        conditions.append(f"{column} = ?")
        params.append(date_value)
        return conditions, params, None

    if mode == "month":
        month_value, error = _valid_month((args.get("filter_month_date") or "").strip())
        if error:
            return [], [], error
        conditions.append(f"strftime('%Y-%m', {column}) = ?")
        params.append(month_value)
        return conditions, params, None

    if mode == "quarter":
        quarter = (args.get("filter_quarter") or "").strip()
        if len(quarter) != 7 or quarter[4] != "-" or quarter[5:] not in ("Q1", "Q2", "Q3", "Q4"):
            return [], [], "Quarter must use YYYY-Q1, YYYY-Q2, YYYY-Q3, or YYYY-Q4"
        year = quarter[:4]
        if not year.isdigit():
            return [], [], "Quarter must use YYYY-Qn format"
        quarter_number = int(quarter[6])
        start_month = (quarter_number - 1) * 3 + 1
        start_date = f"{year}-{start_month:02d}-01"
        if quarter_number == 4:
            end_date = f"{int(year) + 1}-01-01"
        else:
            end_date = f"{year}-{start_month + 3:02d}-01"
        conditions.append(f"{column} >= ? AND {column} < ?")
        params.extend([start_date, end_date])
        return conditions, params, None

    if mode == "year":
        year, error = _valid_year((args.get("filter_year_date") or "").strip())
        if error:
            return [], [], error
        conditions.append(f"strftime('%Y', {column}) = ?")
        params.append(year)
        return conditions, params, None

    if mode == "custom":
        start_date, start_error = _valid_date(
            (args.get("custom_start") or "").strip(), "Custom start date"
        )
        end_date, end_error = _valid_date(
            (args.get("custom_end") or "").strip(), "Custom end date"
        )
        if start_error:
            return [], [], start_error
        if end_error:
            return [], [], end_error
        if start_date > end_date:
            return [], [], "Custom start date cannot be after the end date"
        conditions.append(f"{column} >= ? AND {column} <= ?")
        params.extend([start_date, end_date])
        return conditions, params, None

    return [], [], "Select a valid date filter"


def has_date_filter(args):
    return bool((args.get("date_filter") or "").strip())
