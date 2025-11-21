#!/usr/bin/env python3
"""
Remove `detection.module` keys from the repository's `bad_smells_info.json`.

Creates a backup at `bad_smells_info.json.bak.remove_module_key` before writing.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "bad_smells_info.json"
BACKUP_PATH = ROOT / "bad_smells_info.json.bak.remove_module_key"

if not JSON_PATH.exists():
    print(f"Error: {JSON_PATH} not found.")
    raise SystemExit(1)

shutil.copy2(JSON_PATH, BACKUP_PATH)

with JSON_PATH.open("r", encoding="utf-8") as f:
    data = json.load(f)

changed = False
for metric in data.get("metrics", []):
    detection = metric.get("detection")
    if isinstance(detection, dict) and "module" in detection:
        del detection["module"]
        changed = True

if changed:
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Removed 'module' keys and saved backup to: {BACKUP_PATH}")
else:
    print("No 'module' keys found; nothing changed.")
