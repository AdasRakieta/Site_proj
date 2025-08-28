FROM python:3.11-slim

# Use /srv as project root to avoid accidental volume overwrite of entrypoint
WORKDIR /srv

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System packages needed (psycopg2, building wheels etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /srv/requirements.txt

RUN pip install --upgrade pip \
 && if [ -f /srv/requirements.txt ]; then pip install -r /srv/requirements.txt; fi

# Copy application code into image
# Place app package under /srv/app and keep entrypoint at /srv/app_db.py
COPY app/ /srv/app/
COPY utils/ /srv/utils/
COPY backups/ /srv/backups/
COPY templates/ /srv/templates/
COPY static/ /srv/static/
COPY app_db.py /srv/app_db.py

# Optional: copy management logs or other top-level files if needed
COPY management_logs.json /srv/management_logs.json

EXPOSE 5000

# Run the main entrypoint from /srv so imports `import app...` resolve correctly.
CMD ["python", "/srv/app_db.py"]