import math
import struct
import wave
import os
import random
from pathlib import Path
from backend.app.config import SFX_DIR

def _write_wav(filepath: Path, samples: list[float], sample_rate: int = 44100):
    """Write mono float samples (-1.0 to 1.0) to 16-bit PCM WAV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        packed_frames = bytearray()
        for s in samples:
            # Clamp sample to [-1.0, 1.0]
            val = max(-1.0, min(1.0, s))
            int_val = int(val * 32767.0)
            packed_frames.extend(struct.pack('<h', int_val))
            
        wav_file.writeframes(packed_frames)

def generate_whoosh(duration: float = 0.8, sample_rate: int = 44100) -> list[float]:
    """Generate realistic whoosh sound using filtered noise and frequency sweep."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    # Simple lowpass/bandpass noise simulation
    prev = 0.0
    for i in range(total_samples):
        t = i / total_samples
        # Envelope: Gaussian hump centered around 0.5
        envelope = math.exp(-((t - 0.5) ** 2) / (2 * (0.16 ** 2)))
        
        # White noise
        white_noise = random.uniform(-1.0, 1.0)
        
        # Dynamic filter coefficient (sweeping cut-off)
        cutoff = 0.05 + 0.35 * math.sin(t * math.pi)
        prev += cutoff * (white_noise - prev)
        
        # Add subtle whistling tone
        whistle_freq = 300 + 700 * math.sin(t * math.pi)
        whistle = 0.15 * math.sin(2 * math.pi * whistle_freq * (i / sample_rate))
        
        sample = (prev * 0.85 + whistle) * envelope
        samples.append(sample)
        
    return samples

def generate_cinematic_boom(duration: float = 2.0, sample_rate: int = 44100) -> list[float]:
    """Generate a deep cinematic impact boom with sub-bass drop and transient."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(total_samples):
        t = i / sample_rate
        norm_t = i / total_samples
        
        # Transient click/punch in first 30ms
        transient = 0.0
        if t < 0.03:
            transient = random.uniform(-1.0, 1.0) * math.exp(-t / 0.008)
            
        # Pitch drops from 90Hz to 30Hz
        freq = 90.0 * math.exp(-norm_t * 3.5) + 30.0
        phase = 2 * math.pi * freq * t
        
        # Sub-bass sine wave with exponential decay
        decay = math.exp(-norm_t * 3.2)
        sub = math.sin(phase) * decay
        
        # Harmonic overtone
        sub_harmonic = 0.3 * math.sin(phase * 2.0) * math.exp(-norm_t * 5.0)
        
        # Low rumble noise
        rumble = random.uniform(-0.15, 0.15) * math.exp(-norm_t * 2.0)
        
        sample = (transient * 0.4) + (sub * 0.7) + (sub_harmonic * 0.2) + rumble
        samples.append(sample)
        
    return samples

def generate_riser(duration: float = 2.5, sample_rate: int = 44100) -> list[float]:
    """Generate energetic tension riser building up in pitch and volume."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    phase = 0.0
    for i in range(total_samples):
        norm_t = i / total_samples
        # Exponential pitch rise from 150Hz to 1200Hz
        freq = 150.0 * ((1200.0 / 150.0) ** (norm_t ** 1.8))
        phase += 2 * math.pi * freq / sample_rate
        
        # Volume ramp from 0.05 to 1.0
        volume = 0.05 + 0.95 * (norm_t ** 2.0)
        
        # Combined saw + sine + noise
        saw = (phase % (2 * math.pi)) / math.pi - 1.0
        sine = math.sin(phase)
        noise = random.uniform(-0.3, 0.3) * norm_t
        
        sample = (0.5 * sine + 0.3 * saw + noise) * volume
        samples.append(sample)
        
    return samples

def generate_laser_zap(duration: float = 0.4, sample_rate: int = 44100) -> list[float]:
    """Generate sci-fi laser zap sound."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(total_samples):
        t = i / sample_rate
        norm_t = i / total_samples
        
        # Rapid downward pitch sweep: 2200Hz down to 80Hz
        freq = 2200.0 * math.exp(-norm_t * 9.0) + 80.0
        phase = 2 * math.pi * freq * t
        
        envelope = math.exp(-norm_t * 7.0)
        sample = math.sin(phase) * envelope
        samples.append(sample)
        
    return samples

def generate_ui_pop(duration: float = 0.1, sample_rate: int = 44100) -> list[float]:
    """Generate clean UI button click or pop sound."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(total_samples):
        t = i / sample_rate
        norm_t = i / total_samples
        
        freq = 1400.0 * (1.0 - norm_t * 0.6)
        phase = 2 * math.pi * freq * t
        
        envelope = math.exp(-norm_t * 22.0)
        sample = math.sin(phase) * envelope
        samples.append(sample)
        
    return samples

def generate_glitch(duration: float = 0.5, sample_rate: int = 44100) -> list[float]:
    """Generate digital glitch stutter."""
    total_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(total_samples):
        norm_t = i / total_samples
        # Segment into discrete stutter chunks
        chunk = int(norm_t * 16)
        freq = 200 + (chunk * 173) % 800
        
        is_burst = (chunk % 3 != 0)
        if is_burst:
            sq = 1.0 if math.sin(2 * math.pi * freq * (i / sample_rate)) > 0 else -1.0
            noise = random.uniform(-0.4, 0.4)
            sample = (sq * 0.4 + noise * 0.6) * 0.7
        else:
            sample = 0.0
            
        samples.append(sample)
        
    return samples

# Sound effect generator registry
SFX_GENERATORS = {
    "whoosh": generate_whoosh,
    "boom": generate_cinematic_boom,
    "riser": generate_riser,
    "laser": generate_laser_zap,
    "pop": generate_ui_pop,
    "glitch": generate_glitch,
}

def ensure_default_sfx_library():
    """Ensure standard sound effects are generated and cached in SFX_DIR."""
    created = []
    for name, gen_fn in SFX_GENERATORS.items():
        filepath = SFX_DIR / f"{name}.wav"
        if not filepath.exists():
            samples = gen_fn()
            _write_wav(filepath, samples)
            created.append(name)
    return created

def generate_custom_sfx(prompt: str, duration: float = 1.0) -> dict:
    """Generate or retrieve procedural SFX based on text prompt."""
    prompt_lower = prompt.lower()
    
    # Match keywords
    if any(k in prompt_lower for k in ["boom", "impact", "bass", "hit", "explosion", "drop"]):
        sfx_type = "boom"
        duration = min(duration or 2.0, 3.0)
    elif any(k in prompt_lower for k in ["riser", "build", "tension", "suspense", "up"]):
        sfx_type = "riser"
        duration = min(duration or 2.5, 4.0)
    elif any(k in prompt_lower for k in ["laser", "zap", "pew", "sci-fi", "space"]):
        sfx_type = "laser"
        duration = min(duration or 0.4, 1.0)
    elif any(k in prompt_lower for k in ["click", "pop", "button", "snap", "tap"]):
        sfx_type = "pop"
        duration = min(duration or 0.1, 0.5)
    elif any(k in prompt_lower for k in ["glitch", "stutter", "digital", "noise", "error"]):
        sfx_type = "glitch"
        duration = min(duration or 0.5, 1.5)
    else:
        sfx_type = "whoosh"
        duration = min(duration or 0.8, 2.0)
        
    gen_fn = SFX_GENERATORS.get(sfx_type, generate_whoosh)
    samples = gen_fn(duration=duration)
    
    # Save to unique or standard file
    clean_id = f"{sfx_type}_{abs(hash(prompt + str(duration))) % 100000}"
    filename = f"{clean_id}.wav"
    filepath = SFX_DIR / filename
    _write_wav(filepath, samples)
    
    return {
        "id": clean_id,
        "name": f"RealSFX {sfx_type.capitalize()} ({prompt})",
        "type": sfx_type,
        "duration": duration,
        "filename": filename,
        "url": f"/api/realsfx/audio/{filename}"
    }

def list_sfx_library() -> list[dict]:
    """List available sound effects in the RealSFX library."""
    ensure_default_sfx_library()
    items = []
    presets = [
        {"id": "whoosh", "name": "Cinematic Fast Whoosh", "type": "Transition", "duration": 0.8},
        {"id": "boom", "name": "Deep Sub Bass Boom Impact", "type": "Impact", "duration": 2.0},
        {"id": "riser", "name": "Energy Tension Riser", "type": "Build-up", "duration": 2.5},
        {"id": "laser", "name": "Sci-Fi Energy Laser Zap", "type": "Synthetic", "duration": 0.4},
        {"id": "pop", "name": "Modern Minimalist UI Pop", "type": "Foley", "duration": 0.1},
        {"id": "glitch", "name": "Cyber Digital Stutter Glitch", "type": "Glitch", "duration": 0.5},
    ]
    
    for p in presets:
        fn = f"{p['id']}.wav"
        items.append({
            **p,
            "filename": fn,
            "url": f"/api/realsfx/audio/{fn}"
        })
        
    return items
