from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import uvicorn

app = FastAPI()
pending_messages: Dict[str, List[str]] = {}

class Message(BaseModel):
    username: str
    message: str

@app.post("/messages/")
def store_message(msg: Message):
    if msg.username not in pending_messages:
        pending_messages[msg.username] = []
    pending_messages[msg.username].append(msg.message)
    return {"status": "stored"}

@app.get("/messages/{username}")
def get_messages(username: str):
    messages = pending_messages.pop(username, [])
    return {"messages": messages}

if __name__ == "__main__":
    uvicorn.run("message_api:app", host="127.0.0.1", port=8000, reload=True)
