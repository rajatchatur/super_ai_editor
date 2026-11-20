import json
import mimetypes
import re
import subprocess
import time
from pathlib import Path

MEDIA_TYPES = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
    ".mkv": "video/x-matroska",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
}


def sanitize_filename(filename):
    """Return a safe, flat filename that cannot escape the uploads directory."""
    name = (filename or "").replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[\x00-\x1f\x7f]", "", name).replace(" ", "_")
    if not name or name in (".", ".."):
        name = f"upload_{int(time.time() * 1000)}"
    return name


def guess_media_type(path, declared_type=None):
    """Map a stored file to its real browser-friendly MIME type."""
    media_type = MEDIA_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
    if media_type:
        return media_type
    if declared_type and declared_type.startswith(("video/", "audio/", "image/")):
        return declared_type
    return "application/octet-stream"


def media_kind(media_type):
    if media_type.startswith(("video/", "audio/", "image/")):
        return media_type.split("/")[0]
    return "file"


def parse_multipart(body, content_type):
    """Parse the first file field of a multipart/form-data body.

    Returns (filename, declared_content_type, exact_bytes) or None. The payload
    is preserved byte-for-byte: only the single CRLF that precedes the next
    boundary delimiter is removed, so binary media is never corrupted.
    """
    if "boundary=" not in content_type:
        return None
    boundary = content_type.split("boundary=", 1)[1].split(";", 1)[0].strip().strip('"')
    if not boundary:
        return None
    delimiter = b"--" + boundary.encode()

    for part in body.split(delimiter):
        if b'filename="' not in part or b"\r\n\r\n" not in part:
            continue
        header_data, payload = part.split(b"\r\n\r\n", 1)
        # Remove exactly the single CRLF that delimits the next boundary; any
        # further CR/LF bytes belong to the file and must be preserved.
        if payload.endswith(b"\r\n"):
            payload = payload[:-2]
        headers = header_data.decode("utf-8", errors="ignore")
        match = re.search(r'filename="([^"]*)"', headers)
        if not match:
            continue
        filename = match.group(1)
        declared = None
        type_match = re.search(r"Content-Type:\s*([^\r\n;]+)", headers, re.IGNORECASE)
        if type_match:
            declared = type_match.group(1).strip()
        return filename, declared, payload
    return None


def probe_media(path, check_output=None):
    """Extract duration, dimensions, fps and audio presence with ffprobe."""
    run = check_output or subprocess.check_output
    metadata = {
        "duration": 5.0,
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "has_audio": False,
    }
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path),
        ]
        info = json.loads(run(cmd))
        duration = info.get("format", {}).get("duration")
        if duration is not None:
            metadata["duration"] = float(duration)
        for st in info.get("streams", []):
            if st.get("codec_type") == "video":
                metadata["width"] = int(st.get("width") or 1920)
                metadata["height"] = int(st.get("height") or 1080)
                r_fps = st.get("r_frame_rate", "30/1")
                if "/" in r_fps:
                    n, d = r_fps.split("/")
                    if float(d):
                        metadata["fps"] = round(float(n) / float(d), 2)
            elif st.get("codec_type") == "audio":
                metadata["has_audio"] = True
    except Exception:
        pass
    return metadata


def build_media_response(clean_name, dest_path, declared_type=None):
    media_type = guess_media_type(dest_path, declared_type)
    metadata = probe_media(dest_path)
    metadata["duration"] = round(metadata["duration"], 2)
    return {
        "filename": clean_name,
        "url": f"/api/media/file/{clean_name}",
        "media_type": media_type,
        "kind": media_kind(media_type),
        **metadata,
    }
