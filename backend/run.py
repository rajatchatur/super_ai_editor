#!/usr/bin/env python3
import sys
import os
import time
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

def run_uvicorn():
    import uvicorn
    from backend.app.config import HOST, PORT
    print(f"🚀 Starting super_ai_editor backend with Uvicorn on http://{HOST}:{PORT}")
    uvicorn.run("backend.app.main:app", host=HOST, port=PORT, reload=False)

def run_standalone():
    """Built-in zero-dependency HTTP server fallback implementing the exact same REST API."""
    import http.server
    import json
    import urllib.parse
    from backend.app.services.system_detector import get_hardware_profile
    from backend.app.services.realsfx_service import list_sfx_library, generate_custom_sfx, ensure_default_sfx_library
    from backend.app.services.earshot_service import analyze_audio_track, compute_auto_ducking
    from backend.app.services.whisper_service import transcribe_audio_file, export_srt
    from backend.app.services.ollama_service import check_ollama_status, ask_ollama_copilot
    from backend.app.services.render_service import render_timeline_project
    from backend.app.routers.media import get_demo_project
    from backend.app.media_utils import (
        build_media_response,
        guess_media_type,
        parse_multipart,
        sanitize_filename,
    )
    from backend.app.config import HOST, PORT, SFX_DIR, EXPORT_DIR, UPLOAD_DIR

    ensure_default_sfx_library()

    class APIServerHandler(http.server.BaseHTTPRequestHandler):
        def _send_cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

        def do_OPTIONS(self):
            self.send_response(200)
            self._send_cors()
            self.end_headers()

        def _send_json(self, data, status=200):
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self):
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                return json.loads(raw) if raw else {}
            except Exception:
                return {}

        def _serve_media_file(self, fp):
            """Stream a media file with HTTP Range support so video/audio can seek."""
            total = fp.stat().st_size
            media_type = guess_media_type(fp)
            start, end = 0, total - 1
            status = 200

            range_header = self.headers.get("Range", "")
            if range_header.startswith("bytes="):
                rng = range_header.split("=", 1)[1].split(",", 1)[0].strip()
                first, _, last = rng.partition("-")
                try:
                    if first:
                        start = int(first)
                        end = int(last) if last else total - 1
                    elif last:
                        start = max(0, total - int(last))
                    if start >= total or end < start:
                        self.send_response(416)
                        self.send_header("Content-Range", f"bytes */{total}")
                        self._send_cors()
                        self.end_headers()
                        return
                    end = min(end, total - 1)
                    status = 206
                except ValueError:
                    start, end, status = 0, total - 1, 200

            length = end - start + 1
            self.send_response(status)
            self.send_header("Content-Type", media_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            if status == 206:
                self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
            self._send_cors()
            self.end_headers()
            with open(fp, "rb") as handle:
                handle.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = handle.read(min(65536, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)

        def do_GET(self):
            url = urllib.parse.urlparse(self.path)
            path = url.path

            if path == "/api/health":
                hw = get_hardware_profile()
                ollama = check_ollama_status()
                self._send_json({
                    "status": "online",
                    "app": "super_ai_editor",
                    "version": "1.0.0",
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
                })
            elif path == "/api/system/profile":
                self._send_json(get_hardware_profile())
            elif path == "/api/realsfx/library":
                self._send_json(list_sfx_library())
            elif path.startswith("/api/realsfx/audio/"):
                fn = path.split("/")[-1]
                fp = SFX_DIR / fn
                if fp.exists():
                    data = fp.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(data)))
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._send_json({"error": "Audio file not found"}, 404)
            elif path == "/api/ollama/status":
                self._send_json(check_ollama_status())
            elif path == "/api/media/demo_project":
                self._send_json(get_demo_project())
            elif path.startswith("/api/media/file/"):
                fn = sanitize_filename(path.split("/")[-1])
                fp = UPLOAD_DIR / fn
                if fp.exists() and fp.is_file():
                    self._serve_media_file(fp)
                else:
                    self._send_json({"error": "Media file not found"}, 404)
            elif path.startswith("/api/render/download/"):
                fn = path.split("/")[-1]
                fp = EXPORT_DIR / fn
                if fp.exists():
                    data = fp.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Content-Disposition", f'attachment; filename="{fn}"')
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._send_json({"error": "Rendered video not found"}, 404)
            else:
                # Check static files in frontend/dist
                dist_path = ROOT_DIR / "frontend" / "dist"
                clean_path = path.lstrip("/") or "index.html"
                target_file = dist_path / clean_path
                if dist_path.exists() and target_file.exists() and target_file.is_file():
                    ext = target_file.suffix.lower()
                    mime = "text/html" if ext == ".html" else ("application/javascript" if ext == ".js" else ("text/css" if ext == ".css" else "application/octet-stream"))
                    data = target_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(data)
                elif dist_path.exists() and (dist_path / "index.html").exists():
                    data = (dist_path / "index.html").read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(data)))
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._send_json({"message": "super_ai_editor API online", "path": path})

        def do_POST(self):
            url = urllib.parse.urlparse(self.path)
            path = url.path

            if path == "/api/media/upload":
                content_type = self.headers.get("Content-Type", "")
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length) if length > 0 else b""

                parsed = parse_multipart(body, content_type)
                if parsed is None:
                    self._send_json({"error": "No file uploaded"}, 400)
                    return

                filename, declared_type, file_bytes = parsed
                if not file_bytes:
                    self._send_json({"error": "No file uploaded"}, 400)
                    return

                clean_name = sanitize_filename(filename)
                dest_path = UPLOAD_DIR / clean_name
                if dest_path.exists():
                    dest_path = UPLOAD_DIR / f"{dest_path.stem}_{int(time.time() * 1000)}{dest_path.suffix}"
                    clean_name = dest_path.name

                dest_path.write_bytes(file_bytes)
                self._send_json(build_media_response(clean_name, dest_path, declared_type))
                return

            payload = self._read_json()

            if path == "/api/realsfx/generate":
                prompt = payload.get("prompt", "whoosh")
                dur = payload.get("duration", 1.0)
                self._send_json(generate_custom_sfx(prompt, dur))
            elif path == "/api/earshot/analyze":
                fn = payload.get("filename", "whoosh.wav")
                fp = UPLOAD_DIR / fn if (UPLOAD_DIR / fn).exists() else (SFX_DIR / fn)
                self._send_json(analyze_audio_track(fp))
            elif path == "/api/earshot/ducking":
                sp = payload.get("speech_intervals", [])
                tot = payload.get("total_duration", 5.0)
                lvl = payload.get("duck_level", 0.2)
                self._send_json({"keyframes": compute_auto_ducking(sp, tot, lvl)})
            elif path == "/api/whisper/transcribe":
                fn = payload.get("filename", "whoosh.wav")
                fp = UPLOAD_DIR / fn if (UPLOAD_DIR / fn).exists() else (SFX_DIR / fn)
                self._send_json(transcribe_audio_file(fp))
            elif path == "/api/whisper/export_srt":
                segs = payload.get("segments", [])
                self._send_json({"srt": export_srt(segs)})
            elif path == "/api/ollama/chat":
                prompt = payload.get("prompt", "")
                model = payload.get("model", None)
                self._send_json(ask_ollama_copilot(prompt, model))
            elif path == "/api/render/export":
                res = render_timeline_project(payload)
                self._send_json(res, 200 if res.get("success") else 500)
            else:
                self._send_json({"error": "Unknown POST endpoint", "path": path}, 404)

    server = http.server.ThreadingHTTPServer((HOST, PORT), APIServerHandler)
    print(f"🚀 super_ai_editor standalone zero-dependency server running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        import uvicorn
        run_uvicorn()
    except ImportError:
        run_standalone()
