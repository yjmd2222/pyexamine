#!/usr/bin/env python3
"""
Populate `guidance.definition` from `detection.summary` when the current
definition is a placeholder (e.g., contains 'see').

Creates a backup `bad_smells_info.json.bak.definition_from_summary` before writing.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "bad_smells_info.json"
BACKUP_PATH = ROOT / "bad_smells_info.json.bak.definition_from_summary"

if not JSON_PATH.exists():
    print(f"Error: {JSON_PATH} not found.")
    raise SystemExit(1)

shutil.copy2(JSON_PATH, BACKUP_PATH)

with JSON_PATH.open("r", encoding="utf-8") as f:
    data = json.load(f)

updated = []

for metric in data.get("metrics", []):
    guidance = metric.get("guidance") or {}
    cur_def = guidance.get("definition", "")
    # Only replace placeholder definitions that reference 'see'
    if isinstance(cur_def, str) and "see" in cur_def.lower():
        summary = metric.get("detection", {}).get("summary", "") or ""
        new_def = None

        # Try to extract 'Definition:' section from summary by splitting on blank lines
        parts = [p.strip() for p in summary.split("\n\n") if p.strip()]
        for part in parts:
            low = part.lower()
            if low.startswith("definition:"):
                new_def = part[len("definition:"):].strip()
                break

        # If no Definition found, fall back to a short heuristic definition using the metric name
        if not new_def or new_def.lower().startswith("see"):
            name = metric.get("name", "").strip()
            if name:
                new_def = f"{name}: A code quality issue identified by the detector that indicates {name.lower()}."
            else:
                new_def = "No concise definition available."

        # Ensure we don't keep any 'see' references
        if isinstance(new_def, str):
            new_def = new_def.replace("see detector summary", "").replace("see summary", "").strip()
        guidance["definition"] = new_def
        metric["guidance"] = guidance
        updated.append(metric.get("name"))

if updated:
    with JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated definitions for {len(updated)} metrics. Backup at: {BACKUP_PATH}")
    for name in updated:
        print(f" - {name}")
else:
    print("No placeholder definitions found; no changes made.")
