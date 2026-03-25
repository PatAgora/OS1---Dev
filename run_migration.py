#!/usr/bin/env python3
"""
Run database migration on Railway PostgreSQL
Usage: python run_migration.py
"""
import os
import sys

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system("pip install psycopg2-binary")
    import psycopg2

# Get database URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set!")
    print("Set it with: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

print("=" * 80)
print("DATABASE MIGRATION")
print("=" * 80)
print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")
print()

# Read migration SQL
migration_file = 'migrations/001_add_security_columns.sql'
try:
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
except FileNotFoundError:
    print(f"❌ Migration file not found: {migration_file}")
    sys.exit(1)

# Connect and run migration
try:
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Running migration...")
    cursor.execute(migration_sql)
    
    print("✅ Migration completed successfully!")
    print()
    
    # Verify the changes
    print("Verifying users table structure...")
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
    """)
    
    print("\nUsers table columns:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]}")
    
    # Check if admin user exists
    cursor.execute("SELECT email, role FROM users WHERE role IN ('admin', 'super_admin') LIMIT 5")
    admins = cursor.fetchall()
    
    print(f"\nAdmin users found: {len(admins)}")
    for email, role in admins:
        print(f"  - {email} ({role})")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
