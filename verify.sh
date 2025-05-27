#!/bin/bash
# Verification script for Radware Vulnerable API tests and traffic generation

echo "----------------------------------------"
echo "Radware Vulnerable API Verification Script"
echo "----------------------------------------"

# Change to the project directory
cd "$(dirname "$0")"

PYTHON_EXEC="python3" # Use python3 by default
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Neither python3 nor python found in PATH. Please install Python."
        exit 1
    fi
    PYTHON_EXEC="python" # Fallback to python if python3 is not found
fi
echo "Using Python executable: $PYTHON_EXEC"


# Function to check if port 8000 is in use and get PID
get_server_pid() {
    if command -v lsof &> /dev/null; then
        lsof -ti:8000 # -t gives terse output (just PID), -i for network files
    elif command -v ss &> /dev/null; then
        # ss is common on Linux, lsof on macOS/other Unix
        ss -Halnpt '( sport = :8000 )' | awk -F"," 'match($0, /pid=([0-9]+)/) {print substr($0, RSTART+4, RLENGTH-4)}' | head -n 1
    elif command -v netstat &> /dev/null; then
        # Fallback for systems with netstat (less reliable for PID direct extraction across OS)
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            netstat -tulnp | grep ':8000' | awk '{print $7}' | cut -d'/' -f1 | head -n 1
        elif [[ "$OSTYPE" == "darwin"* ]]; then # macOS
            netstat -anv | grep '\.8000.*LISTEN' | awk '{print $9}' # This gets LSOF PID on macOS for netstat
            # For macOS, lsof is better. This is a rough fallback.
        else
            echo "" # Other OS, netstat parsing is too varied
        fi
    else
        echo "" # No known command to check
    fi
}

# Trap to clean up server if script is interrupted
cleanup() {
    echo "Script interrupted. Cleaning up..."
    # If SERVER_STARTED_BY_SCRIPT is true, implies SERVER_PID is set for the uvicorn we started.
    if [ "$SERVER_STARTED_BY_SCRIPT" = true ] && [ -n "$SERVER_PID" ] && ps -p "$SERVER_PID" > /dev/null; then
        echo "Stopping API server (PID: $SERVER_PID) started by script..."
        kill "$SERVER_PID"
        wait "$SERVER_PID" 2>/dev/null
    else
        # If server wasn't started by script, or if SERVER_PID is not set/valid,
        # try a general cleanup based on port, as per "Always Kill" logic.
        echo "Attempting general cleanup of server on port 8000..."
        EXISTING_PID_ON_TRAP=$(get_server_pid)
        if [ -n "$EXISTING_PID_ON_TRAP" ]; then
            echo "Found server process (PID: $EXISTING_PID_ON_TRAP) during trap. Sending kill signal..."
            kill "$EXISTING_PID_ON_TRAP"
            sleep 0.5 # Give it a moment
            if ps -p "$EXISTING_PID_ON_TRAP" > /dev/null; then kill -9 "$EXISTING_PID_ON_TRAP"; fi
        fi
    fi
    # Attempt to deactivate virtual environment if sourced
    if declare -f deactivate > /dev/null; then
        echo "Deactivating virtual environment..."
        deactivate
    fi
    exit 1
}
trap cleanup INT TERM


# Check if the virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_EXEC" -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment. Exiting."
        exit 1
    fi
    echo "Virtual environment created."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt pytest httpx pytest-asyncio email-validator
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies. Exiting."
    cleanup # Attempt cleanup
    exit 1
fi


SERVER_PID_EXISTING=$(get_server_pid)
SERVER_STARTED_BY_SCRIPT=false # Default to false

# Kill any existing server on port 8000 before starting a new one
if [ -n "$SERVER_PID_EXISTING" ]; then
    echo "An API server appears to be already running (PID: $SERVER_PID_EXISTING) on port 8000. Attempting to stop it..."
    kill "$SERVER_PID_EXISTING"
    sleep 1 # Give it a moment to shut down
    if ps -p "$SERVER_PID_EXISTING" > /dev/null; then
        echo "Server (PID: $SERVER_PID_EXISTING) did not stop gracefully. Sending kill -9..."
        kill -9 "$SERVER_PID_EXISTING"
        sleep 1
    fi
    # Verify it's stopped
    SERVER_PID_EXISTING=$(get_server_pid)
    if [ -n "$SERVER_PID_EXISTING" ]; then
        echo "WARN: Failed to stop existing server (PID: $SERVER_PID_EXISTING). Tests may be affected."
    else
        echo "Existing server on port 8000 stopped."
    fi
fi

# Start the server in the background
echo "Starting the API server..."
"$PYTHON_EXEC" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
SERVER_PID=$! # Get the PID of the uvicorn process started by this script
SERVER_STARTED_BY_SCRIPT=true
echo "API Server started with PID: $SERVER_PID. Logs in uvicorn.log"

# Wait for the server to start (application level check)
echo "Waiting for server application to respond..."
MAX_RETRIES=20
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check a known responsive path that doesn't require auth and returns 200
    if curl -s --head http://localhost:8000/docs | grep "200 OK" > /dev/null; then
        echo "Server application responded successfully!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2 # Increased sleep from 1 to 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Failed to get a successful response from the server application. Exiting."
    if ps -p "$SERVER_PID" > /dev/null; then
        kill "$SERVER_PID" # Kill the server we started
    fi
    cleanup # Attempt cleanup
    exit 1
fi


# Run functional tests
echo "Running functional tests..."
"$PYTHON_EXEC" -m pytest tests/test_functional.py -v

# Run vulnerability tests
echo "Running vulnerability tests..."
"$PYTHON_EXEC" -m pytest tests/test_vulnerabilities.py -v

# Run traffic generator for a short period
echo "Running traffic generator for 10 seconds..."
"$PYTHON_EXEC" traffic_generator.py --rps 2 --duration 10

# --- Server Stop Logic (Always attempt to stop if it was started by this script) ---
if [ "$SERVER_STARTED_BY_SCRIPT" = true ]; then
    echo "Stopping the API server (PID: $SERVER_PID) that was started by this script..."
    if ps -p "$SERVER_PID" > /dev/null; then # Check if our specific PID process still exists
        kill "$SERVER_PID"
        wait "$SERVER_PID" 2>/dev/null # Wait for it to actually terminate
        echo "Server (PID: $SERVER_PID) stopped."

        # Extra check to see if port is free
        FINAL_CHECK_PID=$(get_server_pid)
        if [ -n "$FINAL_CHECK_PID" ]; then
             echo "WARN: Port 8000 is still in use by PID $FINAL_CHECK_PID after attempting to stop PID $SERVER_PID."
        fi
    else
        echo "Server (PID: $SERVER_PID) was not running or already stopped by the time cleanup was reached."
    fi
else
    # This case should ideally not be reached if we kill existing servers at the start.
    # But as a fallback:
    echo "Server was not started by this script. Checking if port 8000 is in use by another process..."
    FINAL_CHECK_PID=$(get_server_pid)
    if [ -n "$FINAL_CHECK_PID" ]; then
         echo "WARN: Port 8000 is still in use by PID $FINAL_CHECK_PID. This script did not start it."
    fi
fi


# Deactivate the virtual environment
echo "Deactivating virtual environment..."
if declare -f deactivate > /dev/null; then
    deactivate
else
    echo "deactivate function not found (perhaps not in a virtual environment or already deactivated)."
fi


echo "----------------------------------------"
echo "Verification complete"
echo "----------------------------------------"