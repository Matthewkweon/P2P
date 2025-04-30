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

## Technologies Used

This project leverages a modern tech stack to deliver a flexible and scalable chat system:

- **Python**: Core programming language with asyncio for asynchronous operations
- **FastAPI**: High-performance API framework for the message storage service
- **MongoDB**: NoSQL database for storing messages and user data
- **WebSockets**: For real-time web interface communication
- **Docker**: Containerization for easy deployment and development
- **HTML/CSS/JavaScript**: Frontend web interface with responsive design
- **OpenAI API**: Integration for AI-powered chat bot functionality
- **pytest**: Comprehensive testing framework

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
   MONGO_URL=mongodb://p2p-mongo:27017
   OPENAI_API_KEY=your_openai_api_key_here  # Optional, for OpenAI bot
   DEFAULT_API_BASE=http://api:8000
   CHAT_SERVER_HOST=p2p-server
   CHAT_SERVER_PORT=5000
   ```

## Running with Docker (Recommended)

The easiest way to run the application is using Docker and Docker Compose:

### Prerequisites for Docker

- Docker
- Docker Compose

### Starting with Docker

1. Build and start the services:
   ```bash
   docker-compose up --build
   ```

   This will:
   - Start a MongoDB container
   - Start the Message API on port 8001
   - Start the Chat server on port 5001
   - Start the Web interface on port 8080
   - Start the Thermometer service
   - Start the OpenAI bot (if API key is configured)

2. Access the web interface:
   Open your browser and navigate to [http://localhost:8080](http://localhost:8080)

3. Stopping the application:
   ```bash
   # Stop the containers but keep the data
   docker-compose down
   
   # Stop the containers and delete all data
   docker-compose down -v
   ```

### Docker Troubleshooting

If you encounter port conflicts, edit the `docker-compose.yml` file to change the exposed ports:
```yaml
ports:
  - "5002:5000"  # Change 5001 to another port
  - "8002:8000"  # Change 8001 to another port
  - "8081:8080"  # Change 8080 to another port
```

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
      - This includes any messages that were sent to you while the user was offline (uses fastapi to store messages and mongoDB to store them)
   - "Subscribe to Thermometer" - Subscribe to temperature updates
   - "Unsubscribe" - Stop receiving temperature updates
   - "Chat with OpenAI" - Allows you to chat to send a message to our AI bot. 

5. **OpenAI Bot Commands**:
   - Simply sending a message to "openai" will allow you to talk to an AI bot that I have configured. The initial personality is happy. You can change it with the following commands:
   - `openai: personality happy` - Change to happy personality
   - `openai: personality angry` - Change to angry personality
   - `openai: personality spanish` - Switch to Spanish mode

6. **Thermometer Subscription Commands**:
   - A thermometer subscription involves just a message every 100 seconds about the temperature outside. Use the following commands. You can see the messages in your stored messages. Click "Stored messages"
   - `thermometer1: subscribe` - Subscribe to the thermometer and get the temperature periodically (100 seconds) inside of your stored messages
   - `thermometer1: unsubscribe` - Don't receive any messages anymore
   - `thermometer1: reboot` - Reboot the subscription
   - `thermometer1: range` - Get range of values of temperature in stored messages

7. **Logout**:
   - Click "Logout" in the top right to disconnect

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
├── Dockerfile             # Docker container configuration
├── docker-compose.yml     # Docker Compose configuration
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

## Known Limitations

- No encryption for message content
- No authentication beyond username selection
- No persistence (messages are lost if the server restarts)
- No group messaging functionality