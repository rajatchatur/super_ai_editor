import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Make the project package importable when this test is run directly.
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app import media_utils
from backend.app.routers import media


FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


def _make_sample(suffix, out_dir):
    """Generate a tiny real media file with ffmpeg, or return None if unavailable."""
    if not FFMPEG:
        return None
    path = Path(out_dir) / f"sample{suffix}"
    cmds = {
        ".mp4": ["-f", "lavfi", "-i", "testsrc=size=160x120:rate=24",
                 "-f", "lavfi", "-i", "sine=frequency=440", "-t", "1",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
        ".mp3": ["-f", "lavfi", "-i", "sine=frequency=440", "-t", "1", "-c:a", "libmp3lame"],
        ".wav": ["-f", "lavfi", "-i", "sine=frequency=440", "-t", "1"],
        ".png": ["-f", "lavfi", "-i", "testsrc=size=160x120:rate=1", "-frames:v", "1"],
        ".jpg": ["-f", "lavfi", "-i", "testsrc=size=160x120:rate=1", "-frames:v", "1"],
    }
    try:
        subprocess.run(
            [FFMPEG, "-y", *cmds[suffix], str(path)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=True,
        )
    except Exception:
        return None
    return path


class TestMediaUpload(unittest.TestCase):
    def test_upload_persists_file_and_returns_usable_file_url(self):
        file_bytes = b"test media bytes"
        ffprobe_result = {
            "format": {"duration": "2.5"},
            "streams": [
                {
                    "codec_type": "video",
                    "width": 640,
                    "height": 360,
                    "r_frame_rate": "24/1",
                },
                {"codec_type": "audio"},
            ],
        }
        app = FastAPI()
        app.include_router(media.router)

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)), patch.object(
                media_utils.subprocess, "check_output", return_value=json.dumps(ffprobe_result).encode()
            ):
                with TestClient(app) as client:
                    response = client.post(
                        "/api/media/upload",
                        files={"file": ("sample video.mp4", file_bytes, "video/mp4")},
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    result = response.json()
                    self.assertEqual(result["filename"], "sample_video.mp4")
                    self.assertEqual(result["url"], "/api/media/file/sample_video.mp4")
                    self.assertEqual(result["media_type"], "video/mp4")
                    self.assertEqual(result["kind"], "video")
                    self.assertEqual(result["duration"], 2.5)
                    self.assertEqual(result["width"], 640)
                    self.assertEqual(result["height"], 360)
                    self.assertEqual(result["fps"], 24.0)
                    self.assertTrue(result["has_audio"])
                    self.assertEqual((Path(temp_dir) / result["filename"]).read_bytes(), file_bytes)

                    served_file = client.get(result["url"])
                    self.assertEqual(served_file.status_code, 200)
                    self.assertEqual(served_file.content, file_bytes)


class TestMediaUploadTypes(unittest.TestCase):
    """Video, audio and image uploads keep their MIME type and survive a round-trip."""

    def _client(self, temp_dir):
        app = FastAPI()
        app.include_router(media.router)
        return TestClient(app)

    def _assert_round_trip(self, client, temp_dir, name, data, declared, expected_type, expected_kind):
        response = client.post("/api/media/upload", files={"file": (name, data, declared)})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(result["filename"], name.replace(" ", "_"))
        self.assertEqual(result["media_type"], expected_type)
        self.assertEqual(result["kind"], expected_kind)
        self.assertEqual((Path(temp_dir) / result["filename"]).read_bytes(), data)

        served = client.get(result["url"])
        self.assertEqual(served.status_code, 200)
        self.assertEqual(served.content, data)
        self.assertEqual(served.headers["content-type"].split(";")[0], expected_type)

    def test_video_audio_image_round_trip(self):
        cases = [
            ("clip.mp4", b"\x00\x00\x00\x18ftypmp42VIDEO\xff\xd9", "video/mp4", "video/mp4", "video"),
            ("movie.mov", b"\x00\x00\x00\x14ftypqt  MOOV", "video/quicktime", "video/quicktime", "video"),
            ("clip.webm", b"\x1a\x45\xdf\xa3WEBM", "video/webm", "video/webm", "video"),
            ("song.mp3", b"ID3\x04\x00\x00AUDIO\x00\x0a", "audio/mpeg", "audio/mpeg", "audio"),
            ("track.wav", b"RIFFxxxxWAVEfmt \x00\xff", "audio/wav", "audio/wav", "audio"),
            ("voice.m4a", b"\x00\x00\x00\x20ftypM4A ", "audio/mp4", "audio/mp4", "audio"),
            ("photo.png", b"\x89PNG\r\n\x1a\nIMAGEDATA", "image/png", "image/png", "image"),
            ("photo.jpg", b"\xff\xd8\xff\xe0JPEGDATA", "image/jpeg", "image/jpeg", "image"),
            ("photo.webp", b"RIFFxxxxWEBP", "image/webp", "image/webp", "image"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)), patch.object(
                media_utils.subprocess, "check_output", side_effect=Exception("no ffprobe")
            ):
                with self._client(temp_dir) as client:
                    for name, data, declared, expected_type, expected_kind in cases:
                        with self.subTest(name=name):
                            self._assert_round_trip(
                                client, temp_dir, name, data, declared, expected_type, expected_kind
                            )

    def test_binary_payload_is_not_corrupted(self):
        # Trailing CR/LF and NUL bytes must be preserved exactly.
        payload = b"\x00\x01\r\n\xffbinary\x00\r\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)), patch.object(
                media_utils.subprocess, "check_output", side_effect=Exception("no ffprobe")
            ):
                with self._client(temp_dir) as client:
                    response = client.post(
                        "/api/media/upload",
                        files={"file": ("clip.mp4", payload, "video/mp4")},
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual((Path(temp_dir) / "clip.mp4").read_bytes(), payload)

    def test_duplicate_upload_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)), patch.object(
                media_utils.subprocess, "check_output", side_effect=Exception("no ffprobe")
            ):
                with self._client(temp_dir) as client:
                    first = client.post(
                        "/api/media/upload",
                        files={"file": ("same.mp4", b"first", "video/mp4")},
                    ).json()
                    second = client.post(
                        "/api/media/upload",
                        files={"file": ("same.mp4", b"second", "video/mp4")},
                    ).json()
                    self.assertNotEqual(first["filename"], second["filename"])
                    self.assertEqual((Path(temp_dir) / first["filename"]).read_bytes(), b"first")
                    self.assertEqual((Path(temp_dir) / second["filename"]).read_bytes(), b"second")

    def test_empty_upload_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)), patch.object(
                media_utils.subprocess, "check_output", side_effect=Exception("no ffprobe")
            ):
                with self._client(temp_dir) as client:
                    response = client.post(
                        "/api/media/upload",
                        files={"file": ("empty.mp4", b"", "video/mp4")},
                    )
                    self.assertEqual(response.status_code, 400)

    @unittest.skipUnless(FFPROBE, "ffprobe not installed")
    def test_real_media_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(media, "UPLOAD_DIR", Path(temp_dir)):
                with self._client(temp_dir) as client:
                    expectations = {
                        ".mp4": ("video", 160, 120, True),
                        ".mp3": ("audio", 1920, 1080, True),
                        ".wav": ("audio", 1920, 1080, True),
                        ".png": ("image", 160, 120, False),
                        ".jpg": ("image", 160, 120, False),
                    }
                    for suffix, (kind, width, height, has_audio) in expectations.items():
                        sample = _make_sample(suffix, temp_dir)
                        if sample is None:
                            self.skipTest("ffmpeg could not generate sample media")
                        with self.subTest(suffix=suffix):
                            with open(sample, "rb") as fh:
                                response = client.post(
                                    "/api/media/upload",
                                    files={"file": (f"real{suffix}", fh.read(), "application/octet-stream")},
                                )
                            self.assertEqual(response.status_code, 200, response.text)
                            result = response.json()
                            self.assertEqual(result["kind"], kind)
                            self.assertGreater(result["duration"], 0)
                            self.assertEqual(result["width"], width)
                            self.assertEqual(result["height"], height)
                            self.assertEqual(result["has_audio"], has_audio)


class TestStandaloneMultipart(unittest.TestCase):
    """The zero-dependency fallback server must parse multipart bodies losslessly."""

    BOUNDARY = "----superaiBoundary"

    def _multipart(self, name, data, content_type="application/octet-stream"):
        header = (
            f'--{self.BOUNDARY}\r\n'
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        return header + data + b"\r\n" + f"--{self.BOUNDARY}--\r\n".encode()

    def test_parse_video_audio_image_payloads(self):
        cases = {
            "clip.mp4": (b"\x00\x00\x00\x18ftypmp42\xff\xd9", "video/mp4"),
            "song.mp3": (b"ID3\x04\x00\x00AUDIO", "audio/mpeg"),
            "photo.png": (b"\x89PNG\r\n\x1a\nDATA", "image/png"),
        }
        for name, (data, content_type) in cases.items():
            with self.subTest(name=name):
                body = self._multipart(name, data, content_type)
                parsed = media_utils.parse_multipart(
                    body, f"multipart/form-data; boundary={self.BOUNDARY}"
                )
                self.assertIsNotNone(parsed)
                filename, declared, payload = parsed
                self.assertEqual(filename, name)
                self.assertEqual(declared, content_type)
                self.assertEqual(payload, data)

    def test_parse_preserves_trailing_newlines(self):
        data = b"binary\r\n\r\n"
        body = self._multipart("clip.mp4", data, "video/mp4")
        parsed = media_utils.parse_multipart(
            body, f"multipart/form-data; boundary={self.BOUNDARY}"
        )
        self.assertEqual(parsed[2], data)

    def test_sanitize_filename_blocks_path_traversal(self):
        self.assertEqual(media_utils.sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(media_utils.sanitize_filename("my clip (1).mp4"), "my_clip_(1).mp4")
        self.assertTrue(media_utils.sanitize_filename(".."))


if __name__ == "__main__":
    unittest.main(verbosity=2)
