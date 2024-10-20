FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY config.py ./

# Richte das Skript ein, um bei Container-Start ausgeführt zu werden
CMD ["python", "./main.py"]