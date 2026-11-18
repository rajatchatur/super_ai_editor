from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.services.earshot_service import analyze_audio_track, compute_auto_ducking
from backend.app.config import UPLOAD_DIR, SFX_DIR

router = APIRouter(prefix="/api/earshot", tags=["Earshot Audio Analysis"])

class AnalyzeRequest(BaseModel):
    filename: str

class DuckingRequest(BaseModel):
    speech_intervals: List[Dict[str, float]]
    total_duration: float
    duck_level: Optional[float] = 0.2

@router.post("/analyze")
def analyze_audio(req: AnalyzeRequest):
    """Analyze audio track for waveform, beat markers, tempo BPM, and silence intervals."""
    filepath = UPLOAD_DIR / req.filename
    if not filepath.exists():
        filepath = SFX_DIR / req.filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"File {req.filename} not found.")

    res = analyze_audio_track(filepath)
    return res

@router.post("/ducking")
def compute_ducking(req: DuckingRequest):
    """Compute volume keyframes for background music to auto-duck around speech intervals."""
    keyframes = compute_auto_ducking(req.speech_intervals, req.total_duration, req.duck_level)
    return {"keyframes": keyframes}
