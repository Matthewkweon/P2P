import asyncio
import httpx  
from datetime import datetime, timezone, UTC



HOST = '127.0.0.1'  # Localhost
PORT = 5000  # Server Port
clients = {}  # username -> (reader, writer)
API_BASE = 'http://127.0.0.1:8000'  # FastAPI address


async def send_message(writer, message):
    try:
        writer.write(message.encode())
        await writer.drain()
    except:
        pass  # Ignore write errors

async def store_message(sender, destination, message):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/messages/", json={
            "sender": sender,
            "destination": destination,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "type": "chat",
            "metadata": {}
        })


async def get_stored_messages(username):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/messages/{username}")
        messages = response.json().get("messages", [])
        return [
            f"[{msg['type'].upper()}][{msg['timestamp']}][{msg['sender']}] {msg['message']} {f'Metadata: {msg["metadata"]}' if msg.get('metadata') else ''}"
            for msg in messages
        ]

async def handle_client(reader, writer):
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

    # 🔄 Retrieve stored messages
    stored_msgs = await get_stored_messages(username)
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
                stored_msgs = await get_stored_messages(username)
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
                    await send_message(target_writer, f"[{username}][{timestamp}] {msg_content}\n")
                else:
                    await store_message(username, target_user, msg_content)
                    await send_message(writer, f"User '{target_user}' is offline. Message saved.\n")
            else:
                await send_message(writer, "Invalid format. Use: TO_USERNAME: MESSAGE\n")
    except:
        pass

    print(f"{username} disconnected.")
    del clients[username]
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
