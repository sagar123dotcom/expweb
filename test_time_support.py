import sqlite3

from app import app


def set_session(client, user_id=1):
    with client.session_transaction() as session:
        session['user_id'] = user_id
        session['username'] = 'tester'


def test_add_expense_persists_date_and_time():
    client = app.test_client()
    set_session(client)

    response = client.post(
        '/add',
        data={
            'date': '2026-08-16',
            'time': '13:12',
            'name': 'Alpha',
            'category': 'Groceries',
            'amount': '9.99',
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True

    conn = sqlite3.connect('expenses.db')
    row = conn.execute(
        "SELECT date, time, name FROM expenses WHERE user_id = 1 AND name = 'Alpha' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row == ('2026-08-16', '13:12', 'Alpha')


def test_get_expenses_orders_by_date_then_time():
    client = app.test_client()
    set_session(client)

    conn = sqlite3.connect('expenses.db')
    conn.execute(
        "INSERT INTO expenses (user_id, date, time, name, category, amount) VALUES (?, ?, ?, ?, ?, ?)",
        (1, '2026-08-16', '12:30', 'Beta', 'Groceries', 7.5),
    )
    conn.execute(
        "INSERT INTO expenses (user_id, date, time, name, category, amount) VALUES (?, ?, ?, ?, ?, ?)",
        (1, '2026-08-16', '23:59', 'Gamma', 'Miscellaneous', 10.5),
    )
    conn.commit()
    conn.close()

    response = client.get('/get_expenses')
    assert response.status_code == 200
    expenses = response.get_json()['expenses']
    assert expenses[0]['name'] == 'Gamma'
    assert expenses[0]['time'] == '23:59'
