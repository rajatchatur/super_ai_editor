from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from backend.app.services.hyperframes_service import extract_thumbnail_strip, apply_frame_interpolation, apply_speed_ramp
from backend.app.config import UPLOAD_DIR, EXPORT_DIR

router = APIRouter(prefix="/api/hyperframes", tags=["HyperFrames Video Processing"])

THUMBNAIL_DIR = EXPORT_DIR / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

class ThumbnailsRequest(BaseModel):
    filename: str
    count: Optional[int] = 12

class InterpolateRequest(BaseModel):
    filename: str
    target_fps: Optional[int] = 60
    mode: Optional[str] = "mci"

class SpeedRampRequest(BaseModel):
    filename: str
    speed_factor: float

@router.post("/thumbnails")
def get_thumbnails(req: ThumbnailsRequest):
    filepath = UPLOAD_DIR / req.filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    thumbs = extract_thumbnail_strip(filepath, THUMBNAIL_DIR, req.count)
    return {"thumbnails": thumbs}

@router.get("/thumbnails/{filename}")
def serve_thumbnail(filename: str):
    path = THUMBNAIL_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")
    return FileResponse(path, media_type="image/jpeg")

@router.post("/interpolate")
def interpolate_frames(req: InterpolateRequest):
    filepath = UPLOAD_DIR / req.filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    out_name = f"interpolated_{req.filename}"
    out_path = EXPORT_DIR / out_name
    res = apply_frame_interpolation(filepath, out_path, req.target_fps, req.mode)
    return res

@router.post("/speed_ramp")
def speed_ramp(req: SpeedRampRequest):
    filepath = UPLOAD_DIR / req.filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    out_name = f"speed_{req.speed_factor}x_{req.filename}"
    out_path = EXPORT_DIR / out_name
    res = apply_speed_ramp(filepath, out_path, req.speed_factor)
    return res
