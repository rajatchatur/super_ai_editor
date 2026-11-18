import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
EXPORT_DIR = BASE_DIR / "exports"
SFX_DIR = BASE_DIR / "sfx_library"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SFX_DIR.mkdir(parents=True, exist_ok=True)

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Hardware & Model recommendations
# 8GB macOS Profile -> lightweight fast models
RECOMMENDED_MODEL_MAC_8GB = "llama3.2:1b"
# 16GB Windows Profile -> high capability models
RECOMMENDED_MODEL_WIN_16GB = "llama3.2:3b"

# App settings
APP_NAME = "super_ai_editor"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
