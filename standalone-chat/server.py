import os
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI

from src.tools.chat_store import ChatStore, Coordinator


load_dotenv()

app = FastAPI(title="Standalone Chat Coordinator API")

# CORS for local Next.js dev
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = ChatStore()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
coordinator = Coordinator(store, client)


class StartRequest(BaseModel):
    user_request: str
    conversation_title: str | None = None


class ContinueRequest(BaseModel):
    conversation_id: str
    user_response: str


@app.post("/coordinator/start")
def start(req: StartRequest) -> Dict[str, Any]:
    try:
        conv = store.create_conversation(title=req.conversation_title or "New conversation")
        result = coordinator.process_request(req.user_request, conv["id"])
        return {"conversation_id": conv["id"], **result}
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coordinator/continue")
def continue_(req: ContinueRequest) -> Dict[str, Any]:
    try:
        result = coordinator.continue_after_user_input(req.conversation_id, req.user_response)
        return {"conversation_id": req.conversation_id, **result}
    except Exception as e:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(e))


