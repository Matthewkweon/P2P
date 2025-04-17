# P2P

A simple asynchronous chat application built with Python's asyncio library that allows users to exchange messages in real-time with offline message support.

## Features

- **Real-time messaging**: Users can chat with other connected users
- **Offline message storage**: Messages sent to offline users are stored and delivered when they connect
- **Simple client-server architecture**: Easy to understand and extend
- **Private messaging**: Direct message support between users
- **Asynchronous I/O**: Built with Python's asyncio for efficient network operations

## Components

The application consists of three main components:

1. **Server (`async_server.py`)**: Manages client connections and routes messages.
2. **Client (`async_client.py`)**: Connects to the server, sends and receives messages
3. **Message_api (`message_api.py`)**: Connects to my fastapi and stores messages inside of my database using mongoDB


## Requirements

- Python 3.12.4
- asyncio library (built into Python standard library)
- pytest and pytest-asyncio (for running tests)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/async-chat-app.git
   cd async-chat-app
   ```

2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```

4. Install all requirements inside of requirements.txt

## Usage

### Starting the Server

First get the fastapi and mongoDB up and running.

make sure that the mongoDB (using community @7.0) and the message_api.py is running.

Run the FastAPI server to begin storing messages server side:
```bash
python message_api.py
```

Then, run the server to begin accepting connections:

```bash
python async_server.py
```

The server will start on localhost (127.0.0.1) port 5000.

### Connecting with a Client

Run as many clients to connect to the server. I used multiple different terminals with differnet usernames so that I can simulate communication between users. To connect, I simply ran this command in terminal to start each client:

```bash
python async_client.py
```

When prompted, enter a username to identify yourself in the chat.

### Messaging Protocol

To send a private message to another user, use the following format:

```
username: Your message here
```

For example, to send a message to user "alice":

```
alice: Hello Alice, how are you?
```

If you send a message to another user not currently connected to the server, it should store that message in my database and send it to the desired user when he/she connects.

For example, if you send a message to Joe using:
```
Joe: hello!!
```

It will say that
```
User 'Joe' is offline. Message saved.
```

Once Joe connects to the server, it will say that:
```
[Stored] [timestamp][sender] 'hello!'

or

[Stored] [timestamp][sender] 'your_message_here'
```

To check for any messages from subscriptions or any messages from the database run:
```
!check
```
This will give you all of the messages that you haven't seen you from the database. This occurs automatically when you log into the service, but also you can manually do it with "!check".

### Commands

- `exit`: Disconnect from the server

## Message protocol

Each message has a specific protocol:
```
class Message(BaseModel):
    sender: str
    destination: str
    message: str
    timestamp: str = datetime.utcnow().isoformat()
    type: str = "chat"  # can be "chat", "command", "notification", or "subscription"
    metadata: dict = {}  # optional metadata for special message types
```

This is a straightforward protocol and allows me to easily replicate this type of message. Allows me to track the time that the message was sent and also allows me to know who sent the message to who (sender -> receive).

I also added a type: str = "chat" to determine if I want to add a different type of message or service in my code. For example, I added a subscription type that once you subscribe to the thermometer user, you will get broadcasted messages about the weather outside. 

Simply run
```
python thermometer.py
```
to run the thermometer service

To subscribe to the thermometer, run:
```
thermomter1: subscribe
```
This will broadcast the temperature outside (random values) every 100 seconds or so.

To reboot the subscription, run:
```
thermometer1: reboot
```
This will reboot the subscription.

To see the range of values from the subscription, run:
```
thermometer1: range
```

To unsubscribe from the service thermometer, simply run:
```
thermometer1: unsubscribe
```

Each of these commands will give you a message in your "messages" after you run "!check".

We needed the sender, destination, message, and timestamp to keep a structure for when users send messages to each other.

## Testing

The application includes automated tests using pytest and pytest-asyncio. The tests verify functionality like message routing and offline message storage.

### Running Tests

Run the tests with pytest to test simple cases:

```bash
pytest test_chat_app.py -v
```

## How It Works

### Server

The server manages all connected clients and routes messages between them. Key features:

- Tracks online users in the `clients` dictionary
- Stores messages for offline users in a database using mongoDB
- Delivers stored messages when users connect using a FASTAPI call from the database. This ensures that no data is being stored client side and that it is all handled server side.
- Handles user connections/disconnections
- Allows subscription to dummy service called "thermometer.py" that periodically gives a random weather/temperature outside. Also allows the restart of service or even a list of the range of values that are used. 

### Client

The client provides a simple interface for connecting to the server and exchanging messages:

- Establishes a connection to the server
- Runs concurrent tasks for sending and receiving messages
- Formats messages according to the messaging protocol

## Project Structure

```
async-chat-app/
├── async_server.py     # Server implementation
├── async_client.py     # Client implementation
├── test_chat_app.py    # Test suite
├── message_api.py      # Handles the API calls and storing of messages in a database
├── requirements.txt    # requirements
└── README.md           # This file
```
Ignore the dummy_server_client (it is for the first part of testing the client/server without asyncio)

## Known Limitations

- No encryption for message content
- No authentication beyond username selection
- No persistence (messages are lost if the server restarts)
- No group messaging functionality

## Things to add in the future:
- Add a password for privacy and user authentication
- support group chats
- add a graphical user interface