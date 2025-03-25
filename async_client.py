import asyncio

HOST = '127.0.0.1'  # Server IP
PORT = 5000  # Server Port

async def handle_client():
    """Connects to the server and enables private messaging."""
    reader, writer = await asyncio.open_connection(HOST, PORT)

    # Receive and set username
    username_prompt = await reader.read(1024)
    print(username_prompt.decode(), end=" ")
    username = input()
    writer.write(username.encode() + b'\n')
    await writer.drain()

    async def receive():
        """Handles incoming messages from the server."""
        while True:
            try:
                data = await reader.read(1024)
                if not data:
                    break
                print(f"\n{data.decode()}", end=" ")
            except:
                break

    async def send():
        """Handles sending messages to the server."""
        while True:
            message = await asyncio.to_thread(input, "You: ")
            if message.lower() == "exit":
                writer.write("exit".encode())
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                break
            writer.write(message.encode())
            await writer.drain()

    # Run send and receive tasks concurrently
    await asyncio.gather(receive(), send())

if __name__ == "__main__":
    asyncio.run(handle_client())
