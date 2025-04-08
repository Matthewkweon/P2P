import asyncio
import random
from datetime import datetime, UTC
import httpx

HOST = '127.0.0.1'
PORT = 5000
USERNAME = "thermometer1"
API_BASE = "http://127.0.0.1:8000"

subscribers = set()
running = True


async def store_message(sender, destination, message, msg_type="notification", metadata={}):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/messages/", json={
            "sender": sender,
            "destination": destination,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            "type": msg_type,
            "metadata": metadata
        })


async def handle_incoming(reader, writer):
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
                    await store_message(USERNAME, sender, "Reboot complete.", "notification")

                elif command == "range":
                    temps = [round(random.uniform(20.0, 25.0), 1) for _ in range(5)]
                    await store_message(
                        USERNAME,
                        sender,
                        "Temperature range data",
                        "notification",
                        {"temps": temps, "time": datetime.now(UTC).isoformat()}
                    )
                elif "unsubscribe" in command:
                    print(f"[THERMOMETER] {sender} unsubscribed from thermometer")
                    subscribers.discard(sender)
                    await store_message(USERNAME, sender, "Unsubscribed.", "notification")
                elif "subscribe" in command:
                    print(f"[THERMOMETER] {sender} subscribed to thermometer")
                    subscribers.add(sender)
                    await store_message(USERNAME, sender, "Subscription confirmed.", "notification")
                

        except Exception as e:
            print(f"[THERMOMETER ERROR] {e}")
            break


async def broadcast_temperature():
    while True:
        if subscribers:
            temperature = round(random.uniform(22.0, 24.0), 1)
            print(f"[THERMOMETER] Broadcasting to subscribers: {subscribers}")
            for sub in subscribers:
                await store_message(
                    USERNAME,
                    sub,
                    "Temperature update",
                    "notification",
                    {
                        "temperature": temperature,
                        "unit": "C",
                        "time": datetime.now(UTC).isoformat()
                    }
                )
        await asyncio.sleep(100) # Broadcast every 100 seconds


async def thermometer_client():
    reader, writer = await asyncio.open_connection(HOST, PORT)

    await reader.read(1024)  # Read prompt
    writer.write(USERNAME.encode() + b"\n")
    await writer.drain()

    await asyncio.gather(
        handle_incoming(reader, writer),
        broadcast_temperature()
    )


if __name__ == "__main__":
    asyncio.run(thermometer_client())
