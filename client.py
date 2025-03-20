import asyncio

HOST = '127.0.0.1'  # Server IP
PORT = 5000         # Must match the server port

async def handle_client():
    """Connects to the server and handles bidirectional communication."""
    reader, writer = await asyncio.open_connection(HOST, PORT)
    print(f"Connected to server at {HOST}:{PORT}")

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

# Run the client
asyncio.run(handle_client())
