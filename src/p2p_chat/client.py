import asyncio
import argparse

DEFAULT_HOST = '127.0.0.1'  # Server IP
DEFAULT_PORT = 5000  # Server Port

async def handle_client(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Connects to the server and enables private messaging."""
    reader, writer = await asyncio.open_connection(host, port)

    # Receive and set username
    username_prompt = await reader.read(1024)
    print(username_prompt.decode(), end=" ")
    username = input()
    writer.write(username.encode() + b'\n')
    await writer.drain()

    print("Type 'TO_USER: message' to send a message. Type '!check' to view stored messages. Type 'exit' to disconnect.")

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

def main(host=DEFAULT_HOST, port=DEFAULT_PORT):
    """Main function to run the client."""
    asyncio.run(handle_client(host, port))

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat Client')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    args = parser.parse_args()
    
    main(args.host, args.port)

if __name__ == "__main__":
    main_entry()