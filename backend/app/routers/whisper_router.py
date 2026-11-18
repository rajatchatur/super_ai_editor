from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.app.services.whisper_service import transcribe_audio_file, export_srt
from backend.app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/whisper", tags=["Whisper Subtitles"])

class TranscribeRequest(BaseModel):
    filename: str
    model_size: Optional[str] = "base"
    language: Optional[str] = "en"

class ExportSrtRequest(BaseModel):
    segments: List[Dict[str, Any]]

@router.post("/transcribe")
def transcribe_media(req: TranscribeRequest):
    filepath = UPLOAD_DIR / req.filename
    if not filepath.exists():
        # Check if it is in sfx_library
        from backend.app.config import SFX_DIR
        alt_path = SFX_DIR / req.filename
        if alt_path.exists():
            filepath = alt_path
        else:
            raise HTTPException(status_code=404, detail=f"File {req.filename} not found.")

    res = transcribe_audio_file(filepath, model_size=req.model_size, language=req.language)
    return res

@router.post("/export_srt")
def export_subtitles_srt(req: ExportSrtRequest):
    srt_text = export_srt(req.segments)
    return {"srt": srt_text}
