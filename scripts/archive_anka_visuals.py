"""Archive all accessible ANKA Finans image outputs with SHA-256 provenance.

Read-only with respect to source images and the user's primary project. Saves
distinct images into a versionable asset index, with each duplicate linked to
the same SHA-256. This does not claim inaccessible chat-generated images.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import zipfile

ROOT = Path.home() / "Documents" / "ANKA_Overnight"
PROJECT = ROOT / "ANKA_TOOLCHAIN_DEMO_20261011"
ARCHIVE = PROJECT / "docs" / "visual_archive"
ZIP = Path.home() / "Documents" / "ANKA_Finans_Gorsel_Arsivi_20261011.zip"
SOURCES = (
    ("ilk_terminal", ROOT / "ANKA_FINANS_RELEASE_CANDIDATE_20261011" / "docs" / "previews"),
    ("profesyonel", ROOT / "ANKA_TERMINAL_PRO_20261011" / "docs" / "previews"),
    ("gercek_araclar", PROJECT / "docs" / "previews"),
)

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dimensions(path: Path):
    if path.suffix.lower() == ".png":
        with path.open("rb") as stream:
            data = stream.read(24)
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return list(struct.unpack(">II", data[16:24]))
    return None

if ARCHIVE.exists():
    raise SystemExit("BLOCKED_ARCHIVE_ALREADY_EXISTS")
ARCHIVE.mkdir(parents=True)
unique = {}
source_records = []
for section, folder in SOURCES:
    if not folder.is_dir():
        continue
    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        fingerprint = digest(f)
        if fingerprint not in unique:
            dest_name = f"{section}__{f.name}"
            dst = ARCHIVE / dest_name
            shutil.copy2(f, dst)
            if digest(dst) != fingerprint:
                raise RuntimeError("COPY_HASH_MISMATCH:" + f.name)
            unique[fingerprint] = {
                "file": dest_name,
                "sha256": fingerprint,
                "bytes": f.stat().st_size,
                "dimensions": dimensions(f),
            }
        source_records.append({
            "source": f.relative_to(ROOT).as_posix(),
            "sha256": fingerprint,
            "archive_file": unique[fingerprint]["file"],
        })
manifest = {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "ANKA Finans created UI screenshot inventory and provenance",
    "limitations": [
        "Includes actual image files available on the user's Windows ANKA project; not invisible chat-only generated images.",
        "Historical AI concept images without accessible source bytes cannot be asserted to be archived.",
        "All market data in saved terminal screenshots is synthetic, not live.",
    ],
    "total_source_image_files": len(source_records),
    "unique_images": len(unique),
    "files": list(unique.values()),
    "sources": source_records,
}
(ARCHIVE / "MANIFEST.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for f in sorted(ARCHIVE.iterdir()):
        archive.write(f, arcname="ANKA_Finans_Gorseller/" + f.name)
with zipfile.ZipFile(ZIP) as archive:
    failures = archive.testzip()
if failures:
    raise RuntimeError("ZIP_INTEGRITY_FAIL:" + failures)
print("SOURCE_IMAGE_FILES=" + str(len(source_records)))
print("UNIQUE_ARCHIVED_IMAGES=" + str(len(unique)))
print("MANIFEST=" + str(ARCHIVE / "MANIFEST.json"))
print("ZIP=" + str(ZIP))
print("ZIP_BYTES=" + str(ZIP.stat().st_size))
print("ZIP_SHA256=" + digest(ZIP))
print("ARCHIVE_VERIFY=PASS")
