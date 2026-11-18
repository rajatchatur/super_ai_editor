import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import APP_NAME, APP_VERSION, EXPORT_DIR, UPLOAD_DIR, SFX_DIR, BASE_DIR
from backend.app.routers import (
    health,
    media,
    whisper_router,
    realsfx_router,
    earshot_router,
    hyperframes_router,
    ollama_router,
    render_router,
)
from backend.app.services.realsfx_service import ensure_default_sfx_library

# Pre-generate built-in SFX files
ensure_default_sfx_library()

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Super AI Editor - High Performance AI Video Editing Engine",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(media.router)
app.include_router(whisper_router.router)
app.include_router(realsfx_router.router)
app.include_router(earshot_router.router)
app.include_router(hyperframes_router.router)
app.include_router(ollama_router.router)
app.include_router(render_router.router)

# Mount static asset folders
app.mount("/static/exports", StaticFiles(directory=str(EXPORT_DIR)), name="exports")
app.mount("/static/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static/sfx", StaticFiles(directory=str(SFX_DIR)), name="sfx")

# Serve built frontend if dist exists
DIST_DIR = BASE_DIR.parent / "frontend" / "dist"
if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    @app.get("/app.js")
    def serve_app_js():
        js_file = DIST_DIR / "app.js"
        if js_file.exists():
            return FileResponse(js_file, media_type="application/javascript")
        return {"error": "app.js not found"}

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        requested_file = DIST_DIR / full_path
        if requested_file.exists() and requested_file.is_file():
            ext = requested_file.suffix.lower()
            media_type = "application/javascript" if ext == ".js" else ("text/css" if ext == ".css" else "text/html")
            return FileResponse(requested_file, media_type=media_type)
        return FileResponse(DIST_DIR / "index.html")
