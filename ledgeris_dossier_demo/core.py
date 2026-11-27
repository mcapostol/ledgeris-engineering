"""Deterministic, audience-scoped dossier archives using the standard library."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from typing import Iterable
import zipfile

SCHEMA = "ledgeris-dossier-demo/v1"
AUDIENCES = {"client", "internal"}
CLASSIFICATIONS = {"public", "internal"}
MAX_FILE_BYTES = 5 * 1024 * 1024
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


class DossierError(ValueError):
    """Raised when a dossier violates an integrity or disclosure invariant."""


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_member(name: str) -> PurePosixPath:
    member = PurePosixPath(name)
    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or member.is_absolute()
        or ".." in member.parts
        or "." in member.parts
    ):
        raise DossierError(f"unsafe archive path: {name!r}")
    return member


def _source_entries(source: Path) -> list[tuple[dict[str, object], bytes]]:
    if not source.is_dir():
        raise DossierError(f"source is not a directory: {source}")

    entries: list[tuple[dict[str, object], bytes]] = []
    for classification in sorted(CLASSIFICATIONS):
        root = source / classification
        if not root.exists():
            continue
        if root.is_symlink() or not root.is_dir():
            raise DossierError(f"invalid classification directory: {classification}")
        for path in sorted(root.rglob("*")):
            if path.is_dir():
                continue
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
                raise DossierError(f"source must be a regular file: {path.name}")
            relative = path.relative_to(root).as_posix()
            _safe_member(relative)
            content = path.read_bytes()
            if len(content) > MAX_FILE_BYTES:
                raise DossierError(f"source file exceeds {MAX_FILE_BYTES} bytes: {relative}")
            archive_path = f"documents/{classification}/{relative}"
            metadata: dict[str, object] = {
                "path": archive_path,
                "classification": classification,
                "size": len(content),
                "sha256": _sha256(content),
            }
            entries.append((metadata, content))
    if not entries:
        raise DossierError("source contains no dossier files")
    return entries


def _input_fingerprint(entries: Iterable[tuple[dict[str, object], bytes]]) -> str:
    canonical = [metadata for metadata, _content in entries]
    return _sha256(_json_bytes(canonical))


def _write_member(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, content)


def build_dossier(source: Path, output: Path, audience: str) -> dict[str, object]:
    """Build a deterministic dossier and return its manifest."""
    if audience not in AUDIENCES:
        raise DossierError(f"audience must be one of: {', '.join(sorted(AUDIENCES))}")

    all_entries = _source_entries(source)
    selected = [
        item
        for item in all_entries
        if audience == "internal" or item[0]["classification"] == "public"
    ]
    if not selected:
        raise DossierError(f"no files are eligible for the {audience} audience")

    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "audience": audience,
        "input_fingerprint": _input_fingerprint(all_entries),
        "files": [metadata for metadata, _content in selected],
    }
    manifest_bytes = _json_bytes(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for metadata, content in selected:
                _write_member(archive, str(metadata["path"]), content)
            _write_member(archive, "manifest.json", manifest_bytes)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return manifest


def verify_dossier(archive_path: Path) -> dict[str, object]:
    """Verify archive structure, audience policy, file sizes, and SHA-256 values."""
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise DossierError("archive contains duplicate paths")
            for name in names:
                _safe_member(name)
            if names.count("manifest.json") != 1:
                raise DossierError("archive must contain exactly one manifest.json")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("schema") != SCHEMA:
                raise DossierError("unsupported manifest schema")
            audience = manifest.get("audience")
            if audience not in AUDIENCES:
                raise DossierError("invalid manifest audience")
            fingerprint = manifest.get("input_fingerprint")
            if (
                not isinstance(fingerprint, str)
                or len(fingerprint) != 64
                or any(character not in "0123456789abcdef" for character in fingerprint)
            ):
                raise DossierError("invalid input fingerprint")
            files = manifest.get("files")
            if not isinstance(files, list) or not files:
                raise DossierError("manifest contains no files")

            expected_paths = {"manifest.json"}
            for entry in files:
                if not isinstance(entry, dict):
                    raise DossierError("invalid file entry")
                name = entry.get("path")
                classification = entry.get("classification")
                size = entry.get("size")
                digest = entry.get("sha256")
                if not isinstance(name, str):
                    raise DossierError("manifest path must be text")
                _safe_member(name)
                if classification not in CLASSIFICATIONS:
                    raise DossierError(f"invalid classification for {name}")
                if not name.startswith(f"documents/{classification}/"):
                    raise DossierError(f"path classification mismatch: {name}")
                if audience == "client" and classification != "public":
                    raise DossierError("client dossier contains internal material")
                if name in expected_paths:
                    raise DossierError(f"duplicate manifest entry: {name}")
                expected_paths.add(name)
                if (
                    not isinstance(size, int)
                    or size < 0
                    or not isinstance(digest, str)
                    or len(digest) != 64
                    or any(character not in "0123456789abcdef" for character in digest)
                ):
                    raise DossierError(f"invalid integrity metadata: {name}")
                content = archive.read(name)
                if len(content) != size or _sha256(content) != digest:
                    raise DossierError(f"integrity check failed: {name}")
            if set(names) != expected_paths:
                raise DossierError("archive and manifest paths differ")
            if archive.testzip() is not None:
                raise DossierError("ZIP CRC verification failed")
            return manifest
    except (OSError, zipfile.BadZipFile, KeyError, json.JSONDecodeError) as exc:
        if isinstance(exc, DossierError):
            raise
        raise DossierError(f"cannot verify dossier: {exc}") from exc
