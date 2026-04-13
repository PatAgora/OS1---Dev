#!/bin/bash
# Railway startup script for ATS application
# Starts gunicorn FIRST so health checks pass, then runs setup tasks in background.

echo "Starting ATS Application..."
echo "Python version: $(python3 --version)"
echo "PORT: ${PORT:-8080}"

# Start gunicorn IMMEDIATELY so Railway health check passes
exec gunicorn app:app \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 4 \
    --timeout 120 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
