import unittest
import sys
from pathlib import Path

# Add root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.system_detector import get_hardware_profile, get_system_ram_gb
from backend.app.services.realsfx_service import (
    ensure_default_sfx_library,
    list_sfx_library,
    generate_custom_sfx,
    SFX_GENERATORS
)
from backend.app.services.earshot_service import analyze_audio_track, compute_auto_ducking
from backend.app.services.whisper_service import transcribe_audio_file, export_srt
from backend.app.services.ollama_service import check_ollama_status, ask_ollama_copilot, offline_fallback_copilot
from backend.app.services.render_service import render_timeline_project

class TestSuperAIEditorBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ensure_default_sfx_library()

    def test_01_system_detector(self):
        """Test hardware detection, RAM profile and Ollama model recommendation."""
        hw = get_hardware_profile()
        self.assertIn(hw["os"], ["macOS", "Windows", "Linux"])
        self.assertGreater(hw["total_ram_gb"], 0)
        self.assertIn("recommended_model", hw)
        self.assertIn(hw["recommended_model"], ["llama3.2:1b", "llama3.2:3b", "llama3.1:8b"])
        self.assertTrue(hw["docker_compatible"])

    def test_02_realsfx_generators(self):
        """Test sound synthesis for all sound types in RealSFX."""
        library = list_sfx_library()
        self.assertGreaterEqual(len(library), 6)
        types = [item["id"] for item in library]
        for expected in ["whoosh", "boom", "riser", "laser", "pop", "glitch"]:
            self.assertIn(expected, types)

        # Test prompt generator
        custom = generate_custom_sfx("cinematic explosion boom", duration=1.5)
        self.assertEqual(custom["type"], "boom")
        self.assertTrue(Path(ROOT_DIR / "backend" / "sfx_library" / custom["filename"]).exists())

    def test_03_earshot_analysis_and_ducking(self):
        """Test Earshot waveform, beat detection, and auto-ducking curves."""
        sfx_path = ROOT_DIR / "backend" / "sfx_library" / "boom.wav"
        res = analyze_audio_track(sfx_path)
        self.assertGreater(res["duration"], 0)
        self.assertEqual(len(res["waveform"]), 300)
        self.assertGreater(res["bpm"], 0)

        # Test auto-ducking calculation
        speech_intervals = [{"start": 1.0, "end": 3.0}]
        duck_points = compute_auto_ducking(speech_intervals, total_duration=5.0, duck_level=0.15)
        self.assertGreaterEqual(len(duck_points), 4)
        # Check that volume dips during speech
        speech_vol = [p["volume"] for p in duck_points if p["time"] == 1.0 or p["time"] == 3.0]
        self.assertTrue(all(v == 0.15 for v in speech_vol))

    def test_04_whisper_transcription(self):
        """Test Whisper speech transcription and SRT subtitle formatting."""
        sfx_path = ROOT_DIR / "backend" / "sfx_library" / "whoosh.wav"
        res = transcribe_audio_file(sfx_path)
        self.assertIn("segments", res)
        self.assertGreater(len(res["segments"]), 0)

        srt = export_srt(res["segments"])
        self.assertIn("-->", srt)
        self.assertIn("1", srt)

    def test_05_ollama_copilot(self):
        """Test Ollama status checking and offline fallback AI copilot."""
        status = check_ollama_status()
        self.assertIn("online", status)
        self.assertIn("recommended_model", status)

        # Test AI Video Copilot query
        prompt = "Add a 3D hologram title 'MATRIX' with boom sound effect and duck background audio"
        ans = ask_ollama_copilot(prompt)
        self.assertIn("reply", ans)
        self.assertIn("timeline_actions", ans)
        actions = [a["action"] for a in ans["timeline_actions"]]
        self.assertIn("add_3d_element", actions)
        self.assertIn("add_sfx", actions)
        self.assertIn("auto_duck", actions)

    def test_06_render_engine(self):
        """Test FFmpeg video rendering pipeline."""
        proj = {
            "duration": 2.0,
            "subtitles": [{"start": 0.2, "end": 1.8, "text": "SUPER AI EDITOR VERIFIED"}],
            "sfx_tracks": [{"sfx_type": "pop", "time": 0.5, "volume": 1.0}],
            "subtitle_style": "neon"
        }
        res = render_timeline_project(proj)
        self.assertTrue(res.get("success"), f"Render failed: {res.get('error')}")
        self.assertTrue((ROOT_DIR / "backend" / "exports" / res["output_filename"]).exists())
        self.assertGreater(res["size_mb"], 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
