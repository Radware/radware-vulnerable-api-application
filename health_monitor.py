#!/usr/bin/env python3
"""
Server Health Monitor for Radware Vulnerable API

This script monitors the API server and restarts it if it becomes unresponsive.
It's designed to run alongside the traffic generator to ensure continuous API availability.

Usage:
    python health_monitor.py [--interval SECONDS] [--max-failures MAX_FAILURES]
"""

import argparse
import subprocess
import time
import os
import signal
import sys
from datetime import datetime
import requests

# Configuration
BASE_URL = "http://localhost:8000"
DEFAULT_CHECK_INTERVAL = 30  # seconds
DEFAULT_MAX_FAILURES = 3     # restart after this many consecutive failures

def log_event(message, is_error=False):
    """Log an event with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_type = "ERROR" if is_error else "INFO"
    print(f"[{timestamp}] [{log_type}] {message}")
    sys.stdout.flush()  # Ensure logs are written immediately

def check_server_health():
    """Check if the API server is responsive."""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            return True
        log_event(f"Server responded with status code: {response.status_code}", True)
        return False
    except Exception as e:
        log_event(f"Server health check failed: {str(e)}", True)
        return False

def restart_server():
    """Restart the API server."""
    log_event("Attempting to restart the API server...")
    
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Kill any existing uvicorn processes
    try:
        subprocess.run(
            "pkill -f 'uvicorn app.main:app'",
            shell=True,
            check=False
        )
        time.sleep(2)  # Give it time to shut down
    except Exception as e:
        log_event(f"Error stopping existing server: {str(e)}", True)
    
    # Start a new server process
    try:
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the server to start
        for _ in range(5):
            time.sleep(2)
            if check_server_health():
                log_event("Server successfully restarted")
                return True
        
        log_event("Failed to restart the server", True)
        return False
    except Exception as e:
        log_event(f"Error starting server: {str(e)}", True)
        return False

def monitor_server(interval, max_failures):
    """Continuously monitor server health and restart if necessary."""
    log_event(f"Starting health monitor (interval: {interval}s, max failures: {max_failures})")
    
    consecutive_failures = 0
    
    try:
        while True:
            if check_server_health():
                consecutive_failures = 0
                log_event("Server health check: OK")
            else:
                consecutive_failures += 1
                log_event(f"Server health check: FAILED ({consecutive_failures}/{max_failures})")
                
                if consecutive_failures >= max_failures:
                    log_event(f"Maximum failures ({max_failures}) reached. Restarting server...")
                    restart_server()
                    consecutive_failures = 0
            
            time.sleep(interval)
    except KeyboardInterrupt:
        log_event("Health monitor stopped by user")
    except Exception as e:
        log_event(f"Unexpected error in health monitor: {str(e)}", True)

def main():
    parser = argparse.ArgumentParser(description="Monitor and maintain API server health")
    parser.add_argument("--interval", type=int, default=DEFAULT_CHECK_INTERVAL, 
                        help=f"Health check interval in seconds (default: {DEFAULT_CHECK_INTERVAL})")
    parser.add_argument("--max-failures", type=int, default=DEFAULT_MAX_FAILURES,
                        help=f"Maximum consecutive failures before restart (default: {DEFAULT_MAX_FAILURES})")
    args = parser.parse_args()
    
    monitor_server(args.interval, args.max_failures)

if __name__ == "__main__":
    main()
