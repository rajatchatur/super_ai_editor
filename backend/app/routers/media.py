import shutil
import subprocess
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from backend.app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/media", tags=["Media Bin & Storage"])

@router.post("/upload")
async def upload_media_file(file: UploadFile = File(...)):
    """Upload media file, extract metadata using ffprobe, and store in uploads directory."""
    filename = file.filename
    clean_name = filename.replace(" ", "_")
    dest_path = UPLOAD_DIR / clean_name
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Probe duration and dimensions
    duration = 5.0
    width = 1920
    height = 1080
    fps = 30.0
    has_audio = False
    
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(dest_path)
        ]
        out = subprocess.check_output(cmd)
        import json
        info = json.loads(out)
        duration = float(info.get("format", {}).get("duration", 5.0))
        
        for st in info.get("streams", []):
            if st.get("codec_type") == "video":
                width = int(st.get("width", 1920))
                height = int(st.get("height", 1080))
                r_fps = st.get("r_frame_rate", "30/1")
                if "/" in r_fps:
                    n, d = r_fps.split("/")
                    fps = round(float(n) / float(d), 2)
            elif st.get("codec_type") == "audio":
                has_audio = True
    except Exception:
        pass
        
    return {
        "filename": clean_name,
        "url": f"/api/media/file/{clean_name}",
        "duration": round(duration, 2),
        "width": width,
        "height": height,
        "fps": fps,
        "has_audio": has_audio
    }

@router.get("/file/{filename}")
def serve_media_file(filename: str):
    """Serve uploaded file."""
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Media file not found.")
    ext = path.suffix.lower()
    media_type = "video/mp4" if ext in [".mp4", ".mov", ".mkv"] else ("audio/wav" if ext == ".wav" else "application/octet-stream")
    return FileResponse(path, media_type=media_type)

@router.get("/demo_project")
def get_demo_project():
    """Return pre-configured sample project with Three.js overlays, Whisper captions, Motion skills, and RealSFX."""
    return {
        "title": "Cyberpunk AI Reel",
        "duration": 6.0,
        "resolution": {"width": 1920, "height": 1080},
        "fps": 30,
        "tracks": {
            "video": [
                {
                    "id": "v1",
                    "title": "Cinematic Studio Base",
                    "start": 0.0,
                    "duration": 6.0,
                    "color": "#3b82f6"
                }
            ],
            "three_js": [
                {
                    "id": "th1",
                    "title": "3D Title: SUPER AI",
                    "type": "text",
                    "text": "SUPER AI",
                    "start": 0.0,
                    "duration": 3.0,
                    "color": "#06b6d4",
                    "animation": "spin_float"
                },
                {
                    "id": "th2",
                    "title": "3D Particle Vortex",
                    "type": "particles",
                    "start": 2.5,
                    "duration": 3.5,
                    "color": "#a855f7",
                    "animation": "vortex"
                }
            ],
            "motion_skills": [
                {
                    "id": "m1",
                    "title": "Kinetic Bounce Pop",
                    "preset": "bounce",
                    "start": 0.2,
                    "duration": 1.5,
                    "color": "#ec4899"
                },
                {
                    "id": "m2",
                    "title": "Cinematic Ken Burns",
                    "preset": "kenburns",
                    "start": 1.8,
                    "duration": 4.2,
                    "color": "#f97316"
                }
            ],
            "subtitles": [
                {
                    "id": 1,
                    "start": 0.5,
                    "end": 2.8,
                    "text": "EXPERIENCE THE NEXT ERA OF AI VIDEO EDITING",
                    "style": "hormozi"
                },
                {
                    "id": 2,
                    "start": 3.2,
                    "end": 5.6,
                    "text": "POWERED BY THREE.JS, HYPERFRAMES, AND WHISPER",
                    "style": "hormozi"
                }
            ],
            "sfx": [
                {
                    "id": "s1",
                    "sfx_type": "whoosh",
                    "title": "Opening Whoosh",
                    "time": 0.1,
                    "duration": 0.8,
                    "volume": 0.9
                },
                {
                    "id": "s2",
                    "sfx_type": "boom",
                    "title": "Title Impact Boom",
                    "time": 0.8,
                    "duration": 2.0,
                    "volume": 1.0
                },
                {
                    "id": "s3",
                    "sfx_type": "riser",
                    "title": "Climax Riser",
                    "time": 3.0,
                    "duration": 2.5,
                    "volume": 0.85
                }
            ]
        }
    }
