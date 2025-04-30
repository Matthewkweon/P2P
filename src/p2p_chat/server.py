import asyncio
import httpx
import argparse
from datetime import datetime, UTC

DEFAULT_HOST = '0.0.0.0'  # Localhost
DEFAULT_PORT = 5000  # Server Port
DEFAULT_API_BASE = 'http://localhost:8000'  # FastAPI address

clients = {}  # username -> (reader, writer)

async def send_message(writer, message):
    try:
        writer.write(message.encode())
        await writer.drain()
        return True  # Message sent successfully
    except:
        return False  # Failed to send message

async def store_message(sender, destination, message, api_base=DEFAULT_API_BASE):
    async with httpx.AsyncClient() as client:
        await client.post(f"{api_base}/messages/", json={
            "sender": sender,
            "destination": destination,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "chat",
            "metadata": {}
        })

async def get_stored_messages(username, api_base=DEFAULT_API_BASE):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{api_base}/messages/{username}")
        messages = response.json().get("messages", [])
        return [
            f"[{msg['type'].upper()}][{msg['timestamp']}][{msg['sender']}] {msg['message']} {f'Metadata: {msg['metadata']}' if msg.get('metadata') else ''}"
            for msg in messages
        ]

async def handle_client(reader, writer, api_base=DEFAULT_API_BASE):
    writer.write("Enter your username: ".encode())
    await writer.drain()
    username = (await reader.read(1024)).decode().strip()

    if username in clients:
        writer.write("Username already taken. Disconnecting...\n".encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    clients[username] = (reader, writer)
    print(f"{username} connected.")

    await send_message(writer, f"Connected! Users online: {', '.join(clients.keys())}\n")

    # Retrieve stored messages
    stored_msgs = await get_stored_messages(username, api_base)
    for msg in stored_msgs:
        await send_message(writer, f"[Stored] {msg}\n")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            message = data.decode().strip()
            if message.lower() == "exit":
                break
            elif message.lower() == "!check":
                stored_msgs = await get_stored_messages(username, api_base)
                for msg in stored_msgs:
                    await send_message(writer, f"[Stored] {msg}\n")
                continue

            if ":" in message:
                target_user, msg_content = message.split(":", 1)
                target_user = target_user.strip()
                msg_content = msg_content.strip()

                timestamp = datetime.now(UTC).isoformat()

                if target_user in clients:
                    _, target_writer = clients[target_user]
                    # Try to send message directly
                    sent = await send_message(target_writer, f"[{username}][{timestamp}] {msg_content}\n")
                    if not sent:
                        # If failed to send (connection might be stale), store it
                        print(f"Failed to send message to {target_user}, storing instead.")
                        await store_message(username, target_user, msg_content, api_base)
                        await send_message(writer, f"Message to '{target_user}' couldn't be delivered. Message saved.\n")
                else:
                    # User is offline, store the message
                    await store_message(username, target_user, msg_content, api_base)
                    await send_message(writer, f"User '{target_user}' is offline. Message saved.\n")
            else:
                await send_message(writer, "Invalid format. Use: TO_USERNAME: MESSAGE\n")
    except:
        pass

    print(f"{username} disconnected.")
    del clients[username]
    writer.close()
    await writer.wait_closed()

async def run_server(host=DEFAULT_HOST, port=DEFAULT_PORT, api_base=DEFAULT_API_BASE):
    """Starts the chat server."""
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, api_base), 
        host, 
        port
    )
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")
    print(f"Using API at {api_base}")
    
    async with server:
        await server.serve_forever()

def main(host=DEFAULT_HOST, port=DEFAULT_PORT, api_base=DEFAULT_API_BASE):
    """Main function to run the server."""
    asyncio.run(run_server(host, port, api_base))

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat Server')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    parser.add_argument('--api-base', default=DEFAULT_API_BASE, help='API base URL')
    args = parser.parse_args()
    
    main(args.host, args.port, args.api_base)

if __name__ == "__main__":
    main_entry()