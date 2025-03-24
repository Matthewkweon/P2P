import asyncio

HOST = '127.0.0.1'  # Localhost
PORT = 5000  # Server Port
clients = {}  # Stores username -> (reader, writer)

async def send_message(writer, message):
    """Send a message to a specific client."""
    try:
        writer.write(message.encode())
        await writer.drain()
    except:
        pass  # Ignore errors from disconnected clients

async def handle_client(reader, writer):
    """Handles communication with a connected client."""
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

    # Notify the client of the available users
    await send_message(writer, f"Connected! Users online: {', '.join(clients.keys())}\n")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            message = data.decode().strip()
            if message.lower() == "exit":
                break

            # Expected format: "TO:USERNAME MESSAGE"
            if ":" in message:
                target_user, msg_content = message.strip().split(":", 1)
                target_user = target_user.strip()
                msg_content = msg_content.strip()

                if target_user in clients:
                    _, target_writer = clients[target_user]
                    await send_message(target_writer, f"[{username}] {msg_content}\n")
                else:
                    await send_message(writer, f"User '{target_user}' not found.\n")
            else:
                await send_message(writer, "Invalid format. Use: USERNAME: MESSAGE\n")
    except:
        pass  # Handle disconnections

    # Cleanup when client disconnects
    print(f"{username} disconnected.")
    del clients[username]
    writer.close()
    await writer.wait_closed()

async def main():
    """Starts the server and listens for client connections."""
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server running on {addr}")

    async with server:
        await server.serve_forever()

# Run the server
if __name__ == "__main__":
    asyncio.run(main())
