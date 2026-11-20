import shutil
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from backend.app.config import UPLOAD_DIR
from backend.app.media_utils import (
    build_media_response,
    guess_media_type,
    sanitize_filename,
)

router = APIRouter(prefix="/api/media", tags=["Media Bin & Storage"])


@router.post("/upload")
async def upload_media_file(file: UploadFile = File(...)):
    """Upload video, audio or image, extract metadata and store it in the uploads directory."""
    clean_name = sanitize_filename(file.filename)
    dest_path = UPLOAD_DIR / clean_name

    # Never overwrite previously uploaded media.
    if dest_path.exists():
        dest_path = UPLOAD_DIR / f"{dest_path.stem}_{int(time.time() * 1000)}{dest_path.suffix}"
        clean_name = dest_path.name

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if dest_path.stat().st_size == 0:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return build_media_response(clean_name, dest_path, file.content_type)


@router.get("/file/{filename}")
def serve_media_file(filename: str):
    """Serve uploaded video, audio or image with the correct MIME type."""
    path = UPLOAD_DIR / sanitize_filename(filename)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Media file not found.")
    return FileResponse(path, media_type=guess_media_type(path))


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
