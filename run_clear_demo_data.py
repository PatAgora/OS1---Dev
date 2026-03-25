#!/usr/bin/env python3
"""
Run 007_clear_demo_data.sql against the connected database.
Usage: python run_clear_demo_data.py
Reads DATABASE_URL from environment.
"""
import os
import sys
import subprocess

try:
    import psycopg2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("DATABASE_URL not set!")
    sys.exit(1)

db_host = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'
print(f"Database: {db_host}")

# Show before counts
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cursor = conn.cursor()

print("\n--- BEFORE ---")
for table in ['users', 'associate_profiles', 'candidates', 'applications', 'jobs',
              'engagements', 'opportunities', 'invoices', 'documents', 'vetting_check']:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    print(f"  {table}: {cursor.fetchone()[0]}")

# Run migration
with open('migrations/007_clear_demo_data.sql', 'r') as f:
    sql = f.read()

print("\nRunning cleanup...")
cursor.execute(sql)
conn.commit()

print("\n--- AFTER ---")
for table in ['users', 'associate_profiles', 'candidates', 'applications', 'jobs',
              'engagements', 'opportunities', 'invoices', 'documents', 'vetting_check']:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    print(f"  {table}: {cursor.fetchone()[0]}")

# Verify preserved data
cursor.execute("SELECT id, email, role FROM users ORDER BY id")
print("\nPreserved users:")
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[1]} ({row[2]})")

cursor.execute("SELECT ap.id, ap.first_name, ap.surname FROM associate_profiles ap ORDER BY ap.id")
print("\nPreserved associate profiles:")
for row in cursor.fetchall():
    print(f"  ID {row[0]}: {row[1]} {row[2]}")

cursor.close()
conn.close()
print("\nDone.")
