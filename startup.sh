#!/bin/bash
# Railway startup script for ATS application - WITH DEBUGGING

set -e  # Exit on error

echo "🚀 Starting ATS Application..."
echo "================================"
echo "✓ Python version: $(python3 --version)"
echo "✓ DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "✓ PORT: ${PORT:-8080}"
echo "✓ FLASK_ENV: ${FLASK_ENV:-development}"
echo "✓ GEMINI_API_KEY: ${GEMINI_API_KEY:0:20}... (length: ${#GEMINI_API_KEY})"

# Check critical environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "⚠ WARNING: DATABASE_URL not set, using default SQLite"
fi

if [ -z "$FLASK_SECRET_KEY" ] || [ "$FLASK_SECRET_KEY" = "dev-secret" ]; then
    echo ""
    echo "⚠ WARNING: FLASK_SECRET_KEY not set, using default (INSECURE!)"
fi

# Test app import with detailed error output
echo ""
echo "Testing app import..."
python3 -c "from app import app; print('✓ App import successful')" 2>&1 || {
    echo "❌ App import failed!"
    echo ""
    echo "Attempting detailed import to find error..."
    python3 << 'PYEOF'
import sys
import traceback
try:
    print("Step 1: Importing Flask...")
    from flask import Flask
    print("✓ Flask imported")
    
    print("Step 2: Importing SQLAlchemy...")
    from sqlalchemy import create_engine
    print("✓ SQLAlchemy imported")
    
    print("Step 3: Importing app module...")
    import app
    print("✓ App module imported")
    
    print("Step 4: Getting app object...")
    app_obj = app.app
    print("✓ App object retrieved")
    
except Exception as e:
    print(f"❌ Error during import:")
    traceback.print_exc()
    sys.exit(1)
PYEOF
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Detailed import also failed. Exiting."
        exit 1
    fi
}

# Ensure admin user exists (does NOT overwrite if already present)
echo ""
echo "Ensuring admin user exists..."
python3 << 'ADMINEOF'
import os, psycopg2
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("No DATABASE_URL — skipping.")
    exit(0)

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email = 'admin@demo.example.com'")
    if cur.fetchone():
        print("Admin user already exists — skipping.")
    else:
        pw_hash = generate_password_hash("DemoAdmin2024!", method="pbkdf2:sha256")
        cur.execute(
            "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s)",
            ("Admin User", "admin@demo.example.com", pw_hash, "admin", True)
        )
        conn.commit()
        print("Admin user created: admin@demo.example.com / DemoAdmin2024!")

    conn.close()
except Exception as e:
    print(f"Admin check error: {e}")
ADMINEOF

# Demo data cleanup REMOVED — production database must never be wiped on deploy
echo ""
echo "Skipping demo data cleanup (production safety)."

# Seed associate profiles if candidates table is empty
echo ""
echo "Checking if associate seed is needed..."
python3 -c "
from app import engine
from sqlalchemy import text
from sqlalchemy.orm import Session
with Session(engine) as s:
    try:
        ccount = s.execute(text('SELECT COUNT(*) FROM candidates')).scalar()
        if ccount == 0:
            print('No candidates found — running associate seed...')
            import seed_associates
            seed_associates.seed_associates()
        else:
            print(f'Database has {ccount} candidates — skipping associate seed.')
    except Exception as e:
        print(f'Associate seed check: {e}')
" 2>&1

# Start application with gunicorn
echo ""
echo "Starting gunicorn..."
echo "================================"

exec gunicorn app:app \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
