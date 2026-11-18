from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from backend.app.services.realsfx_service import list_sfx_library, generate_custom_sfx
from backend.app.config import SFX_DIR

router = APIRouter(prefix="/api/realsfx", tags=["RealSFX Foley & Audio Synthesis"])

class SFXGenerateRequest(BaseModel):
    prompt: str
    duration: Optional[float] = 1.0

@router.get("/library")
def get_library():
    """List pre-rendered and available sound effects in RealSFX."""
    return list_sfx_library()

@router.post("/generate")
def generate_sfx(req: SFXGenerateRequest):
    """Generate or retrieve procedural sound effects based on text prompt."""
    res = generate_custom_sfx(req.prompt, req.duration)
    return res

@router.get("/audio/{filename}")
def get_sfx_audio(filename: str):
    """Serve sound effect WAV audio file."""
    path = SFX_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="SFX audio file not found.")
    return FileResponse(path, media_type="audio/wav")
