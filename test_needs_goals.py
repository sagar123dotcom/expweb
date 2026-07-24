#!/usr/bin/env python3
"""Tests for Needs Management, Goal Planner, Savings Engine, and Insights."""

import time
from app import app


def run_tests():
    client = app.test_client()
    username = f"planning_test_{int(time.time())}"

    client.post("/register", data={"username": username, "password": "Test@12345"})
    client.post("/login", data={"username": username, "password": "Test@12345"})

    results = []

    def check(name, condition):
        results.append((name, condition))
        print(f"{'PASS' if condition else 'FAIL'} | {name}")

    r = client.post("/api/needs/setup/skip")
    check("Needs setup skip", r.status_code == 200 and r.get_json().get("success"))

    r = client.post("/add_income", data={"income_amount": "60000"})
    check("Add income", r.status_code == 200)

    r = client.post("/api/needs/setup", json={"names": ["Rent", "Groceries"]})
    check("Bulk needs setup", r.status_code == 200)

    r = client.put("/api/needs/1", json={"default_amount": 20000})
    if r.status_code == 404:
        needs = client.get("/api/needs").get_json()["needs"]
        if needs:
            r = client.put(f"/api/needs/{needs[0]['id']}", json={"default_amount": 20000})
    check("Update need", r.status_code == 200)

    r = client.post(
        "/api/personal-goals",
        json={
            "goal_name": "Laptop",
            "target_amount": 90000,
            "saved_amount": 15000,
            "target_date": "2027-01-15",
            "priority": 1,
        },
    )
    check("Create personal goal", r.status_code == 200)
    goal_id = r.get_json().get("goal", {}).get("id")

    r = client.get("/api/savings/summary")
    summary = r.get_json().get("summary", {})
    check("Savings summary", r.status_code == 200 and "monthly_free_savings" in summary)

    if goal_id:
        r = client.get(f"/api/savings/goal/{goal_id}/projection")
        check("Goal projection", r.status_code == 200 and "projection" in r.get_json().get("goal", {}))

    r = client.post(
        "/api/affordability/calculate",
        json={"product_name": "Smartphone", "product_price": 30000},
    )
    check("Affordability", r.status_code == 200 and "affordability" in r.get_json())

    r = client.get("/api/insights")
    check("Insights", r.status_code == 200 and isinstance(r.get_json().get("insights"), list))

    r = client.post("/set_goal", data={"goal_amount": "10000"})
    check("Legacy savings goal", r.status_code == 200 and r.get_json().get("success"))

    r = client.get("/get_expenses")
    data = r.get_json()
    check(
        "Legacy get_expenses unchanged",
        set(data.keys()) >= {"expenses", "total_income", "goal", "progress"},
    )

    r = client.get("/")
    check("Dashboard includes planning UI", b"Goal Planner" in r.data)

    passed = sum(1 for _, ok in results if ok)
    print(f"\nTOTAL: {passed}/{len(results)} passed")
    return passed == len(results)


if __name__ == "__main__":
    raise SystemExit(0 if run_tests() else 1)
