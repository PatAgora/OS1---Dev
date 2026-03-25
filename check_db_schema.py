#!/usr/bin/env python3
"""
Quick diagnostic to check what columns exist in the users table
"""
import os
import sys

# This will work locally - you can copy/paste to Railway CLI
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///ats.db')

print("=" * 80)
print("DATABASE SCHEMA DIAGNOSTIC")
print("=" * 80)
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
print()

try:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("Columns in 'users' table:")
    print("-" * 80)
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
    """)
    
    for row in cursor.fetchall():
        col_name, data_type, max_len, nullable = row
        length_info = f"({max_len})" if max_len else ""
        null_info = "NULL" if nullable == 'YES' else "NOT NULL"
        print(f"  {col_name:30s} {data_type:15s}{length_info:10s} {null_info}")
    
    print()
    print("-" * 80)
    print("Looking for password-related columns:")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name LIKE '%password%'
    """)
    
    password_cols = cursor.fetchall()
    if password_cols:
        for col in password_cols:
            print(f"  ✓ Found: {col[0]}")
    else:
        print("  ✗ No password columns found!")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {e}")
    print()
    print("To run this on Railway:")
    print("1. Go to Railway dashboard")
    print("2. Open PostgreSQL service")
    print("3. Click 'Data' tab")
    print("4. Run: SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
