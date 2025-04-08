import asyncio
import random
import argparse
from datetime import datetime, UTC
import httpx

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5000
DEFAULT_USERNAME = "thermometer1"
DEFAULT_API_BASE = "http://127.0.0.1:8000"

subscribers = set()
running = True

async def store_message(sender, destination, message, msg_type="notification", metadata={}, api_base=DEFAULT_API_BASE):
    async with httpx.AsyncClient() as client:
        await client.post(f"{api_base}/messages/", json={
            "sender": sender,
            "destination": destination,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "type": msg_type,
            "metadata": metadata
        })

async def handle_incoming(reader, writer, username=DEFAULT_USERNAME, api_base=DEFAULT_API_BASE):
    global running

    while running:
        try:
            data = await reader.read(1024)
            if not data:
                break

            msg = data.decode(errors="ignore").strip()
            print(f"[THERMOMETER] Received raw message: {msg}")

            # Expect format: [username][timestamp] command
            if msg.startswith("[") and "]" in msg:
                sender = msg.split("]")[0][1:]  # extract between first [ ]
                command = msg.split("]")[-1].strip().lower()

                print(f"[THERMOMETER] Parsed sender: {sender}, command: '{command}'")

                if command == "reboot":
                    print("[THERMOMETER] Rebooting...")
                    await asyncio.sleep(2)
                    await store_message(username, sender, "Reboot complete.", "notification", {}, api_base)

                elif command == "range":
                    temps = [round(random.uniform(20.0, 25.0), 1) for _ in range(5)]
                    await store_message(
                        username,
                        sender,
                        "Temperature range data",
                        "notification",
                        {"temps": temps, "time": datetime.now(UTC).isoformat()},
                        api_base
                    )
                elif "unsubscribe" in command:
                    print(f"[THERMOMETER] {sender} unsubscribed from thermometer")
                    subscribers.discard(sender)
                    await store_message(username, sender, "Unsubscribed.", "notification", {}, api_base)
                elif "subscribe" in command:
                    print(f"[THERMOMETER] {sender} subscribed to thermometer")
                    subscribers.add(sender)
                    await store_message(username, sender, "Subscription confirmed.", "notification", {}, api_base)

        except Exception as e:
            print(f"[THERMOMETER ERROR] {e}")
            break

async def broadcast_temperature(username=DEFAULT_USERNAME, api_base=DEFAULT_API_BASE, interval=100):
    while True:
        if subscribers:
            temperature = round(random.uniform(22.0, 24.0), 1)
            print(f"[THERMOMETER] Broadcasting to subscribers: {subscribers}")
            for sub in subscribers:
                await store_message(
                    username,
                    sub,
                    "Temperature update",
                    "notification",
                    {
                        "temperature": temperature,
                        "unit": "C",
                        "time": datetime.now(UTC).isoformat()
                    },
                    api_base
                )
        await asyncio.sleep(interval)  # Broadcast interval

async def run_thermometer(host=DEFAULT_HOST, port=DEFAULT_PORT, username=DEFAULT_USERNAME, api_base=DEFAULT_API_BASE, interval=100):
    reader, writer = await asyncio.open_connection(host, port)

    await reader.read(1024)  # Read prompt
    writer.write(username.encode() + b"\n")
    await writer.drain()

    await asyncio.gather(
        handle_incoming(reader, writer, username, api_base),
        broadcast_temperature(username, api_base, interval)
    )

def main(host=DEFAULT_HOST, port=DEFAULT_PORT, username=DEFAULT_USERNAME, api_base=DEFAULT_API_BASE, interval=100):
    """Main function to run the thermometer service."""
    print(f"Starting thermometer service as '{username}'")
    print(f"Connecting to chat server at {host}:{port}")
    print(f"Using API at {api_base}")
    print(f"Broadcasting temperature every {interval} seconds")
    
    asyncio.run(run_thermometer(host, port, username, api_base, interval))

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat Thermometer Service')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    parser.add_argument('--username', default=DEFAULT_USERNAME, help='Service username')
    parser.add_argument('--api-base', default=DEFAULT_API_BASE, help='API base URL')
    parser.add_argument('--interval', type=int, default=100, help='Broadcast interval in seconds')
    args = parser.parse_args()
    
    main(args.host, args.port, args.username, args.api_base, args.interval)

if __name__ == "__main__":
    main_entry()