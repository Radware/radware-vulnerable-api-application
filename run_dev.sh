#!/bin/bash

# Start the backend FastAPI app (run in background)
echo "Starting backend API on port 8000..."
if [ -n "$UVICORN_WORKERS" ]; then
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$UVICORN_WORKERS" --reload &
else
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
fi
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# Start the frontend Flask app
echo "Starting frontend app on port 5001..."
python frontend/main.py

# If frontend is stopped, also kill the backend
kill $BACKEND_PID
