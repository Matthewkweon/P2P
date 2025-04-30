#!/usr/bin/env python3
"""
P2P Chat Launcher (Docker-compatible version)
"""

import os
import sys
import time
import subprocess
import signal
import atexit
from threading import Thread
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Track processes to terminate at exit
processes = []

def run_process(command, name):
    """Run a process and add it to the processes list"""
    print(f"Starting {name}...")
    process = subprocess.Popen(command, shell=True)
    processes.append((process, name))
    return process

def cleanup():
    """Terminate all processes on exit"""
    print("\nShutting down services...")
    # Terminate in reverse order
    for process, name in reversed(processes):
        print(f"Stopping {name}...")
        try:
            process.terminate()
            process.wait(timeout=2)
        except:
            print(f"Force killing {name}...")
            try:
                process.kill()
            except:
                pass
    print("All services stopped")

# Register cleanup function to run at exit
atexit.register(cleanup)

# Create logs directory
if not os.path.exists("logs"):
    os.makedirs("logs")

# 1. Start message API
run_process(
    "python -m src.p2p_chat.message_api --host 0.0.0.0 --port 8000 > logs/message_api.log 2>&1",
    "Message API"
)
print("Message API is running (logs in logs/message_api.log)")
time.sleep(2)  # Wait for API to start

# 2. Start chat server
run_process(
    "python -m src.p2p_chat.server --host 0.0.0.0 --port 5000 --api-base http://localhost:8000 > logs/server.log 2>&1",
    "Chat Server"
)
print("Chat Server is running (logs in logs/server.log)")
time.sleep(1)  # Wait for server to start

# 3. Start web interface
run_process(
    "python -m src.p2p_chat.websocket_adapter --host 0.0.0.0 --port 8080 --server-host localhost --server-port 5000 --api-base http://localhost:8000 > logs/web.log 2>&1",
    "Web Interface"
)
print("Web Interface is running at http://0.0.0.0:8080/ (logs in logs/web.log)")

# 4. Start thermometer service
run_process(
    "python -m src.p2p_chat.services.thermometer --host localhost --port 5000 --api-base http://localhost:8000 > logs/thermometer.log 2>&1",
    "Thermometer Service"
)
print("Thermometer Service is running (logs in logs/thermometer.log)")

# 5. Start OpenAI bot if API key is set
if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]:
    run_process(
        "python -m src.p2p_chat.openai --host localhost --port 5000 --api-base http://localhost:8000 > logs/openai.log 2>&1",
        "OpenAI Bot"
    )
    print("OpenAI Bot is running (logs in logs/openai.log)")
else:
    print("Warning: OPENAI_API_KEY not set, OpenAI bot not started")

print("\nP2P Chat is now running. Press Ctrl+C to stop all services")
print("Monitor the log files in the logs/ directory for details")

try:
    # Keep the script running until interrupted
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # The cleanup function will handle termination
    pass