"""Database verification script"""
import sqlite3

conn = sqlite3.connect('expenses.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('DATABASE VERIFICATION')
print('='*60)

# Users
users = c.execute('SELECT COUNT(*) as count FROM users').fetchone()
print(f'Users: {users["count"]}')

# Expenses
expenses = c.execute('SELECT COUNT(*) as count FROM expenses').fetchone()
print(f'Expenses: {expenses["count"]}')

# Goals
goals = c.execute('SELECT COUNT(*) as count FROM goals').fetchone()
print(f'Goals: {goals["count"]}')

print('='*60)

# Sample expenses
print('\nRECENT EXPENSES:')
recent = c.execute('SELECT id, date, name, category, amount FROM expenses ORDER BY id DESC LIMIT 5')
for row in recent:
    print(f'  [{row["id"]}] {row["date"]} - {row["name"]} ({row["category"]}) = ₹{row["amount"]}')

# Check last user
print('\nRECENT USERS:')
users_list = c.execute('SELECT id, username FROM users ORDER BY id DESC LIMIT 3')
for row in users_list:
    print(f'  [{row["id"]}] {row["username"]}')

conn.close()
print('\n✅ Database is working correctly!')
