import asyncio
import argparse
import httpx
from datetime import datetime, UTC
import os
import json
import random
from typing import Literal
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

DEFAULT_HOST = '127.0.0.1'  # Chat server host
DEFAULT_PORT = 5000  # Chat server port
DEFAULT_USERNAME = "openai"  # Bot username
DEFAULT_API_BASE = "http://127.0.0.1:8000"  # Message API base URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # OpenAI API key

# Bot personalities
PERSONALITIES = {
    "happy": {
        "prompt": "You are a very happy, cheerful assistant who responds enthusiastically to users. Always use emojis and exclamation marks! Be upbeat and positive no matter what the user says.",
        "description": "Happy, cheerful, and enthusiastic AI assistant. Responds with positive energy!"
    },
    "angry": {
        "prompt": "You are a grumpy, irritated assistant who responds with sarcasm and slight annoyance. Use ALL CAPS occasionally to emphasize your frustration. Never use emojis.",
        "description": "Grumpy, irritated AI assistant who's had enough of your questions."
    },
    "spanish": {
        "prompt": "Eres un asistente amable que responde SIEMPRE en español. No importa lo que te digan, debes responder siempre en español. Si te preguntan por qué hablas español, explica que es tu idioma preferido.",
        "description": "Spanish-speaking AI assistant. Will only respond in Spanish."
    }
}

# Default personality rotation
DEFAULT_PERSONALITY_ROTATION = ["happy", "angry", "spanish"]

class OpenAIChatbot:
    def __init__(self, username=DEFAULT_USERNAME, api_base=DEFAULT_API_BASE, 
                 model="gpt-4o", personality="happy", rotation=None):
        self.username = username
        self.api_base = api_base
        self.model = model
        self.active_personality = personality
        self.personality_rotation = rotation or DEFAULT_PERSONALITY_ROTATION
        self.rotation_index = 0
        self.subscribers = set()
        self.running = True
        self.writer = None
        self.reader = None
        self.rate_limit_time = 0.1  # Seconds to wait between API calls
        self.last_api_call = 0
        
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        print(f"[OPENAI] Initialized with personality: {self.active_personality}")
        print(f"[OPENAI] Using model: {self.model}")
        
    async def generate_response(self, user_message, personality=None):
        """Generate a response using OpenAI API based on the given personality."""
        personality = personality or self.active_personality
        
        # Basic rate limiting
        now = time.time()
        if now - self.last_api_call < self.rate_limit_time:
            await asyncio.sleep(self.rate_limit_time)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                self.last_api_call = time.time()
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OPENAI_API_KEY}"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": PERSONALITIES[personality]["prompt"]},
                            {"role": "user", "content": user_message}
                        ],
                        "max_tokens": 500
                    }
                )
                
                if response.status_code != 200:
                    print(f"[OPENAI ERROR] API returned status {response.status_code}: {response.text}")
                    return f"Sorry, I encountered an error (status {response.status_code})"
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            print(f"[OPENAI ERROR] {e}")
            return "Sorry, I couldn't generate a response right now."
    
    async def direct_send_message(self, destination, message):
        """Send a message directly to a user if they're online."""
        if not self.writer:
            print("[OPENAI ERROR] Not connected to server, can't send direct message")
            return False
            
        try:
            timestamp = datetime.now(UTC).isoformat()
            command = f"{destination}: {message}"
            self.writer.write(command.encode())
            await self.writer.drain()
            return True
        except Exception as e:
            print(f"[OPENAI ERROR] Failed to send direct message: {e}")
            return False
    
    async def store_message(self, destination, message, msg_type="chat", metadata=None):
        """Store a message in the message API."""
        metadata = metadata or {}
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"{self.api_base}/messages/", json={
                    "sender": self.username,
                    "destination": destination,
                    "message": message,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "type": msg_type,
                    "metadata": metadata
                })
                return True
        except Exception as e:
            print(f"[OPENAI ERROR] Failed to store message: {e}")
            return False
    
    def rotate_personality(self):
        """Rotate to the next personality in the rotation."""
        self.rotation_index = (self.rotation_index + 1) % len(self.personality_rotation)
        self.active_personality = self.personality_rotation[self.rotation_index]
        print(f"[OPENAI] Rotated to personality: {self.active_personality}")
        return self.active_personality
    
    async def handle_command(self, sender, command):
        """Handle various commands sent to the bot."""
        command = command.lower().strip()
        
        if command == "info" or command == "help":
            # Send bot info
            response = (
                "OpenAI Chatbot - I can respond in different personalities!\n"
                "Commands:\n"
                "- personality X: Change my personality to X (happy, angry, spanish)\n"
                "- rotate: Rotate to the next personality\n"
                "- info or help: Show this help message\n"
                f"Current personality: {self.active_personality} - {PERSONALITIES[self.active_personality]['description']}"
            )
            # Try direct send first, fall back to storage
            success = await self.direct_send_message(sender, response)
            if not success:
                await self.store_message(sender, response, "notification")
            
        elif command.startswith("personality "):
            # Change personality
            personality = command.split("personality ")[1].strip()
            if personality in PERSONALITIES:
                self.active_personality = personality
                notification = f"Personality changed to {personality} - {PERSONALITIES[personality]['description']}"
                # Try direct send first, fall back to storage
                success = await self.direct_send_message(sender, notification)
                if not success:
                    await self.store_message(sender, notification, "notification")
            else:
                error_msg = f"Unknown personality: {personality}. Available: {', '.join(PERSONALITIES.keys())}"
                # Try direct send first, fall back to storage
                success = await self.direct_send_message(sender, error_msg)
                if not success:
                    await self.store_message(sender, error_msg, "notification")
                
        elif command == "rotate":
            # Rotate personality
            new_personality = self.rotate_personality()
            notification = f"Rotated to {new_personality} - {PERSONALITIES[new_personality]['description']}"
            # Try direct send first, fall back to storage
            success = await self.direct_send_message(sender, notification)
            if not success:
                await self.store_message(sender, notification, "notification")
            
        else:
            # Normal message - generate a response
            print(f"[OPENAI] Generating response to: {command}")
            response = await self.generate_response(command)
            print(f"[OPENAI] Response generated: {response[:50]}...")
            
            # Try direct send first, fall back to storage
            success = await self.direct_send_message(sender, response)
            if not success:
                print(f"[OPENAI] Direct send failed, storing message for {sender}")
                await self.store_message(sender, response)

    async def handle_incoming(self, reader, writer):
        """Handle incoming messages from the chat server."""
        self.reader = reader
        self.writer = writer
        
        while self.running:
            try:
                data = await reader.read(1024)
                if not data:
                    break

                msg = data.decode(errors="ignore").strip()
                print(f"[OPENAI] Received message: {msg}")

                # Check if this is a HTTP/WebSocket message (browser connection)
                if msg.startswith("GET /") or "HTTP/1.1" in msg or "websocket" in msg.lower() or "Sec-WebSocket-Key:" in msg:
                    print(f"[OPENAI] Ignoring HTTP/WebSocket message")
                    continue

                # Expect format: [username][timestamp] message
                if msg.startswith("[") and "]" in msg:
                    try:
                        sender = msg.split("]")[0][1:]  # extract between first [ ]
                        
                        # Extract message content - this is complicated by the fact that
                        # there might be timestamps or other bracketed content
                        parts = msg.split("]")
                        if len(parts) >= 3:  # Has sender and timestamp
                            content = "]".join(parts[2:]).strip()
                        else:  # Just has sender
                            content = "]".join(parts[1:]).strip()
                        
                        print(f"[OPENAI] Parsed sender: {sender}, content: '{content}'")
                        
                        # Process the message
                        await self.handle_command(sender, content)
                    except Exception as e:
                        print(f"[OPENAI] Error parsing message: {e}")
                        continue

            except Exception as e:
                print(f"[OPENAI ERROR] {e}")
                break
                
        self.reader = None
        self.writer = None

    async def run(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        """Connect to the chat server and start handling messages."""
        try:
            reader, writer = await asyncio.open_connection(host, port)
            
            # Read username prompt and send username
            username_prompt = await reader.read(1024)
            print(f"[OPENAI] Received prompt: {username_prompt.decode()}")
            
            writer.write(self.username.encode() + b"\n")
            await writer.drain()
            
            print(f"[OPENAI] Connected to chat server as '{self.username}'")
            
            # Skip the welcome message
            welcome_msg = await reader.read(1024)
            print(f"[OPENAI] Received welcome: {welcome_msg.decode()}")
            
            # Send a startup message to the chat server
            startup_msg = "OpenAI Chatbot is online! Send me a direct message or use the 'help' command to learn more."
            print(f"[OPENAI] Sending startup message: {startup_msg}")
            writer.write(f"TO_ALL: {startup_msg}".encode())
            await writer.drain()
            
            # Start handling incoming messages
            await self.handle_incoming(reader, writer)
            
        except Exception as e:
            print(f"[OPENAI ERROR] Connection error: {e}")
        finally:
            print("[OPENAI] Disconnected from chat server")
            self.reader = None
            if 'writer' in locals() and writer:
                writer.close()
                await writer.wait_closed()
                self.writer = None

async def main_async(host=DEFAULT_HOST, port=DEFAULT_PORT, username=DEFAULT_USERNAME, 
                    api_base=DEFAULT_API_BASE, model="gpt-4o", personality="happy"):
    """Run the OpenAI chatbot service."""
    chatbot = OpenAIChatbot(username, api_base, model, personality)
    await chatbot.run(host, port)

def main(host=DEFAULT_HOST, port=DEFAULT_PORT, username=DEFAULT_USERNAME, 
         api_base=DEFAULT_API_BASE, model="gpt-4o", personality="happy"):
    """Main function to run the OpenAI chatbot service."""
    print(f"Starting OpenAI chatbot service as '{username}'")
    print(f"Connecting to chat server at {host}:{port}")
    print(f"Using API at {api_base}")
    print(f"Using model: {model}")
    print(f"Initial personality: {personality}")
    
    asyncio.run(main_async(host, port, username, api_base, model, personality))

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='OpenAI Chatbot Service for P2P Chat')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Server host')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Server port')
    parser.add_argument('--username', default=DEFAULT_USERNAME, help='Bot username')
    parser.add_argument('--api-base', default=DEFAULT_API_BASE, help='API base URL')
    parser.add_argument('--model', default="gpt-4o", help='OpenAI model to use')
    parser.add_argument('--personality', default="happy", 
                      choices=list(PERSONALITIES.keys()), 
                      help='Bot personality')
    args = parser.parse_args()
    
    main(args.host, args.port, args.username, args.api_base, args.model, args.personality)

if __name__ == "__main__":
    main_entry()