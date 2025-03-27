from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timezone, UTC
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
import uvicorn
import os
from dotenv import load_dotenv
load_dotenv()
from bson import ObjectId

app = FastAPI()

# Connect to MongoDB using MONGO_URL from .env
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client["messaging_db"]
collection = db["messages"]


# Pydantic message model
class Message(BaseModel):
    sender: str
    destination: str
    message: str
    timestamp: str = datetime.now(UTC).isoformat()
    type: str = "chat"  # can be "chat", "command", "notification", or "subscription"
    metadata: dict = {}  # optional metadata for special message types


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


if __name__ == "__main__":
    uvicorn.run("message_api:app", host="127.0.0.1", port=8000, reload=True)
