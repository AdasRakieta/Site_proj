#!/bin/bash
# Run SmartHome app with Gunicorn (Linux)
# Usage: bash run_server_linux.sh

# Activate venv if exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Install gunicorn if not present
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Run the server
gunicorn -w 4 -b 0.0.0.0:5001 'app_db:main'
