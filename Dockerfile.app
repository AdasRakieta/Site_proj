FROM python:3.11-slim

WORKDIR /srv/app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /srv/app/requirements.txt
RUN pip install --upgrade pip \
 && if [ -f /srv/app/requirements.txt ]; then pip install -r /srv/app/requirements.txt; fi

COPY app/ /srv/app/app/
COPY backups/ /srv/app/backups/
COPY utils/ /srv/app/utils/
COPY app_db.py /srv/app/app_db.py

EXPOSE 5000

CMD ["python", "app_db.py"]