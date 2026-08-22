"""REST API for needs, goals, savings, affordability, and insights."""

from flask import Blueprint, jsonify, request, session

from services import needs_service, goals_service, insights_service
from services.savings_engine import (
    get_financial_snapshot,
    calculate_affordability,
    project_goal,
)
from utils.validators import (
    parse_positive_float,
    parse_required_string,
    parse_date,
    parse_priority,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")

DATE_FILTER_KEYS = (
    "date_filter",
    "filter_day",
    "specific_date",
    "filter_month_date",
    "filter_quarter",
    "filter_year_date",
    "custom_start",
    "custom_end",
)


def _get_db():
    from db.connection import get_db

    return get_db()


def _user_id():
    return session.get("user_id")


def _require_login():
    if not _user_id():
        return jsonify({"error": "Not logged in", "success": False}), 401
    return None


def _payload():
    data = request.get_json(silent=True) or {}
    if not data and request.form:
        data = request.form.to_dict()
    return data


def _date_filter_payload(data):
    return {key: data[key] for key in DATE_FILTER_KEYS if key in data}


def _error(message, status=400):
    return jsonify({"error": message, "success": False}), status


def _ok(**kwargs):
    payload = {"success": True}
    payload.update(kwargs)
    return jsonify(payload), 200


# ---------------------- Needs ----------------------

@api_bp.route("/needs/templates", methods=["GET"])
def needs_templates():
    err = _require_login()
    if err:
        return err
    return _ok(templates=needs_service.get_templates())


@api_bp.route("/needs/setup-status", methods=["GET"])
def needs_setup_status():
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        status = needs_service.get_setup_status(conn, _user_id())
        return _ok(**status)
    finally:
        conn.close()


@api_bp.route("/needs", methods=["GET"])
def needs_list():
    err = _require_login()
    if err:
        return err
    active_only = request.args.get("active_only", "").lower() in ("1", "true", "yes")
    conn = _get_db()
    try:
        needs = needs_service.list_needs(conn, _user_id(), active_only=active_only)
        setup = needs_service.get_setup_status(conn, _user_id())
        return _ok(needs=needs, **setup)
    finally:
        conn.close()


@api_bp.route("/needs/setup/skip", methods=["POST"])
def needs_setup_skip():
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        needs_service.mark_setup_completed(conn, _user_id())
        print(f"[NEEDS] OK Setup skipped - User {_user_id()}")
        return _ok(message="Setup skipped", needs_setup_completed=True, show_setup=False)
    finally:
        conn.close()


@api_bp.route("/needs/setup", methods=["POST"])
def needs_setup():
    err = _require_login()
    if err:
        return err
    data = _payload()
    selected = data.get("needs") if isinstance(data.get("needs"), list) else None
    if not selected:
        names = data.get("names")
        if isinstance(names, list):
            selected = [{"name": n, "default_amount": 0} for n in names]
    if not selected:
        return _error("Select at least one need")

    parsed = []
    for item in selected:
        if isinstance(item, str):
            name, _ = parse_required_string(item, "Need name")
            amount = 0.0
        else:
            name, name_err = parse_required_string(item.get("name"), "Need name")
            if name_err:
                return _error(name_err)
            amount, amt_err = parse_positive_float(
                item.get("default_amount", 0), "Default amount"
            )
            if amt_err:
                return _error(amt_err)
        parsed.append({"name": name, "default_amount": amount})

    conn = _get_db()
    try:
        created, setup_err = needs_service.setup_needs(conn, _user_id(), parsed)
        if setup_err:
            return _error(setup_err)
        print(f"[NEEDS] OK Setup - User {_user_id()}: {len(created)} needs created")
        return _ok(needs=created, message=f"✅ {len(created)} needs saved")
    finally:
        conn.close()


@api_bp.route("/needs", methods=["POST"])
def needs_create():
    err = _require_login()
    if err:
        return err
    data = _payload()
    name, name_err = parse_required_string(data.get("name"), "Need name")
    if name_err:
        return _error(name_err)
    amount, amt_err = parse_positive_float(data.get("default_amount", 0), "Default amount")
    if amt_err:
        return _error(amt_err)

    conn = _get_db()
    try:
        need, create_err = needs_service.create_need(conn, _user_id(), name, amount)
        if create_err:
            return _error(create_err)
        print(f"[NEEDS] OK Created - User {_user_id()}: {name} amount {amount:.2f}")
        return _ok(need=need, message=f"✅ Need '{name}' added")
    finally:
        conn.close()


@api_bp.route("/needs/<int:need_id>", methods=["PUT"])
def needs_update(need_id):
    err = _require_login()
    if err:
        return err
    data = _payload()
    name = None
    amount = None
    if "name" in data:
        name, name_err = parse_required_string(data.get("name"), "Need name")
        if name_err:
            return _error(name_err)
    if "default_amount" in data:
        amount, amt_err = parse_positive_float(data.get("default_amount"), "Default amount")
        if amt_err:
            return _error(amt_err)

    conn = _get_db()
    try:
        need, update_err = needs_service.update_need(
            conn, need_id, _user_id(), name=name, default_amount=amount
        )
        if update_err:
            status = 404 if "not found" in update_err.lower() else 400
            return _error(update_err, status)
        print(f"[NEEDS] OK Updated - Need {need_id}")
        return _ok(need=need, message="✅ Need updated")
    finally:
        conn.close()


@api_bp.route("/needs/<int:need_id>/toggle", methods=["PATCH"])
def needs_toggle(need_id):
    err = _require_login()
    if err:
        return err
    data = _payload()
    is_active = data.get("is_active", True)
    if isinstance(is_active, str):
        is_active = is_active.lower() in ("1", "true", "yes")

    conn = _get_db()
    try:
        need, toggle_err = needs_service.toggle_need(
            conn, need_id, _user_id(), bool(is_active)
        )
        if toggle_err:
            return _error(toggle_err, 404)
        state = "enabled" if need["is_active"] else "disabled"
        print(f"[NEEDS] OK Toggled - Need {need_id} {state}")
        return _ok(need=need, message=f"✅ Need {state}")
    finally:
        conn.close()


@api_bp.route("/needs/<int:need_id>", methods=["DELETE"])
def needs_delete(need_id):
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        ok, delete_err = needs_service.delete_need(conn, need_id, _user_id())
        if not ok:
            return _error(delete_err, 404)
        print(f"[NEEDS] OK Deleted - Need {need_id}")
        return _ok(message="✅ Need deleted")
    finally:
        conn.close()


# ---------------------- Personal Goals ----------------------

def _parse_goal_payload(data, for_create=True):
    goal_name, name_err = parse_required_string(data.get("goal_name"), "Goal name")
    if name_err:
        return None, name_err
    target_amount, target_err = parse_positive_float(
        data.get("target_amount"), "Target amount", allow_zero=False
    )
    if target_err:
        return None, target_err
    target_date, date_err = parse_date(
        data.get("target_date"), "Target date", allow_past=not for_create
    )
    if date_err and for_create:
        return None, date_err
    if not for_create and "target_date" in data and date_err:
        return None, date_err

    saved_amount = 0.0
    if "saved_amount" in data:
        saved_amount, saved_err = parse_positive_float(
            data.get("saved_amount"), "Saved amount"
        )
        if saved_err:
            return None, saved_err

    priority, priority_err = parse_priority(data.get("priority"))
    if priority_err:
        return None, priority_err

    parsed = {
        "goal_name": goal_name,
        "target_amount": target_amount,
        "saved_amount": saved_amount,
        "target_date": target_date if target_date else data.get("target_date"),
        "priority": priority,
        "notes": (data.get("notes") or "").strip() or None,
    }
    if not for_create:
        parsed = {k: v for k, v in parsed.items() if k in data or k == "goal_name"}
        if "goal_name" not in data:
            parsed.pop("goal_name", None)
        if "target_amount" not in data:
            parsed.pop("target_amount", None)
        if "target_date" not in data:
            parsed.pop("target_date", None)
        if "saved_amount" not in data:
            parsed.pop("saved_amount", None)
        if "priority" not in data:
            parsed.pop("priority", None)
        if "notes" not in data:
            parsed.pop("notes", None)
    return parsed, None


@api_bp.route("/personal-goals", methods=["GET"])
def personal_goals_list():
    err = _require_login()
    if err:
        return err
    status = request.args.get("status", "active")
    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        if status == "all":
            goals = []
            for st in ("active", "archived", "completed"):
                goals.extend(
                    goals_service.list_goals_with_projections(
                        conn, _user_id(), snapshot, status=st
                    )
                )
        else:
            goals = goals_service.list_goals_with_projections(
                conn, _user_id(), snapshot, status=status
            )
        return _ok(goals=goals)
    finally:
        conn.close()


@api_bp.route("/personal-goals/<int:goal_id>", methods=["GET"])
def personal_goal_detail(goal_id):
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        goal = goals_service.get_goal_with_projection(conn, goal_id, _user_id(), snapshot)
        if not goal:
            return _error("Goal not found", 404)
        return _ok(goal=goal)
    finally:
        conn.close()


@api_bp.route("/personal-goals", methods=["POST"])
def personal_goal_create():
    err = _require_login()
    if err:
        return err
    parsed, parse_err = _parse_goal_payload(_payload(), for_create=True)
    if parse_err:
        return _error(parse_err)

    conn = _get_db()
    try:
        goal = goals_service.create_goal(conn, _user_id(), parsed)
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        row = conn.execute(
            "SELECT * FROM personal_goals WHERE id = ?", (goal["id"],)
        ).fetchone()
        goal["projection"] = project_goal(row, snapshot)
        print(f"[GOAL] OK Created - User {_user_id()}: {goal['goal_name']}")
        return _ok(goal=goal, message=f"✅ Goal '{goal['goal_name']}' created")
    finally:
        conn.close()


@api_bp.route("/personal-goals/<int:goal_id>", methods=["PUT"])
def personal_goal_update(goal_id):
    err = _require_login()
    if err:
        return err
    data = _payload()
    parsed = {}
    if "goal_name" in data:
        name, name_err = parse_required_string(data.get("goal_name"), "Goal name")
        if name_err:
            return _error(name_err)
        parsed["goal_name"] = name
    if "target_amount" in data:
        target, target_err = parse_positive_float(
            data.get("target_amount"), "Target amount", allow_zero=False
        )
        if target_err:
            return _error(target_err)
        parsed["target_amount"] = target
    if "saved_amount" in data:
        saved, saved_err = parse_positive_float(data.get("saved_amount"), "Saved amount")
        if saved_err:
            return _error(saved_err)
        parsed["saved_amount"] = saved
    if "target_date" in data:
        target_date, date_err = parse_date(data.get("target_date"), "Target date")
        if date_err:
            return _error(date_err)
        parsed["target_date"] = target_date
    if "priority" in data:
        priority, priority_err = parse_priority(data.get("priority"))
        if priority_err:
            return _error(priority_err)
        parsed["priority"] = priority
    if "notes" in data:
        parsed["notes"] = (data.get("notes") or "").strip() or None

    if not parsed:
        return _error("No fields to update")

    conn = _get_db()
    try:
        goal, update_err = goals_service.update_goal(conn, goal_id, _user_id(), parsed)
        if update_err:
            return _error(update_err, 404)
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        row = conn.execute(
            "SELECT * FROM personal_goals WHERE id = ?", (goal_id,)
        ).fetchone()
        goal["projection"] = project_goal(row, snapshot)
        print(f"[GOAL] OK Updated - Goal {goal_id}")
        return _ok(goal=goal, message="✅ Goal updated")
    finally:
        conn.close()


@api_bp.route("/personal-goals/<int:goal_id>/archive", methods=["PATCH"])
def personal_goal_archive(goal_id):
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        goal, archive_err = goals_service.archive_goal(conn, goal_id, _user_id())
        if archive_err:
            return _error(archive_err, 404)
        print(f"[GOAL] OK Archived - Goal {goal_id}")
        return _ok(goal=goal, message="✅ Goal archived")
    finally:
        conn.close()


@api_bp.route("/personal-goals/<int:goal_id>", methods=["DELETE"])
def personal_goal_delete(goal_id):
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        ok, delete_err = goals_service.delete_goal(conn, goal_id, _user_id())
        if not ok:
            return _error(delete_err, 404)
        print(f"[GOAL] OK Deleted - Goal {goal_id}")
        return _ok(message="✅ Goal deleted")
    finally:
        conn.close()


# ---------------------- Savings & Affordability ----------------------

@api_bp.route("/savings/summary", methods=["GET"])
def savings_summary():
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        rounded = {k: round(v, 2) if isinstance(v, float) else v for k, v in snapshot.items()}
        return _ok(summary=rounded)
    finally:
        conn.close()


@api_bp.route("/savings/goal/<int:goal_id>/projection", methods=["GET"])
def savings_goal_projection(goal_id):
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        goal = goals_service.get_goal_with_projection(conn, goal_id, _user_id(), snapshot)
        if not goal:
            return _error("Goal not found", 404)
        return _ok(goal=goal)
    finally:
        conn.close()


@api_bp.route("/affordability/calculate", methods=["POST"])
def affordability_calculate():
    err = _require_login()
    if err:
        return err
    data = _payload()
    name = (data.get("product_name") or "").strip() or "Product"
    price, price_err = parse_positive_float(
        data.get("product_price"), "Product price", allow_zero=False
    )
    if price_err:
        return _error(price_err)

    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(
            conn, _user_id(), _date_filter_payload(data) or request.args
        )
        result = calculate_affordability(name, price, snapshot)
        print(f"[AFFORDABILITY] OK User {_user_id()}: {name} price {price:.2f}")
        return _ok(affordability=result)
    finally:
        conn.close()


# ---------------------- Insights ----------------------

@api_bp.route("/insights", methods=["GET"])
def insights_list():
    err = _require_login()
    if err:
        return err
    conn = _get_db()
    try:
        snapshot = get_financial_snapshot(conn, _user_id(), request.args)
        goals = goals_service.list_goals_with_projections(
            conn, _user_id(), snapshot, status="active"
        )
        insights = insights_service.generate_insights(snapshot, goals)
        return _ok(insights=insights, summary=snapshot)
    finally:
        conn.close()
