#!/usr/bin/env python3
"""
Quick script to reset admin password.
Usage: python reset_admin_password.py
"""
import os
import sys
from werkzeug.security import generate_password_hash

# Get database URL from environment or use default
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ats.db')

print("=" * 80)
print("ADMIN PASSWORD RESET")
print("=" * 80)
print()

# Ask for new password
new_password = input("Enter new admin password (min 12 chars): ")

if len(new_password) < 12:
    print("❌ Password must be at least 12 characters!")
    sys.exit(1)

# Generate hash
password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')

print()
print("To update the database, run this SQL command:")
print()
print("UPDATE users")
print(f"SET password_hash = '{password_hash}',")
print("    failed_login_attempts = 0,")
print("    locked_until = NULL")
print("WHERE email = 'admin@example.com';")
print()
print("=" * 80)
print("OR use these credentials with the existing password:")
print("Email: admin@example.com")
print("Password: Check Railway deployment logs for auto-generated password")
print("         (Search logs for 'ADMIN USER CREATED')")
print("=" * 80)
