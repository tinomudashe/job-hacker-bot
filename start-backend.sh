#!/bin/bash

# Navigate to backend directory and start the FastAPI server
echo "Starting Job Hacker Bot Backend..."

# FIX: Set the PYTHONPATH to include the project's root directory
# This allows absolute imports like 'from app...' to work correctly.
export PYTHONPATH=$(pwd)/backend

# FIX: Run uvicorn from the project root, pointing to the app inside the backend directory.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001 --app-dir backend 