#!/usr/bin/env python3
"""离线验证：不访问网络、不读取真实凭据。"""
from contextlib import redirect_stdout, redirect_stderr
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import zlib
import api
import jobs
import payload
import rika
from common import ROOT, ClientError, resolve_key


def png(width, height):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (bytes((137, 80, 78, 71, 13, 10, 26, 10))
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes((width * 4 + 1) * height))) + chunk(b"IEND", b""))


class OfflineTests(unittest.TestCase):
    def test_blank_and_environment_key(self):
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"RIKA_API_KEY": ""}):
            config = Path(td) / "config.json"
            config.write_text(json.dumps({"api_key": ""}))
            with self.assertRaises(ClientError) as caught:
                resolve_key(config)
            self.assertEqual(caught.exception.code, 3)
            with patch.dict(os.environ, {"RIKA_API_KEY": "offline-test-value"}):
                self.assertEqual(resolve_key(config), "offline-test-value")

    def test_all_five_templates(self):
        with tempfile.TemporaryDirectory() as td:
            image = Path(td) / "input.png"
            image.write_bytes(png(256, 128))
            for kind, count in (("v1", 1), ("v2", 3), ("character", 0), ("item", 0), ("map", 1)):
                with self.subTest(kind=kind):
                    data = payload.build(kind, ROOT / f"examples/{kind}.json", [image] * count)
                    self.assertEqual(len(data["image_base64"]), count)

    def test_v2_rejects_wrong_reference_count_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            image = Path(td) / "input.png"
            image.write_bytes(png(256, 128))
            with self.assertRaises(ClientError):
                payload.build("v2", ROOT / "examples/v2.json", [image])
            image.write_bytes(png(128, 128))
            with self.assertRaises(ClientError):
                payload.build("v2", ROOT / "examples/v2.json", [image] * 3)

    def test_dry_run_never_reads_key_or_uses_network(self):
        with patch("rika.resolve_key", side_effect=AssertionError("read key")), patch("api.request", side_effect=AssertionError("network")), redirect_stdout(io.StringIO()):
            self.assertEqual(rika.main(["submit", "character", "--payload", str(ROOT / "examples/character.json"), "--dry-run"]), 0)

    def test_submit_not_retried_on_network_failure(self):
        with patch("api.urllib.request.build_opener") as build:
            build.return_value.open.side_effect = urllib.error.URLError("offline")
            with self.assertRaises(ClientError) as caught:
                api.request("POST", "/generate-character", "offline-test-value", {})
            self.assertEqual(caught.exception.code, 5)
            self.assertEqual(build.return_value.open.call_count, 1)

    def test_polling_and_timeout(self):
        with patch("api.request", side_effect=[{"status": "queued"}, {"status": "succeeded"}]), patch("jobs.time.sleep"):
            self.assertEqual(jobs.get_job("test-id", "offline", True)["status"], "succeeded")
        with patch("api.request", return_value={"status": "running"}), patch("jobs.time.monotonic", side_effect=[0, 1000]):
            with self.assertRaises(ClientError) as caught:
                jobs.get_job("test-id", "offline", True)
            self.assertEqual(caught.exception.code, 6)

    def test_download_without_key_and_without_overwrite(self):
        job = {"status": "succeeded", "output_images": [{"url": "https://cdn.rika-ai.com/test.png"}]}
        with tempfile.TemporaryDirectory() as td, patch("jobs.urllib.request.build_opener") as build:
            build.return_value.open.return_value = io.BytesIO(png(32, 32))
            files = jobs.download(job, "test-id", td)
            self.assertTrue(Path(files[0]).exists())
            req = build.return_value.open.call_args.args[0]
            self.assertFalse(any(k.lower() == "x-api-key" for k in req.headers))
            build.return_value.open.return_value = io.BytesIO(b"replacement")
            with self.assertRaises(FileExistsError):
                jobs.download(job, "test-id", td)
            self.assertEqual(Path(files[0]).read_bytes(), png(32, 32))
        with self.assertRaises(ClientError):
            jobs.check_url("http://example.com/file.png")

    def test_failed_job_exit_code(self):
        with patch("rika.resolve_key", return_value="offline"), patch("jobs.get_job", return_value={"status": "failed"}), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(rika.main(["job", "test-id"]), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
