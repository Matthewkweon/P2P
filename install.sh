#!/bin/bash
# install.sh - Quick installation script for P2P Chat

# Check if Python 3.8+ is installed
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0")
min_version="3.8"

# Function to compare version numbers
version_lt() {
    [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ] && [ "$1" != "$2" ]
}

if version_lt "$python_version" "$min_version"; then
    echo "Error: Python $min_version or higher is required (found $python_version)"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment (source doesn't work in scripts)
. ./venv/bin/activate 2>/dev/null || \
  . ./venv/Scripts/activate 2>/dev/null || \
  echo "Warning: Could not activate virtual environment automatically. Please activate it manually."

# Ensure pip is up to date
echo "Updating pip..."
pip install --upgrade pip

# Install the package in development mode
echo "Installing P2P Chat package..."
pip install -e .

# Check for MongoDB
echo "Checking for MongoDB..."
if ! command -v mongod &> /dev/null; then
    echo "Warning: MongoDB does not appear to be installed."
    echo "Please install MongoDB Community Server 7.0 from https://www.mongodb.com/try/download/community"
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
MONGO_URL=mongodb://localhost:27017
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "Please edit the .env file to add your actual OpenAI API key if you want to use the OpenAI bot"
fi

echo "Installation complete!"
echo "To start the application, you need to:"
echo "1. Start MongoDB"
echo "2. Run 'p2p-chat-api' to start the API server"
echo "3. Run 'p2p-chat-server' to start the chat server"
echo "4. Run 'p2p-chat-web' to start the web interface"
echo "5. Connect via 'p2p-chat-client' or web browser at http://localhost:8080/"