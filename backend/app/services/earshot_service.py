import math
import struct
import subprocess
import wave
from pathlib import Path
from typing import Dict, List, Any

def extract_audio_to_wav(input_path: Path, output_wav_path: Path, sample_rate: int = 22050) -> bool:
    """Extract audio from video or audio file to 16-bit mono WAV using FFmpeg."""
    output_wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ac", "1",
        "-ar", str(sample_rate),
        str(output_wav_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0 and output_wav_path.exists()
    except Exception:
        return False

def read_wav_samples(wav_path: Path) -> tuple[list[float], int]:
    """Read float samples (-1.0 to 1.0) and sample rate from 16-bit PCM WAV."""
    with wave.open(str(wav_path), 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        raw_bytes = wf.readframes(n_frames)
        
    samples = []
    if sampwidth == 2:
        # 16-bit signed
        total_samples = len(raw_bytes) // (2 * n_channels)
        fmt = f"<{total_samples * n_channels}h"
        raw_ints = struct.unpack(fmt, raw_bytes)
        
        # Take first channel or average
        if n_channels == 1:
            samples = [val / 32768.0 for val in raw_ints]
        else:
            for i in range(0, len(raw_ints), n_channels):
                avg = sum(raw_ints[i:i + n_channels]) / (n_channels * 32768.0)
                samples.append(avg)
    else:
        # Fallback for 8-bit
        for b in raw_bytes:
            samples.append((b - 128) / 128.0)
            
    return samples, framerate

def analyze_audio_track(filepath: Path) -> Dict[str, Any]:
    """Perform full Earshot audio intelligence analysis."""
    # If not a wav, convert to temp wav
    temp_wav = filepath.with_suffix(".earshot.wav")
    need_cleanup = False
    
    if filepath.suffix.lower() == ".wav":
        wav_path = filepath
    else:
        success = extract_audio_to_wav(filepath, temp_wav)
        if not success:
            return {
                "error": "Could not extract audio track",
                "duration": 0,
                "waveform": [],
                "bpm": 120,
                "beats": [],
                "silence_intervals": []
            }
        wav_path = temp_wav
        need_cleanup = True
        
    try:
        samples, sr = read_wav_samples(wav_path)
    except Exception as e:
        if need_cleanup and temp_wav.exists():
            temp_wav.unlink(missing_ok=True)
        return {"error": str(e), "duration": 0, "waveform": [], "bpm": 120, "beats": []}
        
    if need_cleanup and temp_wav.exists():
        temp_wav.unlink(missing_ok=True)
        
    total_samples = len(samples)
    duration = total_samples / sr if sr > 0 else 0
    if duration == 0:
        return {"duration": 0, "waveform": [], "bpm": 120, "beats": [], "silence_intervals": []}
        
    # 1. Downsampled Waveform (300 points for UI rendering)
    num_waveform_points = min(300, total_samples)
    step = total_samples / num_waveform_points
    waveform = []
    
    for i in range(num_waveform_points):
        start = int(i * step)
        end = min(int((i + 1) * step), total_samples)
        segment = samples[start:end]
        if segment:
            rms = math.sqrt(sum(s * s for s in segment) / len(segment))
            peak = max(abs(s) for s in segment)
            val = round((rms * 0.7 + peak * 0.3), 3)
            waveform.append(min(1.0, val))
        else:
            waveform.append(0.0)
            
    # 2. Energy and Onset / Beat Detection
    # Calculate energy in 50ms windows
    window_size = int(sr * 0.05)
    hop_size = int(sr * 0.025)
    energies = []
    times = []
    
    for idx in range(0, total_samples - window_size, hop_size):
        seg = samples[idx:idx + window_size]
        e = sum(s * s for s in seg) / len(seg)
        energies.append(e)
        times.append(idx / sr)
        
    # Detect local peaks in energy (onsets)
    beats = []
    avg_energy = sum(energies) / len(energies) if energies else 0.001
    threshold = avg_energy * 1.6
    
    last_beat_time = -0.3
    for i in range(1, len(energies) - 1):
        t = times[i]
        if energies[i] > threshold and energies[i] > energies[i - 1] and energies[i] > energies[i + 1]:
            if t - last_beat_time >= 0.28:  # Enforce minimum distance between beats (~210 BPM max)
                beats.append(round(t, 2))
                last_beat_time = t
                
    # Estimate BPM from intervals
    bpm = 120.0
    if len(beats) >= 4:
        intervals = [beats[i] - beats[i - 1] for i in range(1, len(beats))]
        avg_interval = sum(intervals) / len(intervals)
        if 0.3 <= avg_interval <= 1.5:
            bpm = round(60.0 / avg_interval, 1)
            
    # 3. Detect Silence Intervals (< -35 dB for > 0.4s)
    silence_intervals = []
    silence_threshold = 0.015  # approx -36 dB
    in_silence = False
    silence_start = 0.0
    
    for i, t in enumerate(times):
        is_quiet = (energies[i] < silence_threshold * silence_threshold)
        if is_quiet and not in_silence:
            in_silence = True
            silence_start = t
        elif not is_quiet and in_silence:
            in_silence = False
            if t - silence_start >= 0.4:
                silence_intervals.append({
                    "start": round(silence_start, 2),
                    "end": round(t, 2),
                    "duration": round(t - silence_start, 2)
                })
                
    if in_silence and (duration - silence_start >= 0.4):
        silence_intervals.append({
            "start": round(silence_start, 2),
            "end": round(duration, 2),
            "duration": round(duration - silence_start, 2)
        })
        
    return {
        "duration": round(duration, 2),
        "sample_rate": sr,
        "waveform": waveform,
        "bpm": bpm,
        "beats": beats[:80],  # Return up to 80 primary beat markers
        "silence_intervals": silence_intervals,
        "peak_amplitude": round(max((abs(s) for s in samples), default=0.0), 3)
    }

def compute_auto_ducking(speech_intervals: List[Dict[str, float]], total_duration: float, duck_level: float = 0.2) -> List[Dict[str, float]]:
    """
    Generate volume automation keyframe points for background music track.
    duck_level: 0.2 (-14dB), 1.0 = full volume.
    Returns list of {time: float, volume: float}.
    """
    if not speech_intervals:
        return [{"time": 0.0, "volume": 1.0}, {"time": total_duration, "volume": 1.0}]
        
    keyframes = []
    attack = 0.25   # 250ms ramp down
    release = 0.35  # 350ms ramp up
    
    # Sort intervals
    intervals = sorted(speech_intervals, key=lambda x: x["start"])
    
    # Merge overlapping or closely adjacent intervals (< 0.4s)
    merged = []
    for cur in intervals:
        if not merged:
            merged.append(dict(cur))
        else:
            prev = merged[-1]
            if cur["start"] <= prev["end"] + 0.4:
                prev["end"] = max(prev["end"], cur["end"])
            else:
                merged.append(dict(cur))
                
    last_t = 0.0
    for interval in merged:
        s = max(0.0, interval["start"])
        e = min(total_duration, interval["end"])
        
        # Before speech
        t_before = max(last_t, s - attack)
        keyframes.append({"time": round(t_before, 2), "volume": 1.0})
        keyframes.append({"time": round(s, 2), "volume": round(duck_level, 2)})
        
        # During speech
        keyframes.append({"time": round(e, 2), "volume": round(duck_level, 2)})
        
        # After speech
        t_after = min(total_duration, e + release)
        keyframes.append({"time": round(t_after, 2), "volume": 1.0})
        last_t = t_after
        
    if last_t < total_duration:
        keyframes.append({"time": round(total_duration, 2), "volume": 1.0})
        
    return keyframes
