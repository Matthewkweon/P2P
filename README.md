# P2P

A simple asynchronous chat application built with Python's asyncio library that allows users to exchange messages in real-time with offline message support.

## Features

- **Real-time messaging**: Users can chat with other connected users
- **Offline message storage**: Messages sent to offline users are stored and delivered when they connect
- **Simple client-server architecture**: Easy to understand and extend
- **Private messaging**: Direct message support between users
- **Asynchronous I/O**: Built with Python's asyncio for efficient network operations

## Components

The application consists of two main components:

1. **Server (`async_server.py`)**: Manages client connections, routes messages, and stores offline messages
2. **Client (`async_client.py`)**: Connects to the server, sends and receives messages

## Requirements

- Python 3.7+
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

## Usage

### Starting the Server

Run the server to begin accepting connections:

```bash
python async_server.py
```

The server will start on localhost (127.0.0.1) port 5000.

### Connecting with a Client

Run the client to connect to the server:

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

### Commands

- `exit`: Disconnect from the server

## Testing

The application includes automated tests using pytest and pytest-asyncio. The tests verify functionality like message routing and offline message storage.

### Running Tests

Run the tests with pytest:

```bash
pytest test_chat_app.py -v
```

### Continuous Integration

This project uses GitHub Actions for continuous integration. The workflow is defined in `.github/workflows/` and automatically runs the test suite when changes are pushed to the repository.

## How It Works

### Server

The server manages all connected clients and routes messages between them. Key features:

- Tracks online users in the `clients` dictionary
- Stores messages for offline users in the `pending_messages` dictionary
- Delivers stored messages when users connect
- Handles user connections/disconnections

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
├── .github/            
│   └── workflows/      # GitHub Actions CI configuration
└── README.md           # This file
```

## Known Limitations

- No encryption for message content
- No authentication beyond username selection
- No persistence (messages are lost if the server restarts)
- No group messaging functionality

## Future Improvements

- Add message encryption for privacy
- Implement user authentication
- Add persistent storage for messages
- Support for group chats and channels
- Add a graphical user interface
