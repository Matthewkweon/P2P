from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, UTC
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import os
import argparse
from dotenv import load_dotenv
load_dotenv()

# Pydantic message model
class Message(BaseModel):
    sender: str
    destination: str
    message: str
    timestamp: str = datetime.now(UTC).isoformat()
    type: str = "chat"  # can be "chat", "command", "notification", or "subscription"
    metadata: dict = {}  # optional metadata for special message types

def create_app(mongo_url=None):
    """Create and configure the FastAPI application."""
    app = FastAPI(title="P2P Chat Message API")
    
    # Connect to MongoDB
    mongo_url = mongo_url or os.getenv("MONGO_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(mongo_url)
    db = client["messaging_db"]
    collection = db["messages"]
    
    @app.post("/messages/")
    async def store_message(msg: Message):
        await collection.insert_one(msg.dict())
        return {"status": "stored"}
    
    @app.get("/messages/{username}")
    async def get_messages(username: str):
        cursor = collection.find({"destination": username})
        raw_messages = await cursor.to_list(length=None)
        
        # Convert ObjectId to string
        messages = []
        for msg in raw_messages:
            msg["_id"] = str(msg["_id"])  # make ObjectId serializable
            messages.append(msg)
    
        await collection.delete_many({"destination": username})
        return {"messages": messages}
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}
    
    return app

def main(host="127.0.0.1", port=8000, mongo_url=None):
    """Run the API server."""
    app = create_app(mongo_url)
    uvicorn.run(app, host=host, port=port)

def main_entry():
    """Entry point for console script."""
    parser = argparse.ArgumentParser(description='P2P Chat Message API')
    parser.add_argument('--host', default="127.0.0.1", help='API host')
    parser.add_argument('--port', type=int, default=8000, help='API port')
    parser.add_argument('--mongo-url', help='MongoDB connection URL')
    args = parser.parse_args()
    
    main(args.host, args.port, args.mongo_url)

if __name__ == "__main__":
    main_entry()