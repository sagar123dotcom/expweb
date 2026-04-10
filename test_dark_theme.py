#!/usr/bin/env python3
"""Test suite for Expense Tracker dark theme SaaS"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def test_register():
    """Test user registration"""
    print("\n🔐 Testing Registration...")
    response = SESSION.post(f"{BASE_URL}/register", data={
        'username': 'testuser123',
        'password': 'Test@123456'
    })
    if response.status_code == 200:
        print("✅ Registration page loaded")
        return True
    return False

def test_login():
    """Test user login"""
    print("\n🔓 Testing Login...")
    response = SESSION.post(f"{BASE_URL}/login", data={
        'username': 'testuser123',
        'password': 'Test@123456'
    })
    if response.status_code == 200:
        print("✅ Login successful")
        return 'user_id' in SESSION.cookies.get_dict()
    return False

def test_add_expense():
    """Test add expense endpoint"""
    print("\n💰 Testing Add Expense...")
    today = datetime.now().strftime("%Y-%m-%d")
    
    response = SESSION.post(f"{BASE_URL}/add", data={
        'date': today,
        'name': 'Test Expense',
        'category': 'Education',
        'amount': '50.00'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Expense added successfully: {data.get('message')}")
            return True
    else:
        print(f"❌ Failed: {response.text}")
    return False

def test_add_income():
    """Test add income endpoint"""
    print("\n📈 Testing Add Income...")
    
    response = SESSION.post(f"{BASE_URL}/add_income", data={
        'income_amount': '1000.00'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Income added successfully: {data.get('message')}")
            return True
    else:
        print(f"❌ Failed: {response.text}")
    return False

def test_set_goal():
    """Test set savings goal"""
    print("\n🎯 Testing Set Goal...")
    
    response = SESSION.post(f"{BASE_URL}/set_goal", data={
        'goal_amount': '5000.00'
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print(f"✅ Goal set successfully: {data.get('message')}")
            return True
    else:
        print(f"❌ Failed: {response.text}")
    return False

def test_get_expenses():
    """Test get expenses endpoint"""
    print("\n📋 Testing Get Expenses...")
    
    response = SESSION.get(f"{BASE_URL}/get_expenses")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got expenses - Total Income: ₹{data['total_income']}, Total Expense: ₹{data['total_expense']}, Balance: ₹{data['balance']}")
        return True
    else:
        print(f"❌ Failed: {response.text}")
    return False

def test_ui_theme():
    """Test that dark theme is applied"""
    print("\n🌙 Testing Dark Theme CSS...")
    
    response = SESSION.get(f"{BASE_URL}/")
    if response.status_code == 200:
        content = response.text
        if '#0f172a' in content or 'bg-gradient-dark' in content or 'slate-900' in content:
            print("✅ Dark theme CSS found in HTML")
            return True
    print("❌ Dark theme CSS not found")
    return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 EXPENSE TRACKER - DARK THEME SAAS TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_ui_theme,
        test_register,
        test_login,
        test_add_expense,
        test_add_income,
        test_set_goal,
        test_get_expenses,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"✅ TESTS PASSED: {passed}/{len(tests)}")
    print(f"❌ TESTS FAILED: {failed}/{len(tests)}")
    print("=" * 60)
