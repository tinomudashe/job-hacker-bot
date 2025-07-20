#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Run database migrations to ensure the database is up-to-date.
echo "Running database migrations..."
alembic upgrade head

# Execute the main command (passed from the Dockerfile's CMD).
# This will start the Uvicorn server for the FastAPI application.
exec "$@"