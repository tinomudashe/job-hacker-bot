#!/bin/bash

# Navigate to backend directory and start the FastAPI server
echo "Starting Job Hacker Bot Backend..."
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 