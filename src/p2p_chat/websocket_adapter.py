import asyncio
import json
import re
import argparse
from datetime import datetime, UTC
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

# Track active connections
active_connections = {}  # username -> WebSocket
connected_to_server = {}  # username -> (reader, writer)
server_host = "localhost"
server_port = 5000
api_base = "http://localhost:8000"

# Serve static files (assuming frontend is in a 'static' directory)
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the main HTML file
@app.get("/")
async def get_html():
    with open(static_path / "index.html", "r") as f:
        return HTMLResponse(content=f.read())

# Pattern to extract sender and message from server messages
MSG_PATTERN = re.compile(r'\[([^\]]+)\](?:\[([^\]]+)\])?\s+(.*)')
STORED_MSG_PATTERN = re.compile(r'\[Stored\]\s+\[([^]]+)\](?:\[([^]]+)\])?\s+(.*)')

# Parse server messages
def parse_server_message(message):
    # Check if this is a connection message with users list
    if message.startswith("Connected! Users online:"):
        try:
            # Extract just the usernames at the end, ignoring any HTTP headers
            user_section = message.split("Users online:")[-1].strip()
            # Find the last comma in the HTTP headers section if present
            if "Sec-WebSocket-Extensions:" in user_section:
                user_section = user_section.split("permessage-deflate; client_max_window_bits")[-1].strip()
                if user_section.startswith(","):
                    user_section = user_section[1:].strip()
            
            # Clean up any other HTTP header remnants
            clean_users = []
            for user in user_section.split(", "):
                # Skip HTTP headers
                if ":" in user or user.startswith("HTTP") or len(user) > 30:
                    continue
                # Only keep valid usernames (alphanumeric and a few special chars)
                if user and all(c.isalnum() or c in "_-." for c in user):
                    clean_users.append(user)
            
            return {
                "type": "login_success",
                "online_users": clean_users
            }
        except Exception as e:
            print(f"Error parsing user list: {e}")
    
    # Other message parsing continues as before
    if message.startswith("[Stored]"):
        match = STORED_MSG_PATTERN.match(message)
        if match:
            msg_type, timestamp, content = match.groups()
            return {
                "type": "stored",
                "sender": msg_type,
                "timestamp": timestamp,
                "message": content
            }
    else:
        match = MSG_PATTERN.match(message)
        if match:
            sender, timestamp, content = match.groups()
            return {
                "type": "chat",
                "sender": sender,
                "timestamp": timestamp or datetime.now(UTC).isoformat(),
                "message": content
            }
    
    # Default system message
    return {
        "type": "system",
        "message": message
    }

# Connect to chat server
async def connect_to_server(username, websocket, host=server_host, port=server_port):
    try:
        print(f"Attempting to connect to server at {host}:{port}")
        reader, writer = await asyncio.open_connection(host, port)
        
        # Read username prompt
        username_prompt = await reader.read(1024)
        
        # Send username
        writer.write(username.encode() + b'\n')
        await writer.drain()
        
        # Store connection
        connected_to_server[username] = (reader, writer)
        
        # Send success to client
        online_users = list(connected_to_server.keys())
        await websocket.send_json({
            "type": "login_success",
            "online_users": online_users
        })
        
        # Notify other users
        for user, conn in active_connections.items():
            if user != username:
                await conn.send_json({
                    "type": "user_joined",
                    "username": username,
                    "online_users": online_users
                })
        
        # Start listening for server messages
        asyncio.create_task(listen_server_messages(username, reader, websocket))
        
        return True
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return False

# Listen for messages from the chat server
async def listen_server_messages(username, reader, websocket):
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
                
            message = data.decode().strip()
            print(f"Raw server message: {message}")
            
            # Handle connection message with user list specially
            if "Connected! Users online:" in message:
                # Parse out clean user list
                msg_data = parse_server_message(message)
                await websocket.send_json(msg_data)
            # Handle special messages like stored messages or notifications
            elif message.startswith("[Stored]"):
                msg_data = parse_server_message(message)
                await websocket.send_json(msg_data)
            elif "[NOTIFICATION]" in message or "notification" in message.lower():
                # Try to extract JSON metadata if present
                try:
                    metadata_start = message.find('{')
                    metadata_end = message.rfind('}')
                    if metadata_start > 0 and metadata_end > metadata_start:
                        metadata_str = message[metadata_start:metadata_end+1]
                        metadata = json.loads(metadata_str)
                        clean_message = message[:metadata_start].strip()
                        
                        # Extract sender from notification format
                        sender = "System"
                        if "[" in clean_message and "]" in clean_message:
                            sender = clean_message[clean_message.find("[")+1:clean_message.find("]")]
                            clean_message = clean_message[clean_message.find("]")+1:].strip()
                        
                        await websocket.send_json({
                            "type": "notification",
                            "sender": sender,
                            "message": clean_message,
                            "metadata": metadata,
                            "timestamp": datetime.now(UTC).isoformat()
                        })
                    else:
                        # Regular message format
                        msg_data = parse_server_message(message)
                        await websocket.send_json(msg_data)
                except:
                    # Fall back to regular message parsing
                    msg_data = parse_server_message(message)
                    await websocket.send_json(msg_data)
            else:
                # Regular chat message
                msg_data = parse_server_message(message)
                await websocket.send_json(msg_data)
    except Exception as e:
        print(f"Error in server listener for {username}: {e}")
    finally:
        # Clean up connection
        if username in connected_to_server:
            _, writer = connected_to_server[username]
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
            del connected_to_server[username]

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    username = None
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle login
            if data["type"] == "login":
                username = data["username"]
                active_connections[username] = websocket
                
                # Get server host and port from client if provided
                host = data.get("server_host", server_host)
                port = int(data.get("server_port", server_port))
                
                print(f"Connecting user {username} to chat server at {host}:{port}")
                
                # Connect to chat server
                success = await connect_to_server(username, websocket, host, port)
                if not success:
                    await websocket.send_json({
                        "type": "system",
                        "message": f"Failed to connect to chat server at {host}:{port}"
                    })
                    break
            
            # Handle chat message
            elif data["type"] == "chat":
                if username and username in connected_to_server:
                    _, writer = connected_to_server[username]
                    
                    # Format message as expected by the server
                    if "recipient" in data:
                        server_msg = f"{data['recipient']}: {data['message']}"
                    else:
                        server_msg = data["message"]
                    
                    writer.write(server_msg.encode())
                    await writer.drain()
            
            # Handle commands
            elif data["type"] == "command":
                if username and username in connected_to_server:
                    _, writer = connected_to_server[username]
                    writer.write(data["command"].encode())
                    await writer.drain()
    
    except WebSocketDisconnect:
        if username:
            # Remove from active connections
            if username in active_connections:
                del active_connections[username]
            
            # Disconnect from server
            if username in connected_to_server:
                _, writer = connected_to_server[username]
                try:
                    # Try to send exit command
                    writer.write("exit".encode())
                    await writer.drain()
                except:
                    pass
                writer.close()
                try:
                    await writer.wait_closed()
                except:
                    pass
                del connected_to_server[username]
            
            # Notify other users
            online_users = list(connected_to_server.keys())
            for user, conn in active_connections.items():
                await conn.send_json({
                    "type": "user_left",
                    "username": username,
                    "online_users": online_users
                })
    
    except Exception as e:
        print(f"WebSocket error: {e}")
        if username:
            if username in active_connections:
                del active_connections[username]
            if username in connected_to_server:
                _, writer = connected_to_server[username]
                writer.close()
                try:
                    await writer.wait_closed()
                except:
                    pass
                del connected_to_server[username]

def main(server_addr="localhost", server_p=5000, api_url="http://localhost:8000", host="0.0.0.0", port=8080):
    global server_host, server_port, api_base
    server_host = server_addr
    server_port = server_p
    api_base = api_url
    
    import uvicorn
    uvicorn.run(app, host=host, port=port)

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat WebSocket Adapter')
    parser.add_argument('--host', default="0.0.0.0", help='WebSocket server host')
    parser.add_argument('--port', type=int, default=8080, help='WebSocket server port')
    parser.add_argument('--server-host', default="localhost", help='Chat server host')
    parser.add_argument('--server-port', type=int, default=5000, help='Chat server port')
    parser.add_argument('--api-base', default="http://localhost:8000", help='API base URL')
    args = parser.parse_args()
    
    main(args.server_host, args.server_port, args.api_base, args.host, args.port)

if __name__ == "__main__":
    main_entry()