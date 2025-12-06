FROM python:3.12-slim

# Install tzdata for timezone support
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Timezone will be set by docker-compose via TZ environment variable
# or will use system timezone from mounted /etc/localtime

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN opentelemetry-bootstrap --action=install

WORKDIR /app/src

CMD ["opentelemetry-instrument", "python", "main.py"]
