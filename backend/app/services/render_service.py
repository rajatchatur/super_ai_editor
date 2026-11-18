import subprocess
import json
import uuid
from pathlib import Path
from typing import Dict, List, Any
from backend.app.config import EXPORT_DIR, SFX_DIR, UPLOAD_DIR
from backend.app.services.whisper_service import export_srt

def render_timeline_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render video project timeline into final MP4 video using FFmpeg.
    Compatible with all FFmpeg builds on macOS, Windows 10/11, and Linux.
    """
    render_id = str(uuid.uuid4())[:8]
    output_filename = f"export_{render_id}.mp4"
    output_path = EXPORT_DIR / output_filename

    video_clips = project_data.get("video_clips", [])
    subtitles = project_data.get("subtitles", [])
    sfx_tracks = project_data.get("sfx_tracks", [])
    total_duration = float(project_data.get("duration", 5.0))

    if video_clips:
        clip_max = max((c.get("start", 0.0) + c.get("duration", 5.0) for c in video_clips), default=5.0)
        total_duration = max(total_duration, clip_max)

    total_duration = max(1.0, min(600.0, total_duration))

    # 1. Base Video Source
    input_args = []
    has_custom_video = False
    if video_clips and (UPLOAD_DIR / video_clips[0].get("filename", "")).exists():
        src_path = UPLOAD_DIR / video_clips[0]["filename"]
        input_args.extend(["-i", str(src_path)])
        has_custom_video = True
    else:
        # Generates dark sleek studio background
        input_args.extend([
            "-f", "lavfi",
            "-i", f"color=c=0x0f172a:s=1920x1080:d={total_duration}:r=30"
        ])

    # 2. Subtitles handling: write .srt file
    srt_path = EXPORT_DIR / f"subs_{render_id}.srt"
    has_subtitles = False
    if subtitles:
        srt_content = export_srt(subtitles)
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        has_subtitles = srt_path.exists() and len(subtitles) > 0

    # 3. Sound Effects (RealSFX)
    sfx_inputs = []
    sfx_mappings = []
    current_input_idx = 1

    for sfx in sfx_tracks:
        fn = sfx.get("filename")
        p = SFX_DIR / fn if fn else (SFX_DIR / f"{sfx.get('sfx_type', 'whoosh')}.wav")
        if p.exists():
            sfx_inputs.extend(["-i", str(p)])
            sfx_mappings.append((sfx, current_input_idx))
            current_input_idx += 1

    # Add subtitle input if present
    sub_input_idx = None
    if has_subtitles:
        sub_input_idx = current_input_idx
        current_input_idx += 1

    # 4. Build command
    cmd = ["ffmpeg", "-y"]
    # Base video input
    cmd.extend(input_args)
    # SFX inputs
    cmd.extend(sfx_inputs)
    # Subtitle input (if any)
    if has_subtitles:
        cmd.extend(["-i", str(srt_path)])

    # Audio filtergraph
    filter_complex = []
    if sfx_mappings:
        amix_inputs = []
        for sfx_info, in_idx in sfx_mappings:
            delay_ms = max(0, int(float(sfx_info.get("time", 0.0)) * 1000))
            vol = float(sfx_info.get("volume", 1.0))
            filter_complex.append(f"[{in_idx}:a]adelay={delay_ms}|{delay_ms},volume={vol}[sfx{in_idx}]")
            amix_inputs.append(f"[sfx{in_idx}]")

        if len(amix_inputs) == 1:
            cmd.extend([
                "-filter_complex", filter_complex[0],
                "-map", "0:v",
                "-map", f"[sfx{sfx_mappings[0][1]}]"
            ])
        else:
            mix_chain = "".join(amix_inputs)
            filter_str = ";".join(filter_complex) + f";{mix_chain}amix=inputs={len(amix_inputs)}:dropout_transition=2[aout]"
            cmd.extend([
                "-filter_complex", filter_str,
                "-map", "0:v",
                "-map", "[aout]"
            ])
    else:
        # Generate silent track or copy original audio
        if has_custom_video:
            cmd.extend(["-map", "0:v", "-map", "0:a?"])
        else:
            cmd.extend([
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
                "-map", "0:v", "-map", f"{current_input_idx}:a"
            ])

    # Map subtitles if available
    if has_subtitles and sub_input_idx is not None:
        cmd.extend(["-map", f"{sub_input_idx}:s", "-c:s", "mov_text"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(total_duration),
        str(output_path)
    ])

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        success = res.returncode == 0 and output_path.exists()

        if srt_path.exists():
            srt_path.unlink(missing_ok=True)

        if success:
            size_mb = round(output_path.stat().st_size / (1024 * 1024), 2)
            return {
                "success": True,
                "render_id": render_id,
                "output_filename": output_filename,
                "output_url": f"/api/render/download/{output_filename}",
                "duration": total_duration,
                "size_mb": size_mb
            }
        else:
            return {
                "success": False,
                "error": res.stderr.decode("utf-8", errors="ignore")[-400:],
                "command": " ".join(cmd)
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
