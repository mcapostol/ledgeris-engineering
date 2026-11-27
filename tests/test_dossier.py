from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from ledgeris_dossier_demo import DossierError, build_dossier, verify_dossier


FIXTURE = Path(__file__).parents[1] / "fixtures" / "monthly-close"


class DossierTests(unittest.TestCase):
    def test_client_archive_excludes_internal_working_papers(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "client.zip"
            manifest = build_dossier(FIXTURE, target, "client")
            self.assertTrue(all(item["classification"] == "public" for item in manifest["files"]))
            with zipfile.ZipFile(target) as archive:
                self.assertFalse(any("review-notes" in name for name in archive.namelist()))
            self.assertEqual(verify_dossier(target)["audience"], "client")

    def test_internal_archive_contains_both_scopes(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "internal.zip"
            manifest = build_dossier(FIXTURE, target, "internal")
            self.assertEqual({item["classification"] for item in manifest["files"]}, {"public", "internal"})
            self.assertEqual(verify_dossier(target)["input_fingerprint"], manifest["input_fingerprint"])

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.zip"
            second = Path(temporary) / "second.zip"
            build_dossier(FIXTURE, first, "client")
            build_dossier(FIXTURE, second, "client")
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_tampered_document_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            original = Path(temporary) / "original.zip"
            tampered = Path(temporary) / "tampered.zip"
            build_dossier(FIXTURE, original, "client")
            with zipfile.ZipFile(original) as source, zipfile.ZipFile(tampered, "w") as target:
                for info in source.infolist():
                    content = source.read(info.filename)
                    if info.filename.endswith("summary.csv"):
                        content += b"changed,true\n"
                    target.writestr(info, content)
            with self.assertRaisesRegex(DossierError, "integrity check failed"):
                verify_dossier(tampered)

    def test_client_manifest_cannot_relabel_internal_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "internal.zip"
            malformed = Path(temporary) / "malformed.zip"
            build_dossier(FIXTURE, source, "internal")
            with zipfile.ZipFile(source) as incoming, zipfile.ZipFile(malformed, "w") as outgoing:
                for info in incoming.infolist():
                    content = incoming.read(info.filename)
                    if info.filename == "manifest.json":
                        manifest = json.loads(content)
                        manifest["audience"] = "client"
                        content = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
                    outgoing.writestr(info, content)
            with self.assertRaisesRegex(DossierError, "client dossier contains internal material"):
                verify_dossier(malformed)


if __name__ == "__main__":
    unittest.main()
