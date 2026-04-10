#!/usr/bin/env python3
"""
Test script for Expense Tracker ADD and DELETE operations
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

class TestExpenseTracker:
    def __init__(self):
        self.session = requests.Session()
        self.user_id = None
        self.expense_ids = []
        
    def register_user(self, username, password):
        print("\n" + "="*60)
        print("🔐 REGISTER USER")
        print("="*60)
        
        response = self.session.post(f"{BASE_URL}/register", data={
            'username': username,
            'password': password
        }, allow_redirects=False)
        
        print(f"Status: {response.status_code}")
        print(f"✅ Registration successful!" if response.status_code == 302 else "❌ Registration failed")
        return response.status_code == 302
    
    def login_user(self, username, password):
        print("\n" + "="*60)
        print("🔑 LOGIN USER")
        print("="*60)
        
        response = self.session.post(f"{BASE_URL}/login", data={
            'username': username,
            'password': password
        }, allow_redirects=False)
        
        print(f"Status: {response.status_code}")
        print(f"✅ Login successful!" if response.status_code == 302 else "❌ Login failed")
        
        # Check if session is set
        print(f"Session cookies: {self.session.cookies}")
        return response.status_code == 302
    
    def get_homepage(self):
        print("\n" + "="*60)
        print("📄 GET HOMEPAGE")
        print("="*60)
        
        response = self.session.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"✅ Homepage loaded" if response.status_code == 200 else "❌ Homepage failed")
        return response.status_code == 200
    
    def test_add_expense(self):
        print("\n" + "="*60)
        print("➕ ADD EXPENSE")
        print("="*60)
        
        today = datetime.now().strftime("%Y-%m-%d")
        data = {
            'date': today,
            'name': 'Test Expense',
            'category': 'Groceries',
            'amount': '500'
        }
        
        print(f"Payload: {data}")
        
        response = self.session.post(f"{BASE_URL}/add", data=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Expense added successfully!")
                if 'expense_id' in result:
                    self.expense_ids.append(result['expense_id'])
                    print(f"   Expense ID: {result['expense_id']}")
                return True
            else:
                print(f"❌ Error: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return False
    
    def test_add_multiple_expenses(self):
        print("\n" + "="*60)
        print("➕ ADD MULTIPLE EXPENSES")
        print("="*60)
        
        today = datetime.now().strftime("%Y-%m-%d")
        expenses = [
            {'date': today, 'name': 'Coffee', 'category': 'Groceries', 'amount': '50'},
            {'date': today, 'name': 'Electricity Bill', 'category': 'Utilities', 'amount': '800'},
            {'date': today, 'name': 'Movie Ticket', 'category': 'Entertainment', 'amount': '300'},
        ]
        
        added = 0
        for expense in expenses:
            response = self.session.post(f"{BASE_URL}/add", data=expense)
            try:
                result = response.json()
                if result.get('success'):
                    print(f"✅ {expense['name']}: ₹{expense['amount']}")
                    if 'expense_id' in result:
                        self.expense_ids.append(result['expense_id'])
                    added += 1
                else:
                    print(f"❌ {expense['name']}: {result.get('error')}")
            except:
                print(f"❌ {expense['name']}: Failed to parse response")
        
        print(f"\n✅ Added {added}/{len(expenses)} expenses")
        return added == len(expenses)
    
    def test_add_income(self):
        print("\n" + "="*60)
        print("💰 ADD INCOME")
        print("="*60)
        
        data = {'income_amount': '2000'}
        print(f"Payload: {data}")
        
        response = self.session.post(f"{BASE_URL}/add_income", data=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Income added successfully!")
                return True
            else:
                print(f"❌ Error: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return False
    
    def test_set_goal(self):
        print("\n" + "="*60)
        print("🎯 SET GOAL")
        print("="*60)
        
        data = {'goal_amount': '5000'}
        print(f"Payload: {data}")
        
        response = self.session.post(f"{BASE_URL}/set_goal", data=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        try:
            result = response.json()
            print(f"JSON: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print("✅ Goal set successfully!")
                return True
            else:
                print(f"❌ Error: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return False
    
    def test_get_expenses(self):
        print("\n" + "="*60)
        print("📊 GET EXPENSES")
        print("="*60)
        
        response = self.session.get(f"{BASE_URL}/get_expenses")
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Total Income: ₹{result.get('total_income', 0)}")
            print(f"Total Expense: ₹{result.get('total_expense', 0)}")
            print(f"Balance: ₹{result.get('balance', 0)}")
            print(f"Goal: ₹{result.get('goal', 0)}")
            print(f"Number of transactions: {len(result.get('expenses', []))}")
            
            if result.get('expenses'):
                print("\nRecent transactions:")
                for exp in result['expenses'][:3]:
                    print(f"  - {exp['date']}: {exp['name']} ({exp['category']}) = ₹{exp['amount']}")
            
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def test_delete_expense(self):
        print("\n" + "="*60)
        print("🗑️  DELETE EXPENSE")
        print("="*60)
        
        if not self.expense_ids:
            print("❌ No expense IDs to delete")
            return False
        
        expense_id = self.expense_ids[0]
        print(f"Deleting expense ID: {expense_id}")
        
        # Try both GET and POST
        for method in ['GET', 'POST']:
            print(f"\nTrying DELETE with {method}...")
            if method == 'GET':
                response = self.session.get(f"{BASE_URL}/delete/{expense_id}")
            else:
                response = self.session.post(f"{BASE_URL}/delete/{expense_id}")
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            try:
                result = response.json()
                print(f"JSON: {json.dumps(result, indent=2)}")
                
                if result.get('success'):
                    print(f"✅ Deleted with {method}!")
                    self.expense_ids.pop(0)
                    return True
                else:
                    print(f"❌ {method} failed: {result.get('error')}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return False
    
    def run_all_tests(self):
        print("\n" + "█"*60)
        print("█  EXPENSE TRACKER - COMPREHENSIVE TEST SUITE")
        print("█"*60)
        
        results = []
        
        # Register and login
        import time
        timestamp = str(int(time.time()))
        username = f"testuser_{timestamp}"
        
        if not self.register_user(username, "Test@12345"):
            print("\n❌ Cannot proceed without registration")
            return
        
        if not self.login_user(username, "Test@12345"):
            print("\n❌ Cannot proceed without login")
            return
        
        # Get homepage
        results.append(("Homepage Load", self.get_homepage()))
        
        # Test operations
        results.append(("Add Single Expense", self.test_add_expense()))
        results.append(("Add Multiple Expenses", self.test_add_multiple_expenses()))
        results.append(("Add Income", self.test_add_income()))
        results.append(("Set Goal", self.test_set_goal()))
        results.append(("Get Expenses", self.test_get_expenses()))
        results.append(("Delete Expense", self.test_delete_expense()))
        
        # Print summary
        print("\n" + "█"*60)
        print("█  TEST SUMMARY")
        print("█"*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:8} | {name}")
        
        print("█"*60)
        print(f"TOTAL: {passed}/{total} tests passed")
        print("█"*60 + "\n")

if __name__ == "__main__":
    tester = TestExpenseTracker()
    tester.run_all_tests()
