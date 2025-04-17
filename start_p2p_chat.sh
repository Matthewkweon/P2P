#!/bin/bash
# start_p2p_chat.sh - Script to start all P2P Chat services

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check for required commands
if ! command_exists python; then
  echo "Error: Python is not installed or not in PATH"
  exit 1
fi

if ! command_exists mongod; then
  echo "Warning: MongoDB is not installed or not in PATH"
  echo "Make sure MongoDB is running before continuing"
  read -p "Press Enter to continue or Ctrl+C to abort..."
fi

# Create a directory for log files
mkdir -p logs

echo "Starting P2P Chat services..."

# Check if MongoDB is running
mongo_running=$(ps aux | grep -v grep | grep -c mongod)
if [ $mongo_running -eq 0 ]; then
  echo "Starting MongoDB..."
  mongod --fork --logpath=logs/mongodb.log --dbpath=./data/db
  if [ $? -ne 0 ]; then
    echo "Failed to start MongoDB. Make sure it's installed and configured properly."
    exit 1
  fi
else
  echo "MongoDB is already running"
fi

# Start the Message API
echo "Starting Message API..."
p2p-chat-api --host 127.0.0.1 --port 8000 > logs/message_api.log 2>&1 &
MESSAGE_API_PID=$!
echo "Message API started with PID $MESSAGE_API_PID"

# Wait for the API to be ready
echo "Waiting for Message API to start..."
sleep 3

# Start the Chat Server
echo "Starting Chat Server..."
p2p-chat-server --host 127.0.0.1 --port 5000 --api-base http://127.0.0.1:8000 > logs/chat_server.log 2>&1 &
CHAT_SERVER_PID=$!
echo "Chat Server started with PID $CHAT_SERVER_PID"

# Start the Thermometer Service
echo "Starting Thermometer Service..."
p2p-chat-thermometer --host 127.0.0.1 --port 5000 --username thermometer1 --api-base http://127.0.0.1:8000 --interval 100 > logs/thermometer.log 2>&1 &
THERMOMETER_PID=$!
echo "Thermometer Service started with PID $THERMOMETER_PID"

# Start the WebSocket Bridge
echo "Starting WebSocket Bridge..."
p2p-chat-websocket --ws-host 0.0.0.0 --ws-port 5001 --tcp-host 127.0.0.1 --tcp-port 5000 > logs/websocket_bridge.log 2>&1 &
WEBSOCKET_BRIDGE_PID=$!
echo "WebSocket Bridge started with PID $WEBSOCKET_BRIDGE_PID"

# Start the Web Server
echo "Starting Web Server..."
p2p-chat-web --host 127.0.0.1 --port 3000 > logs/web_server.log 2>&1 &
WEB_SERVER_PID=$!
echo "Web Server started with PID $WEB_SERVER_PID"

# Save PIDs to a file for easier shutdown
echo "Saving service PIDs to services.pid"
cat > services.pid << EOF
MESSAGE_API_PID=$MESSAGE_API_PID
CHAT_SERVER_PID=$CHAT_SERVER_PID
THERMOMETER_PID=$THERMOMETER_PID
WEBSOCKET_BRIDGE_PID=$WEBSOCKET_BRIDGE_PID
WEB_SERVER_PID=$WEB_SERVER_PID
EOF

echo "All services started!"
echo ""
echo "To access the web interface, open your browser and navigate to:"
echo "http://localhost:3000"
echo ""
echo "To stop all services, run the stop_p2p_chat.sh script"
echo ""
echo "Service logs are available in the logs directory:"
echo "- Message API: logs/message_api.log"
echo "- Chat Server: logs/chat_server.log"
echo "- Thermometer: logs/thermometer.log"
echo "- WebSocket Bridge: logs/websocket_bridge.log"
echo "- Web Server: logs/web_server.log"