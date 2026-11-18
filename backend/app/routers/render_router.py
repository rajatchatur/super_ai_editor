from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.app.services.render_service import render_timeline_project
from backend.app.config import EXPORT_DIR

router = APIRouter(prefix="/api/render", tags=["Render & Video Export Engine"])

class RenderRequest(BaseModel):
    duration: Optional[float] = 5.0
    video_clips: Optional[List[Dict[str, Any]]] = []
    audio_tracks: Optional[List[Dict[str, Any]]] = []
    sfx_tracks: Optional[List[Dict[str, Any]]] = []
    subtitles: Optional[List[Dict[str, Any]]] = []
    subtitle_style: Optional[str] = "hormozi"

@router.post("/export")
def export_video(req: RenderRequest):
    """Render full video project to MP4 using FFmpeg."""
    res = render_timeline_project(req.model_dump())
    if not res.get("success"):
        raise HTTPException(status_code=500, detail=res.get("error", "Render failed."))
    return res

@router.get("/download/{filename}")
def download_rendered_video(filename: str):
    """Download exported MP4 video file."""
    path = EXPORT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rendered file not found.")
    return FileResponse(path, media_type="video/mp4", filename=filename)
