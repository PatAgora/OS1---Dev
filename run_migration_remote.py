#!/usr/bin/env python3
"""
Run database migration to add security columns
"""
import os
import sys

# Get DATABASE_URL from environment
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("❌ DATABASE_URL environment variable not set!")
    print("This script needs to run on Railway or with DATABASE_URL set.")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2...")
    os.system("pip install -q psycopg2-binary")
    import psycopg2

print("=" * 80)
print("CREST SECURITY MIGRATION")
print("=" * 80)
print()

migration_sql = """
-- Add security columns to users table
ALTER TABLE users 
  ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'employee',
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS last_login TIMESTAMP,
  ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    user_id INTEGER,
    user_email VARCHAR(255),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    action VARCHAR(255) NOT NULL,
    details TEXT,
    status VARCHAR(20) DEFAULT 'success',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_category ON audit_logs(event_category);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Set first user as admin
UPDATE users 
SET role = 'admin' 
WHERE id = (SELECT MIN(id) FROM users);
"""

try:
    print("Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("Running migration...")
    cursor.execute(migration_sql)
    
    print("✅ Migration completed successfully!")
    print()
    
    # Verify
    print("Verifying changes...")
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'users' 
        ORDER BY ordinal_position
    """)
    
    print("\n✅ Users table columns:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    
    # Check audit_logs table
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'audit_logs'
    """)
    audit_exists = cursor.fetchone()[0]
    
    if audit_exists:
        print("\n✅ audit_logs table: Created")
    else:
        print("\n❌ audit_logs table: Not found")
    
    # Check first user
    cursor.execute("SELECT id, name, email, role FROM users ORDER BY id LIMIT 1")
    first_user = cursor.fetchone()
    if first_user:
        print(f"\n✅ First user: {first_user[1]} ({first_user[2]}) - Role: {first_user[3]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 80)
    print("✅ MIGRATION COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
