import subprocess
from pathlib import Path
from typing import List, Dict, Any

def extract_thumbnail_strip(video_path: Path, output_dir: Path, count: int = 12) -> List[str]:
    """Extract a sequence of evenly spaced thumbnails for timeline scrubbing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Probe video duration
    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    try:
        dur_out = subprocess.check_output(dur_cmd).decode().strip()
        duration = float(dur_out)
    except Exception:
        duration = 10.0
        
    step = duration / max(1, count)
    thumbnails = []
    
    stem = video_path.stem
    for i in range(count):
        t = round(i * step, 2)
        thumb_name = f"{stem}_thumb_{i:03d}.jpg"
        out_file = output_dir / thumb_name
        
        # Only extract if doesn't exist
        if not out_file.exists():
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(t),
                "-i", str(video_path),
                "-vframes", "1",
                "-vf", "scale=160:-1",
                "-q:v", "5",
                str(out_file)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
        if out_file.exists():
            thumbnails.append(f"/api/hyperframes/thumbnails/{thumb_name}")
            
    return thumbnails

def apply_frame_interpolation(input_path: Path, output_path: Path, target_fps: int = 60, mode: str = "mci") -> Dict[str, Any]:
    """
    Interpolate video frames to high frame-rate using FFmpeg motion-compensated interpolation (minterpolate).
    mode: 'mci' (motion compensated interpolation) or 'blend' (frame blending).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if mode == "mci":
        vf = f"minterpolate=fps={target_fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"
    else:
        vf = f"minterpolate=fps={target_fps}:mi_mode=blend"
        
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-c:a", "copy",
        str(output_path)
    ]
    
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
        success = res.returncode == 0 and output_path.exists()
        return {
            "success": success,
            "target_fps": target_fps,
            "output_path": str(output_path),
            "output_url": f"/api/media/file/{output_path.name}" if success else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def apply_speed_ramp(input_path: Path, output_path: Path, speed_factor: float = 1.0) -> Dict[str, Any]:
    """
    Apply speed ramping with pitch-corrected audio time-stretching.
    speed_factor: e.g. 0.5 for 2x slow-mo, 2.0 for 2x fast-forward.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    speed_factor = max(0.1, min(10.0, speed_factor))
    
    # In FFmpeg setpts: 1/speed_factor
    pts_factor = 1.0 / speed_factor
    vf = f"setpts={pts_factor}*PTS"
    
    # Audio atempo filter supports between 0.5 and 2.0 per filter instance
    # Chain multiple atempo filters if needed
    af_filters = []
    rem_speed = speed_factor
    while rem_speed > 2.0:
        af_filters.append("atempo=2.0")
        rem_speed /= 2.0
    while rem_speed < 0.5:
        af_filters.append("atempo=0.5")
        rem_speed /= 0.5
    af_filters.append(f"atempo={rem_speed:.4f}")
    af = ",".join(af_filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-filter_complex", f"[0:v]{vf}[v];[0:a]{af}[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        str(output_path)
    ]
    
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        success = res.returncode == 0 and output_path.exists()
        return {
            "success": success,
            "speed_factor": speed_factor,
            "output_path": str(output_path),
            "output_url": f"/api/media/file/{output_path.name}" if success else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
