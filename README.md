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
4. **Web Interface (`websocket_adapter.py` + `static/index.html`)**: Web-based chat interface
5. **Thermometer Service (`thermometer.py`)**: Simulated IoT device that broadcasts temperature readings
6. **OpenAI Bot (`openai.py`)**: AI assistant powered by OpenAI's API

## Requirements

- Python 3.12.4
- asyncio library (built into Python standard library)
- pytest and pytest-asyncio (for running tests)
- MongoDB Community Edition 7.0
- OpenAI API key (optional, for the AI bot only)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/matthewkweon/P2P
   cd P2P
   ```

2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with:
   ```
   MONGO_URL=mongodb://localhost:27017
   OPENAI_API_KEY=your_openai_api_key_here  # Optional, for OpenAI bot
   ```

## Usage

### Using the Launcher Script (Recommended)

The easiest way to run the application is using the launcher script, which starts all components in the correct order:

```bash
python launcher.py
```

This will start:
- MongoDB connection
- Message API
- Chat server
- Web interface (accessible at http://localhost:8080)
- Thermometer service
- OpenAI bot (if API key is configured)

All output is directed to log files in the "logs" directory.

Options:
```bash
python launcher.py --no-web           # Don't start the web interface
python launcher.py --no-thermometer   # Don't start the thermometer service
python launcher.py --no-openai        # Don't start the OpenAI bot
```

### Starting Components Manually

If you prefer to start components individually:

1. First ensure MongoDB is running

2. Run the Message API server:
   ```bash
   python /src/p2p_chat/message_api.py
   ```

3. Run the chat server:
   ```bash
   python /src/p2p_chat/server.py
   ```
   The server will start on localhost (127.0.0.1) port 5000.

4. For web interface (optional):
   ```bash
   python /src/p2p_chat/websocket_adapter.py
   ```
   Then access http://localhost:8080 in your browser

5. For thermometer service (optional):
   ```bash
   python src/p2p_chat/services/thermometer.py
   ```

6. For OpenAI bot (optional):
   ```bash
   python src/p2p_chat/openai.py
   ```

### Connecting with a Client

#### Command Line Client

Run as many clients to connect to the server. I used multiple different terminals with differnet usernames so that I can simulate communication between users. To connect, I simply ran this command in terminal to start each client:

```bash
python /src/p2p_chat/client.py
```

When prompted, enter a username to identify yourself in the chat.

#### Web Interface

For a more user-friendly experience, access the web interface at http://localhost:8080/ after starting the websocket adapter. The web interface offers:

1. **Login Screen**:
   - Enter your username
   - Optional: Configure server connection settings (host and port)
   - Click "Join Chat" to connect

2. **Chat Interface**:
   - Modern UI with message history and online users list
   - Different message types are color-coded:
     - Regular messages (light blue)
     - Your outgoing messages (light green) 
     - System messages/stored messages (gray)
     - Bot messages 

3. **Sending Messages**:
   - Enter recipient username in the "To:" field
   - Type your message in the input box
   - Click "Send" or press Enter

4. **Command Buttons**:
   - "Check Stored Messages" - Retrieves any stored messages for you (including subscription messages)
   - "Subscribe to Thermometer" - Subscribe to temperature updates
   - "Unsubscribe" - Stop receiving temperature updates
   - "Chat with OpenAI" - Allows you to chat to send a message to our AI bot. 

5. **OpenAI Bot Commands**:
   - `openai: help` - Get a list of available commands
   - `openai: personality happy` - Change to happy personality
   - `openai: personality angry` - Change to angry personality
   - `openai: personality spanish` - Switch to Spanish mode
   - `openai: rotate` - Rotate to the next personality

6. **Thermometer Subscription Commands**:
   - `thermometer1: subscribe` - Subscribe to the thermometer and get the temperature periodically (100 seconds) inside of your stored messages
   - `thermometer1: unsubscribe` - Don't receive any messages anymore
   - `thermometer1: reboot` - Reboot the subscription
   - `thermometer1: range` - Get range of values of temperature in stored messages

7. **Logout**:
   - Click "Logout" in the top right to disconnect

### Messaging Protocol in the terminal (if you run it not on the web interface and only through pure socket communication)

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
- press "logout" on the web interface

## Message protocol in the terminal

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

## Using the OpenAI Bot in the terminal

The project includes an OpenAI-powered chatbot that can respond to users with different personalities. To interact with the OpenAI bot:

1. Make sure you have an OpenAI API key set in your `.env` file
2. Start the bot with `python openai.py` or use the launcher script
3. In any client, send a direct message to the "openai" user:
   ```
   openai: Hello, how are you?
   ```

Special commands for the bot:
- `openai: help` - Get a list of available commands
- `openai: personality happy` - Change to happy personality
- `openai: personality angry` - Change to angry personality
- `openai: personality spanish` - Switch to Spanish mode
- `openai: rotate` - Rotate to the next personality

In the web interface, you can also click the "Chat with OpenAI" button and use the command buttons that appear.

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

### Web Interface

The web interface provides a browser-based way to access the chat:

- Clean, modern UI with message history
- Online users list displayed in the header
- Color-coded message types for better visualization
- Command buttons for common actions
- Support for private messaging with "To:" field
- Responsive design that works on mobile and desktop

The web interface communicates with the server via a WebSocket adapter (websocket_adapter.py) which:
- Translates between WebSocket and TCP protocols
- Manages client connections and message routing
- Parses and formats messages for the web client
- Provides real-time updates on user status

## Project Structure

```
P2P/
├── .env                   # Environment variables (mongodb and openai key)
├── .gitignore             # Git ignore file
├── README.md              # This file
├── install.sh             # Installation script for Unix systems
├── launcher.py            # Script to launch all components
├── pyproject.toml         # Python package configuration
├── requirements.txt       # Project dependencies
├── setup.py               # Package setup script
├── static/                # Web interface files
│   └── index.html         # Web client implementation
├── src/                   # Source directory for installed package
│   ├── p2p_chat/          # Package module
│   │   ├── __init__.py    # Package initialization
│   │   ├── client.py      # Client module
│   │   ├── message_api.py # API module
│   │   ├── openai.py      # OpenAI bot module
│   │   ├── server.py      # Server module
│   │   ├── websocket_adapter.py # Web adapter module
│   │   └── services/      # Services submodule
│   │       ├── __init__.py # Services initialization
│   │       └── thermometer.py # Thermometer service module
│   └── tests/             # Test directory
│       └── test_chat_app.py # Test suite
```
Ignore the dummy_server_client (it is for the first part of testing the client/server without asyncio)

## Known Limitations

- No encryption for message content
- No authentication beyond username selection
- No persistence (messages are lost if the server restarts)
- No group messaging functionality