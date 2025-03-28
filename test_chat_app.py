# test_chat_app.py
import asyncio
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

# Session-scoped event loop fixture to prevent premature closing.
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# ----- Tests for message_api.py -----
from message_api import app, collection

@pytest.fixture(autouse=True)
async def cleanup_db():
    # Clear the collection before and after each test.
    await collection.delete_many({})
    yield
    await collection.delete_many({})

@pytest.mark.asyncio
async def test_store_message():
    test_message = {
        "sender": "alice",
        "destination": "bob",
        "message": "Hello Bob!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "chat",
        "metadata": {}
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/messages/", json=test_message)
        assert response.status_code == 200
        assert response.json() == {"status": "stored"}

@pytest.mark.asyncio
async def test_get_messages():
    # First, store a message.
    test_message = {
        "sender": "alice",
        "destination": "bob",
        "message": "Hello Bob!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "chat",
        "metadata": {}
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        post_resp = await client.post("/messages/", json=test_message)
        assert post_resp.status_code == 200

        # Retrieve stored messages for "bob"
        get_resp = await client.get("/messages/bob")
        data = get_resp.json()
        assert "messages" in data
        assert len(data["messages"]) == 2
        retrieved_msg = data["messages"][0]
        assert retrieved_msg["sender"] == "alice"
        assert "Hello Bob!" in retrieved_msg["message"]

        # A subsequent retrieval should return an empty list (messages are deleted after retrieval)
        get_resp2 = await client.get("/messages/bob")
        data2 = get_resp2.json()
        assert data2["messages"] == []

# ----- Tests for async_server.py -----
from async_server import main as server_main, clients

@pytest.fixture
async def fake_storage(monkeypatch):
    storage = {}

    async def fake_store_message(sender, destination, message):
        storage.setdefault(destination, []).append(message)

    async def fake_get_stored_messages(username):
        msgs = storage.get(username, [])
        storage[username] = []
        return [f"[CHAT][dummy-timestamp][{username}] {msg}" for msg in msgs]

    monkeypatch.setattr("async_server.store_message", fake_store_message)
    monkeypatch.setattr("async_server.get_stored_messages", fake_get_stored_messages)
    yield storage
    storage.clear()

@pytest.mark.asyncio
async def test_chat_server_offline_message(fake_storage):
    # Start the server in a background task.
    server_task = asyncio.create_task(server_main())
    await asyncio.sleep(0.1)

    # --- Client 1 (Alice) connects and sends a message to offline user Bob ---
    reader1, writer1 = await asyncio.open_connection('127.0.0.1', 5000)
    data = await reader1.read(1024)
    assert "Enter your username:" in data.decode()

    writer1.write(b"alice\n")
    await writer1.drain()
    data = await reader1.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer1.write(b"bob: Hello Bob!\n")
    await writer1.drain()
    data = await reader1.read(1024)
    assert "User 'bob' is offline" in data.decode()

    writer1.write(b"exit")
    await writer1.drain()
    writer1.close()
    await writer1.wait_closed()

    # --- Client 2 (Bob) connects and checks for stored messages ---
    reader2, writer2 = await asyncio.open_connection('127.0.0.1', 5000)
    data = await reader2.read(1024)
    assert "Enter your username:" in data.decode()

    writer2.write(b"bob\n")
    await writer2.drain()
    data = await reader2.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer2.write(b"!check\n")
    await writer2.drain()
    data = await reader2.read(1024)
    decoded = data.decode()
    assert "Hello Bob!" in decoded

    writer2.write(b"exit")
    await writer2.drain()
    writer2.close()
    await writer2.wait_closed()

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_chat_server_online_message(monkeypatch):
    async def dummy_store_message(sender, destination, message):
        pass

    async def dummy_get_stored_messages(username):
        return []

    monkeypatch.setattr("async_server.store_message", dummy_store_message)
    monkeypatch.setattr("async_server.get_stored_messages", dummy_get_stored_messages)

    server_task = asyncio.create_task(server_main())
    await asyncio.sleep(0.1)

    # --- Client 1 (Alice) connects ---
    reader1, writer1 = await asyncio.open_connection('127.0.0.1', 5000)
    data = await reader1.read(1024)
    assert "Enter your username:" in data.decode()
    writer1.write(b"alice\n")
    await writer1.drain()
    data = await reader1.read(1024)
    assert "Connected! Users online:" in data.decode()

    # --- Client 2 (Bob) connects ---
    reader2, writer2 = await asyncio.open_connection('127.0.0.1', 5000)
    data = await reader2.read(1024)
    assert "Enter your username:" in data.decode()
    writer2.write(b"bob\n")
    await writer2.drain()
    data = await reader2.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer1.write(b"bob: Hello Bob!\n")
    await writer1.drain()

    data = await reader2.read(1024)
    decoded = data.decode()
    assert "alice" in decoded and "Hello Bob!" in decoded

    writer1.write(b"exit")
    await writer1.drain()
    writer1.close()
    await writer1.wait_closed()

    writer2.write(b"exit")
    await writer2.drain()
    writer2.close()
    await writer2.wait_closed()

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass
