from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
from datetime import datetime
import uvicorn

app = FastAPI()

# New structure: username -> List of full message dicts
pending_messages: Dict[str, List[Dict[str, str]]] = {}

class Message(BaseModel):
    sender: str
    destination: str
    message: str
    timestamp: str = datetime.utcnow().isoformat()


@app.post("/messages/")
def store_message(msg: Message):
    if msg.destination not in pending_messages:
        pending_messages[msg.destination] = []
    pending_messages[msg.destination].append({
        "sender": msg.sender,
        "message": msg.message,
        "timestamp": msg.timestamp
    })
    return {"status": "stored"}

@app.get("/messages/{username}")
def get_messages(username: str):
    messages = pending_messages.pop(username, [])
    return {"messages": messages}


if __name__ == "__main__":
    uvicorn.run("message_api:app", host="127.0.0.1", port=8000, reload=True)
