import asyncio

HOST = '127.0.0.1'  # Localhost
PORT = 5000  # Server Port
clients = {}  # username -> (reader, writer)
pending_messages = {}  # username -> list of pending messages

async def send_message(writer, message):
    try:
        writer.write(message.encode())
        await writer.drain()
    except:
        pass  # Ignore write errors

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

    # Notify about current users
    await send_message(writer, f"Connected! Users online: {', '.join(clients.keys())}\n")

    # Deliver pending messages
    if username in pending_messages:
        for msg in pending_messages[username]:
            await send_message(writer, f"[Stored] {msg}\n")
        del pending_messages[username]  # Clear after delivering

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            message = data.decode().strip()
            if message.lower() == "exit":
                break

            # Expected format: "TO_USERNAME: MESSAGE"
            if ":" in message:
                target_user, msg_content = message.split(":", 1)
                target_user = target_user.strip()
                msg_content = msg_content.strip()

                full_msg = f"[{username}] {msg_content}"

                if target_user in clients:
                    _, target_writer = clients[target_user]
                    await send_message(target_writer, full_msg + "\n")
                else:
                    # Store message for later delivery
                    if target_user not in pending_messages:
                        pending_messages[target_user] = []
                    pending_messages[target_user].append(full_msg)
                    await send_message(writer, f"User '{target_user}' is offline. Message saved.\n")
            else:
                await send_message(writer, "Invalid format. Use: TO_USERNAME: MESSAGE\n")
    except:
        pass

    # Cleanup
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
