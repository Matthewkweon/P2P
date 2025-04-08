# test_chat_app.py
import asyncio
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

# ----------------------
# Event Loop Fixture
# ----------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ----------------------
# Fake Database for message_api
# ----------------------
import src.p2p_chat.message_api as message_api

class FakeCollection:
    def __init__(self):
        self.data = []

    async def insert_one(self, document):
        self.data.append(document)
        class FakeInsertOneResult:
            inserted_id = "fake_id"
        return FakeInsertOneResult()

    def find(self, query):
        dest = query.get("destination")
        return FakeCursor([doc for doc in self.data if doc.get("destination") == dest])

    async def delete_many(self, query):
        if query:
            dest = query.get("destination")
            if dest is None:
                self.data = []
            else:
                self.data = [doc for doc in self.data if doc.get("destination") != dest]
        else:
            self.data = []
        return None

class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length=None):
        return self.docs

@pytest.fixture(autouse=True)
async def fake_db(monkeypatch):
    fake_collection = FakeCollection()
    monkeypatch.setattr(message_api, "collection", fake_collection)
    yield fake_collection


# ----------------------
# FastAPI Endpoint Tests
# ----------------------
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
    transport = ASGITransport(app=message_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/messages/", json=test_message)
        assert response.status_code == 200
        assert response.json() == {"status": "stored"}

@pytest.mark.asyncio
async def test_get_messages():
    test_message = {
        "sender": "alice",
        "destination": "bob",
        "message": "Hello Bob!",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "chat",
        "metadata": {}
    }
    transport = ASGITransport(app=message_api.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post_resp = await client.post("/messages/", json=test_message)
        assert post_resp.status_code == 200

        get_resp = await client.get("/messages/bob")
        data = get_resp.json()
        assert "messages" in data
        # Expect one stored message.
        assert len(data["messages"]) == 1
        retrieved_msg = data["messages"][0]
        assert retrieved_msg["sender"] == "alice"
        assert "Hello Bob!" in retrieved_msg["message"]

        # Subsequent retrieval should return an empty list.
        get_resp2 = await client.get("/messages/bob")
        data2 = get_resp2.json()
        assert data2["messages"] == []


# ----------------------
# Async Server Tests
# ----------------------
import src.p2p_chat.server as server

# Fixture to reset global state.
@pytest.fixture
def reset_server_state():
    server.clients.clear()
    yield
    server.clients.clear()


# Updated run_server fixture that yields a tuple (server, server_task).
@pytest.fixture
async def run_server():
    server = await asyncio.start_server(
        server.handle_client, server.HOST, server.PORT
    )
    server_task = asyncio.create_task(server.serve_forever())
    yield (server, server_task)
    # Teardown: close the server and cancel the serve_forever task.
    server.close()
    await server.wait_closed()
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


# Override the storage functions so the server does not perform real HTTP calls.
@pytest.fixture
def fake_storage(monkeypatch):
    storage = {}

    async def fake_store_message(sender, destination, message):
        storage.setdefault(destination, []).append(message)

    async def fake_get_stored_messages(username):
        msgs = storage.get(username, [])
        storage[username] = []
        return [f"[CHAT][dummy-timestamp][{username}] {msg}" for msg in msgs]

    monkeypatch.setattr(server, "store_message", fake_store_message)
    monkeypatch.setattr(server, "get_stored_messages", fake_get_stored_messages)
    return storage


@pytest.mark.asyncio
async def test_chat_server_offline_message(run_server, fake_storage, reset_server_state):
    # Get the (server, task) tuple directly from the fixture.
    server, _ = run_server

    # --- Client 1 (Alice) connects and sends a message to offline Bob ---
    reader1, writer1 = await asyncio.open_connection(server.HOST, server.PORT)
    data = await reader1.read(1024)
    assert "Enter your username:" in data.decode()

    writer1.write(b"alice\n")
    await writer1.drain()
    data = await reader1.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer1.write(b"bob: Hello Bob!\n")
    await writer1.drain()
    # Give the server a brief moment to process and send a response.
    await asyncio.sleep(0.1)
    data = await reader1.read(1024)
    output = data.decode()
    assert "User 'bob' is offline" in output

    writer1.write(b"exit")
    await writer1.drain()
    writer1.close()
    await writer1.wait_closed()

    # --- Client 2 (Bob) connects and checks for stored messages ---
    reader2, writer2 = await asyncio.open_connection(server.HOST, server.PORT)
    data = await reader2.read(1024)
    assert "Enter your username:" in data.decode()

    writer2.write(b"bob\n")
    await writer2.drain()
    data = await reader2.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer2.write(b"!check\n")
    await writer2.drain()
    await asyncio.sleep(0.1)
    data = await reader2.read(1024)
    decoded = data.decode()
    assert "Hello Bob!" in decoded

    writer2.write(b"exit")
    await writer2.drain()
    writer2.close()
    await writer2.wait_closed()


@pytest.mark.asyncio
async def test_chat_server_online_message(run_server, monkeypatch, reset_server_state):
    async def dummy_store_message(sender, destination, message):
        pass

    async def dummy_get_stored_messages(username):
        return []

    monkeypatch.setattr(server, "store_message", dummy_store_message)
    monkeypatch.setattr(server, "get_stored_messages", dummy_get_stored_messages)

    # Get the (server, task) tuple directly from the fixture.
    server, _ = run_server

    # --- Client 1 (Alice) connects ---
    reader1, writer1 = await asyncio.open_connection(server.HOST, server.PORT)
    data = await reader1.read(1024)
    assert "Enter your username:" in data.decode()
    writer1.write(b"alice\n")
    await writer1.drain()
    data = await reader1.read(1024)
    assert "Connected! Users online:" in data.decode()

    # --- Client 2 (Bob) connects ---
    reader2, writer2 = await asyncio.open_connection(server.HOST, server.PORT)
    data = await reader2.read(1024)
    assert "Enter your username:" in data.decode()
    writer2.write(b"bob\n")
    await writer2.drain()
    data = await reader2.read(1024)
    assert "Connected! Users online:" in data.decode()

    writer1.write(b"bob: Hello Bob!\n")
    await writer1.drain()
    await asyncio.sleep(0.1)
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
