# src/p2p_chat/websocket_bridge.py
import asyncio
import json
import websockets
import logging
import signal
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
import argparse
from datetime import datetime, UTC

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("websocket_bridge.log")
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_WS_HOST = '0.0.0.0'  # WebSocket server host
DEFAULT_WS_PORT = 5051       # WebSocket server port
DEFAULT_TCP_HOST = '127.0.0.1'  # TCP chat server host
DEFAULT_TCP_PORT = 5050      # TCP chat server port
DEFAULT_API_BASE = 'http://127.0.0.1:8000'  # FastAPI address

# Global state
websocket_clients = {}  # username -> WebSocket connection
tcp_clients = {}        # username -> (reader, writer)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, you may want to restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Server status endpoint
@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "connected_websocket_clients": len(websocket_clients),
        "connected_tcp_clients": len(tcp_clients),
        "websocket_clients": list(websocket_clients.keys()),
        "tcp_clients": list(tcp_clients.keys())
    }

# Forward messages from WebSocket to TCP server
async def forward_to_tcp(username, message_data):
    if username not in tcp_clients:
        logger.warning(f"No TCP connection for user {username}")
        return False
    
    _, writer = tcp_clients[username]
    
    try:
        # Format message according to TCP server expectations
        if message_data.get('type') == 'command' and message_data.get('command') == '!check':
            writer.write("!check".encode())
        elif message_data.get('type') == 'chat':
            destination = message_data.get('destination', '')
            content = message_data.get('message', '')
            formatted_message = f"{destination}: {content}"
            writer.write(formatted_message.encode())
        else:
            # Handle other message types if needed
            return False
            
        await writer.drain()
        return True
    except Exception as e:
        logger.error(f"Error forwarding to TCP: {e}")
        if username in tcp_clients:
            del tcp_clients[username]
        return False

# Forward messages from TCP to WebSocket
async def forward_to_websocket(username, message):
    if username not in websocket_clients:
        logger.warning(f"No WebSocket connection for user {username}")
        return False
    
    ws = websocket_clients[username]
    
    try:
        # Parse message from TCP server format
        # In websocket_bridge.py, replace the parsing code for stored messages:

        if message.startswith("[Stored]"):
            # Handle stored message format: [Stored] [timestamp][sender] message
            try:
                logger.info(f"Parsing stored message: {message}")
                parts = message.split("]")
                
                if len(parts) >= 3:
                    # Extract message type, timestamp, and sender
                    type_part = parts[1].strip()[1:]  # Remove the leading [
                    type_timestamp = type_part.split("][")
                    
                    msg_type = "chat"  # Default type
                    if len(type_timestamp) > 1:
                        msg_type = type_timestamp[0].lower()
                        timestamp = type_timestamp[1]
                    else:
                        timestamp = type_timestamp[0]
                    
                    sender_content = parts[2].split("[")
                    if len(sender_content) > 1:
                        sender = sender_content[1].split("]")[0]
                    else:
                        sender = "System"
                    
                    # Extract message content - everything after the last bracket
                    msg_content = "]".join(parts[2:])
                    last_bracket_pos = msg_content.find("]")
                    if last_bracket_pos != -1:
                        msg_content = msg_content[last_bracket_pos+1:].strip()
                    
                    # Handle metadata if present
                    metadata = {}
                    if "Metadata:" in msg_content:
                        content_parts = msg_content.split("Metadata:")
                        msg_content = content_parts[0].strip()
                        try:
                            metadata_str = content_parts[1].strip()
                            # Try to parse metadata as JSON if it looks like JSON
                            if metadata_str.startswith("{") and metadata_str.endswith("}"):
                                import json
                                metadata = json.loads(metadata_str)
                        except:
                            logger.warning(f"Failed to parse metadata from: {content_parts[1]}")
                    
                    await ws.send_json({
                        "type": msg_type,
                        "sender": sender,
                        "message": msg_content,
                        "timestamp": timestamp,
                        "metadata": metadata
                    })
                    return True
            except Exception as e:
                logger.error(f"Error parsing stored message: {e}")
                # Fall back to sending as notification
                await ws.send_json({
                    "type": "notification",
                    "message": message,
                    "timestamp": datetime.now(UTC).isoformat()
                })
                return True
    except Exception as e:
        logger.error(f"Error forwarding to WebSocket: {e}")
        if username in websocket_clients:
            del websocket_clients[username]
        return False

# Connect to TCP server for a specific user
async def connect_to_tcp_server(username, host=DEFAULT_TCP_HOST, port=DEFAULT_TCP_PORT):
    try:
        logger.info(f"Connecting to TCP server at {host}:{port} for user {username}")
        reader, writer = await asyncio.open_connection(host, port)
        
        # Read username prompt
        prompt = await reader.read(1024)
        logger.info(f"TCP Server prompt: {prompt.decode()}")
        
        # Send username
        writer.write(f"{username}\n".encode())
        await writer.drain()
        
        # Read connection confirmation
        confirmation = await reader.read(1024)
        logger.info(f"TCP Server confirmation for {username}: {confirmation.decode()}")
        
        tcp_clients[username] = (reader, writer)
        
        # Forward confirmation to WebSocket
        if username in websocket_clients:
            await forward_to_websocket(username, confirmation.decode())
        
        return reader, writer
    except ConnectionRefusedError:
        logger.error(f"Connection refused to TCP server at {host}:{port}. Is the server running?")
        return None, None
    except Exception as e:
        logger.error(f"Error connecting to TCP server: {e}")
        return None, None

# Handle TCP messages
async def handle_tcp_messages(username, reader):
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                logger.info(f"TCP server closed connection for {username}")
                break
                
            message = data.decode()
            logger.info(f"TCP message for {username}: {message}")
            
            if username in websocket_clients:
                await forward_to_websocket(username, message)
    except ConnectionResetError:
        logger.error(f"TCP connection reset for {username}")
    except Exception as e:
        logger.error(f"Error handling TCP messages for {username}: {e}")
    finally:
        if username in tcp_clients:
            _, writer = tcp_clients[username]
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            del tcp_clients[username]
        
        # Notify the WebSocket client that the connection has been lost
        if username in websocket_clients:
            try:
                await websocket_clients[username].send_json({
                    "type": "notification",
                    "message": "Connection to chat server lost. Please reconnect.",
                    "timestamp": datetime.now(UTC).isoformat()
                })
            except:
                pass
        
        logger.info(f"TCP connection closed for {username}")

# WebSocket endpoint
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    websocket_clients[username] = websocket
    
    logger.info(f"WebSocket connection established for user: {username}")
    
    # Connect to TCP server
    reader, writer = await connect_to_tcp_server(username)
    if not reader or not writer:
        await websocket.send_json({
            "type": "error",
            "message": "Failed to connect to chat server. Is the server running?",
            "timestamp": datetime.now(UTC).isoformat()
        })
        await websocket.close()
        if username in websocket_clients:
            del websocket_clients[username]
        return
    
    # Start TCP message handler
    tcp_handler = asyncio.create_task(handle_tcp_messages(username, reader))
    
    try:
        # Handle WebSocket messages
        while True:
            message = await websocket.receive_json()
            logger.info(f"WebSocket message from {username}: {message}")
            
            # Forward to TCP server
            success = await forward_to_tcp(username, message)
            if not success:
                await websocket.send_json({
                    "type": "error",
                    "message": "Failed to send message to chat server.",
                    "timestamp": datetime.now(UTC).isoformat()
                })
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {username}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received from WebSocket client: {username}")
    except Exception as e:
        logger.error(f"WebSocket error for {username}: {e}")
    finally:
        # Cleanup WebSocket connection
        if username in websocket_clients:
            del websocket_clients[username]
            logger.info(f"Removed {username} from websocket_clients")
        
        # Cleanup TCP connection
        if username in tcp_clients:
            try:
                _, writer = tcp_clients[username]
                try:
                    writer.write("exit".encode())
                    await writer.drain()
                except:
                    logger.warning(f"Error sending exit command for {username}")
                
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    logger.warning(f"Error closing writer for {username}")
                
                del tcp_clients[username]
                logger.info(f"Removed {username} from tcp_clients")
            except Exception as e:
                logger.error(f"Error during TCP cleanup for {username}: {e}")
        
        # Cancel the TCP handler task if it exists
        if 'tcp_handler' in locals() and tcp_handler:
            try:
                tcp_handler.cancel()
                await asyncio.shield(asyncio.gather(tcp_handler, return_exceptions=True))
                logger.info(f"Canceled TCP handler task for {username}")
            except Exception as e:
                logger.error(f"Error canceling TCP handler for {username}: {e}")
        
        logger.info(f"Cleaned up connections for {username}")

# Graceful shutdown handler
def handle_shutdown(sig, frame):
    logger.info("Shutdown signal received, closing connections...")
    # Close all TCP connections
    for username, (_, writer) in tcp_clients.items():
        try:
            writer.close()
            logger.info(f"Closed TCP connection for {username}")
        except:
            pass
    
    logger.info("Exiting...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

# Run the server
def main(ws_host=DEFAULT_WS_HOST, ws_port=DEFAULT_WS_PORT, tcp_host=DEFAULT_TCP_HOST, tcp_port=DEFAULT_TCP_PORT):
    """Run the WebSocket bridge server."""
    logger.info(f"Starting WebSocket bridge on {ws_host}:{ws_port}")
    logger.info(f"Connecting to TCP server at {tcp_host}:{tcp_port}")
    
    global DEFAULT_TCP_HOST, DEFAULT_TCP_PORT
    DEFAULT_TCP_HOST = tcp_host
    DEFAULT_TCP_PORT = tcp_port
    
    try:
        uvicorn.run(app, host=ws_host, port=ws_port, log_level="info")
    except Exception as e:
        logger.error(f"Error starting WebSocket bridge: {e}")
        sys.exit(1)

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat WebSocket Bridge')
    parser.add_argument('--ws-host', default=DEFAULT_WS_HOST, help='WebSocket host')
    parser.add_argument('--ws-port', type=int, default=DEFAULT_WS_PORT, help='WebSocket port')
    parser.add_argument('--tcp-host', default=DEFAULT_TCP_HOST, help='TCP server host')
    parser.add_argument('--tcp-port', type=int, default=DEFAULT_TCP_PORT, help='TCP server port')
    args = parser.parse_args()
    
    main(args.ws_host, args.ws_port, args.tcp_host, args.tcp_port)

if __name__ == "__main__":
    main_entry()