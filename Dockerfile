FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends openssl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install curl for healthcheck and psql for database check
RUN apt-get update && apt-get install -y curl postgresql-client && rm -rf /var/lib/apt/lists/*

CMD ["sh", "-c", "\
    # Wait for database to be ready \
    until PGPASSWORD=postgres psql -h slackparaphrase-db -U postgres -d slackparaphrase -c '\\q'; do \
        echo 'Postgres is unavailable - sleeping'; \
        sleep 1; \
    done && \
    \
    # Apply migrations \
    echo 'Applying migrations...' && \
    yoyo apply --database postgresql://postgres:postgres@slackparaphrase-db:5432/slackparaphrase migrations && \
    \
    # Start the application \
    echo 'Starting application...' && \
    uvicorn src.main:app \
        --host 0.0.0.0 \
        --port 8443 \
        --ssl-keyfile ./certs/key.pem \
        --ssl-certfile ./certs/cert.pem"] 