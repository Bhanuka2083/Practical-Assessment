#!/bin/bash
set -e

echo "Waiting for PostgreSQL connection at ${POSTGRES_SERVER:-postgres}:${POSTGRES_PORT:-5432}..."

# Loop until PostgreSQL port is responsive
python - <<END
import socket
import time
import os

host = os.getenv("POSTGRES_SERVER", "postgres")
port = int(os.getenv("POSTGRES_PORT", 5432))

start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL is reachable!")
            break
    except OSError:
        time.sleep(1)
        if time.time() - start > 45:
            raise TimeoutError("Database connection timed out after 45 seconds.")
END

echo "Running automated database setup & seeding..."
python -m app.db.init_db

echo "Starting Uvicorn..."
exec "$@"