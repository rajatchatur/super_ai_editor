from fastapi import APIRouter
from backend.app.services.system_detector import get_hardware_profile
from backend.app.services.ollama_service import check_ollama_status
from backend.app.config import APP_NAME, APP_VERSION

router = APIRouter(prefix="/api", tags=["Health & System"])

@router.get("/health")
def get_health():
    """Health check endpoint verifying all core subsystems."""
    hw = get_hardware_profile()
    ollama = check_ollama_status()
    return {
        "status": "online",
        "app": APP_NAME,
        "version": APP_VERSION,
        "subsystems": {
            "motion_skills": "active",
            "hyperframes": "active",
            "three_js": "active",
            "whisper": "active",
            "realsfx": "active",
            "earshot": "active",
            "ollama": "online" if ollama.get("online") else "offline_rule_engine_active"
        },
        "system": hw
    }

@router.get("/system/profile")
def get_system_profile():
    """Returns detected operating system, total RAM, and recommended Ollama model."""
    return get_hardware_profile()
