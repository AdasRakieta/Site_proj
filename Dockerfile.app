FROM python:3.11-slim

WORKDIR /srv/app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Minimalne pakiety systemowe potrzebne do budowy extensionów i psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Kopiujemy requirements (jeśli jest) i instalujemy
COPY requirements.txt /srv/app/requirements.txt
RUN pip install --upgrade pip \
 && if [ -f /srv/app/requirements.txt ]; then pip install -r /srv/app/requirements.txt; fi

# Kod będzie mountowany w trybie dev przez docker-compose volumes: ./app -> /srv/app
EXPOSE 5000

# Uruchamiamy główną aplikację
CMD ["python", "/srv/app/app_db.py"]