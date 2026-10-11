"""Validate and publish an ANKA design archive without exposing local usernames."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path.home() / "Documents" / "ANKA_Overnight" / "ANKA_TOOLCHAIN_DEMO_20261011"
ASSET_DIR = ROOT / "docs" / "visual_archive"
MANIFEST = ASSET_DIR / "MANIFEST.json"
LOCAL_ZIP = Path.home() / "Documents" / "ANKA_Finans_Gorsel_Arsivi_20261011.zip"
REPO_ZIP = ROOT / "docs" / LOCAL_ZIP.name

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
assert manifest["unique_images"] == 7
assert manifest["total_source_image_files"] == 10
for record in manifest["sources"]:
    path = record["source"]
    if "ANKA_Overnight" in path and ":" in path:
        path = path.split("ANKA_Overnight", 1)[1].lstrip("\\/").replace("\\", "/")
    record["source"] = path
    assert ":" not in path and "Users" not in path, "Unexpected machine-specific path"
for record in manifest["files"]:
    content = (ASSET_DIR / record["file"]).read_bytes()
    assert hashlib.sha256(content).hexdigest() == record["sha256"], record["file"]
MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
temporary = LOCAL_ZIP.with_name(LOCAL_ZIP.name + ".tmp")
with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as z:
    for file in sorted(ASSET_DIR.iterdir()):
        z.write(file, "ANKA_Finans_Gorseller/" + file.name)
with zipfile.ZipFile(temporary) as z:
    assert z.testzip() is None
temporary.replace(LOCAL_ZIP)
shutil.copy2(LOCAL_ZIP, REPO_ZIP)
assert hashlib.sha256(LOCAL_ZIP.read_bytes()).digest() == hashlib.sha256(REPO_ZIP.read_bytes()).digest()
print("MANIFEST_REDACTED=PASS")
print("ALL_SHA256_MATCH=PASS")
print("IMAGES_UNIQUE=7")
print("LOCAL_ZIP="+str(LOCAL_ZIP))
print("GITHUB_ZIP="+str(REPO_ZIP))
print("ZIP_SHA256="+hashlib.sha256(REPO_ZIP.read_bytes()).hexdigest())
print("ARCHIVE_FINAL=PASS")
