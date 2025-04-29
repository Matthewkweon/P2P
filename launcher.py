#!/usr/bin/env python3
"""
Simple P2P Chat Launcher
"""

import os
import sys
import time
import subprocess
import signal
import atexit
from threading import Thread

# Track processes to terminate at exit
processes = []

def find_file(filenames):
    """Find the first file that exists from a list of possible filenames"""
    for filename in filenames:
        if os.path.exists(filename):
            return filename
    return None

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

# Find Python files
message_api_file = find_file(["message_api.py", "src/p2p_chat/message_api.py"])
server_file = find_file(["async_server.py", "server.py", "src/p2p_chat/server.py"])
websocket_file = find_file(["websocket_adapter.py", "src/p2p_chat/websocket_adapter.py"])
thermometer_file = find_file(["thermometer.py", "src/p2p_chat/services/thermometer.py"])
openai_file = find_file(["openai.py", "src/p2p_chat/openai.py"])

# Create logs directory
if not os.path.exists("logs"):
    os.makedirs("logs")

# 1. Start message API
if message_api_file:
    run_process(
        f"python {message_api_file} > logs/message_api.log 2>&1",
        "Message API"
    )
    print("Message API is running (logs in logs/message_api.log)")
    time.sleep(2)  # Wait for API to start
else:
    print("Error: message_api.py not found!")
    sys.exit(1)

# 2. Start chat server
if server_file:
    run_process(
        f"python {server_file} > logs/server.log 2>&1",
        "Chat Server"
    )
    print("Chat Server is running (logs in logs/server.log)")
    time.sleep(1)  # Wait for server to start
else:
    print("Error: async_server.py not found!")
    sys.exit(1)

# 3. Start web interface
if websocket_file:
    run_process(
        f"python {websocket_file} > logs/web.log 2>&1",
        "Web Interface"
    )
    print("Web Interface is running at http://localhost:8080/ (logs in logs/web.log)")
else:
    print("Warning: websocket_adapter.py not found, web interface not started")

# 4. Start thermometer service
if thermometer_file:
    run_process(
        f"python {thermometer_file} > logs/thermometer.log 2>&1",
        "Thermometer Service"
    )
    print("Thermometer Service is running (logs in logs/thermometer.log)")
else:
    print("Warning: thermometer.py not found, thermometer service not started")

# 5. Start OpenAI bot
if openai_file and "OPENAI_API_KEY" in os.environ:
    run_process(
        f"python {openai_file} > logs/openai.log 2>&1",
        "OpenAI Bot"
    )
    print("OpenAI Bot is running (logs in logs/openai.log)")
elif openai_file:
    print("Warning: OPENAI_API_KEY not set, OpenAI bot not started")
else:
    print("Warning: openai.py not found, OpenAI bot not started")

print("\nP2P Chat is now running. Press Ctrl+C to stop all services")
print("Monitor the log files in the logs/ directory for details")

try:
    # Keep the script running until interrupted
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    # The cleanup function will handle termination
    pass