#!/bin/bash
# stop_p2p_chat.sh - Script to stop all P2P Chat services

echo "Stopping P2P Chat services..."

# Check if services.pid file exists
if [ ! -f services.pid ]; then
  echo "Error: services.pid file not found."
  echo "Unable to automatically stop services."
  echo "You may need to stop them manually using 'pkill' or 'kill'."
  exit 1
fi

# Load PIDs from the file
source services.pid

# Stop services in reverse order
# Web Server
if [ -n "$WEB_SERVER_PID" ]; then
  echo "Stopping Web Server (PID: $WEB_SERVER_PID)..."
  kill $WEB_SERVER_PID 2>/dev/null || echo "Web Server already stopped"
fi

# WebSocket Bridge
if [ -n "$WEBSOCKET_BRIDGE_PID" ]; then
  echo "Stopping WebSocket Bridge (PID: $WEBSOCKET_BRIDGE_PID)..."
  kill $WEBSOCKET_BRIDGE_PID 2>/dev/null || echo "WebSocket Bridge already stopped"
fi

# Thermometer Service
if [ -n "$THERMOMETER_PID" ]; then
  echo "Stopping Thermometer Service (PID: $THERMOMETER_PID)..."
  kill $THERMOMETER_PID 2>/dev/null || echo "Thermometer Service already stopped"
fi

# Chat Server
if [ -n "$CHAT_SERVER_PID" ]; then
  echo "Stopping Chat Server (PID: $CHAT_SERVER_PID)..."
  kill $CHAT_SERVER_PID 2>/dev/null || echo "Chat Server already stopped"
fi

# Message API
if [ -n "$MESSAGE_API_PID" ]; then
  echo "Stopping Message API (PID: $MESSAGE_API_PID)..."
  kill $MESSAGE_API_PID 2>/dev/null || echo "Message API already stopped"
fi

# Ask if MongoDB should be stopped too
read -p "Do you want to stop MongoDB as well? (y/n): " stop_mongo
if [[ $stop_mongo == [Yy]* ]]; then
  echo "Stopping MongoDB..."
  mongod --shutdown
  if [ $? -ne 0 ]; then
    echo "Failed to stop MongoDB gracefully. Trying force kill..."
    pkill -f mongod
  fi
  echo "MongoDB stopped"
fi

# Remove the PID file
rm services.pid

echo "All services stopped!"