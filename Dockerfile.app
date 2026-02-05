FROM python:3.11-slim

# Accept build argument for asset versioning
ARG ASSET_VERSION=dev
ENV ASSET_VERSION=${ASSET_VERSION}

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

# SECURITY: Create non-root user for running the application (MEDIUM FIX)
RUN groupadd -r smarthome && useradd -r -g smarthome smarthome

# Set ownership of application files to non-root user
RUN chown -R smarthome:smarthome /srv

# Create upload directory with proper permissions
RUN mkdir -p /srv/static/profile_pictures && \
    chown -R smarthome:smarthome /srv/static/profile_pictures

# Switch to non-root user
USER smarthome

EXPOSE 5000

# Run the main entrypoint from /srv so imports `import app...` resolve correctly.
CMD ["python", "/srv/app_db.py"]