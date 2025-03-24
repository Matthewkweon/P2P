import asyncio

HOST = '127.0.0.1'  # Localhost
PORT = 5000         # Server Port

async def handle_client(reader, writer):
    """Handles a connected client."""
    addr = writer.get_extra_info('peername')
    print(f"Client connected: {addr}")

    # Create a task to receive messages
    async def receive():
        while True:
            try:
                data = await reader.read(1024)  # Non-blocking read
                if not data:
                    break
                print(f"\n{data.decode()}")
            except:
                break
    
    # Create a task to send messages
    async def send():
        while True:
            message = await asyncio.to_thread(input)
            writer.write(message.encode())
            await writer.drain()
            if message.lower() == "exit":
                writer.close()
                await writer.wait_closed()
                break

    # Run both tasks concurrently
    await asyncio.gather(receive(), send())

async def main():
    """Starts the server and listens for connections."""
    server = await asyncio.start_server(handle_client, HOST, PORT)
    addr = server.sockets[0].getsockname()
    print(f"Server is running on {addr}")

    async with server:
        await server.serve_forever()

# Run the server
asyncio.run(main())
