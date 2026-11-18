from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.app.services.ollama_service import check_ollama_status, ask_ollama_copilot

router = APIRouter(prefix="/api/ollama", tags=["Ollama AI Copilot"])

class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None

@router.get("/status")
def get_ollama_status():
    """Returns Ollama connectivity, available models, and hardware recommendation."""
    return check_ollama_status()

@router.post("/chat")
def chat_with_copilot(req: ChatRequest):
    """Sends editing command to Ollama or offline fallback copilot, returns timeline actions."""
    return ask_ollama_copilot(req.prompt, req.model)
