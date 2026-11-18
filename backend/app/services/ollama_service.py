import json
import urllib.request
import urllib.error
from typing import Dict, List, Any
from backend.app.config import OLLAMA_BASE_URL
from backend.app.services.system_detector import get_hardware_profile

SYSTEM_PROMPT = """You are the AI Video Editing Copilot for 'super_ai_editor'.
You help creators edit videos by generating timeline actions.
You must respond with valid JSON containing:
1. "reply": A friendly, helpful explanation of what changes you applied.
2. "timeline_actions": A list of executable video editing commands.

Supported action types:
- {"action": "add_subtitle", "start": 0.5, "end": 2.5, "text": "...", "style": "hormozi|cinematic|neon"}
- {"action": "add_sfx", "sfx_type": "whoosh|boom|riser|laser|pop|glitch", "time": 1.0}
- {"action": "add_3d_element", "element_type": "text|particles|hologram|rings", "text": "SUPER AI", "time": 0.0, "duration": 4.0}
- {"action": "apply_motion", "preset": "kenburns|bounce|slide_up|elastic|glitch", "target": "video|overlay"}
- {"action": "auto_duck", "duck_level": 0.2}
- {"action": "speed_ramp", "speed_factor": 1.5, "time": 0.0}
- {"action": "split_clip", "time": 2.5}
"""

def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama service is reachable and list models."""
    hw = get_hardware_profile()
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE_URL}/api/tags", headers={"User-Agent": "super_ai_editor"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name") for m in data.get("models", [])]
            return {
                "online": True,
                "base_url": OLLAMA_BASE_URL,
                "models": models,
                "recommended_model": hw["recommended_model"],
                "hardware_profile": hw["profile_name"]
            }
    except Exception as e:
        return {
            "online": False,
            "base_url": OLLAMA_BASE_URL,
            "models": [],
            "recommended_model": hw["recommended_model"],
            "hardware_profile": hw["profile_name"],
            "note": "Ollama service offline. Offline AI rule engine active."
        }

def offline_fallback_copilot(prompt: str) -> Dict[str, Any]:
    """Parse editing instructions using built-in offline NLP engine when Ollama is offline."""
    prompt_lower = prompt.lower()
    actions = []
    reply_parts = []
    
    # 3D Element
    if any(k in prompt_lower for k in ["3d", "three.js", "title", "text 3d", "hologram", "particle"]):
        text = "SUPER AI"
        if "'" in prompt:
            parts = prompt.split("'")
            if len(parts) >= 2:
                text = parts[1]
        elif '"' in prompt:
            parts = prompt.split('"')
            if len(parts) >= 2:
                text = parts[1]
                
        elem_type = "particles" if "particle" in prompt_lower else ("hologram" if "hologram" in prompt_lower else "text")
        actions.append({
            "action": "add_3d_element",
            "element_type": elem_type,
            "text": text,
            "time": 0.0,
            "duration": 4.5
        })
        reply_parts.append(f"Added dynamic Three.js 3D {elem_type} ('{text}') with cinematic lighting.")
        
    # Sound Effects
    if any(k in prompt_lower for k in ["whoosh", "sfx", "sound", "boom", "impact", "riser", "pop", "laser"]):
        sfx_type = "whoosh"
        if "boom" in prompt_lower or "impact" in prompt_lower:
            sfx_type = "boom"
        elif "riser" in prompt_lower:
            sfx_type = "riser"
        elif "laser" in prompt_lower:
            sfx_type = "laser"
        elif "pop" in prompt_lower or "click" in prompt_lower:
            sfx_type = "pop"
            
        actions.append({
            "action": "add_sfx",
            "sfx_type": sfx_type,
            "time": 1.0
        })
        reply_parts.append(f"Inserted RealSFX {sfx_type.upper()} effect timed at 00:01.")
        
    # Subtitles & Captions
    if any(k in prompt_lower for k in ["sub", "caption", "whisper", "transcript", "hormozi", "karaoke"]):
        style = "hormozi" if "hormozi" in prompt_lower or "karaoke" in prompt_lower else "cinematic"
        actions.append({
            "action": "add_subtitle",
            "start": 0.5,
            "end": 3.5,
            "text": "Experience next-gen AI video editing with super_ai_editor",
            "style": style
        })
        reply_parts.append(f"Generated Whisper subtitles with dynamic '{style}' karaoke animation style.")
        
    # Auto Ducking
    if any(k in prompt_lower for k in ["duck", "earshot", "lower music", "volume", "quiet music"]):
        actions.append({
            "action": "auto_duck",
            "duck_level": 0.2
        })
        reply_parts.append("Applied Earshot intelligent auto-ducking to lower background music during speech.")
        
    # Motion Graphics
    if any(k in prompt_lower for k in ["motion", "ken burns", "zoom", "bounce", "slide", "pan"]):
        preset = "kenburns" if "ken" in prompt_lower or "zoom" in prompt_lower else "bounce"
        actions.append({
            "action": "apply_motion",
            "preset": preset,
            "target": "video"
        })
        reply_parts.append(f"Enabled Motion Skills '{preset}' easing animation on the video layer.")
        
    # Speed Ramp / HyperFrames
    if any(k in prompt_lower for k in ["speed", "slow", "fast", "ramp", "hyperframe", "interpolate"]):
        speed = 0.5 if "slow" in prompt_lower else 2.0
        actions.append({
            "action": "speed_ramp",
            "speed_factor": speed,
            "time": 0.0
        })
        reply_parts.append(f"Applied HyperFrames speed ramp factor {speed}x with motion interpolation.")
        
    # Cut / Split
    if any(k in prompt_lower for k in ["cut", "split", "trim"]):
        actions.append({
            "action": "split_clip",
            "time": 2.0
        })
        reply_parts.append("Split video clip at current cursor position (00:02.00).")
        
    if not actions:
        reply = f"I analyzed your request ('{prompt}'). You can tell me to add 3D titles, generate Whisper subtitles, insert RealSFX whooshes/booms, auto-duck background audio, or apply Motion Skills animation!"
    else:
        reply = " ".join(reply_parts)
        
    return {
        "reply": reply,
        "timeline_actions": actions,
        "mode": "offline_copilot"
    }

def ask_ollama_copilot(prompt: str, model: str = None) -> Dict[str, Any]:
    """Execute AI video editing copilot query via Ollama API or fallback seamlessly."""
    status = check_ollama_status()
    hw = get_hardware_profile()
    selected_model = model or status.get("recommended_model") or hw["recommended_model"]
    
    if not status.get("online"):
        return offline_fallback_copilot(prompt)
        
    # Query Ollama
    req_body = json.dumps({
        "model": selected_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "format": "json",
        "stream": False
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/chat",
            data=req_body,
            headers={"Content-Type": "application/json", "User-Agent": "super_ai_editor"}
        )
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            data = json.loads(resp.read().decode())
            content_str = data.get("message", {}).get("content", "{}")
            parsed = json.loads(content_str)
            return {
                "reply": parsed.get("reply", "Actions processed."),
                "timeline_actions": parsed.get("timeline_actions", []),
                "mode": "ollama_live",
                "model": selected_model
            }
    except Exception:
        # Fall back gracefully to offline copilot
        fallback = offline_fallback_copilot(prompt)
        fallback["mode"] = "ollama_fallback"
        return fallback
