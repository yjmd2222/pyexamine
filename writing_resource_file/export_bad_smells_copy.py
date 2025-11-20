"""Export helper: copy canonical bad_smells_info.json into this folder.

This small helper copies the repository's canonical `bad_smells_info.json`
from the repository root into this `writing_resource_file/` directory so the
resource package contains the canonical JSON alongside the summary and
helper scripts.

Why this exists
- When packaging or sharing the smell metadata, it's convenient to have a
  self-contained `writing_resource_file` directory containing the final
  `bad_smells_info.json` alongside supporting scripts and documentation.

Usage
------
From the repository root run:

    python writing_resource_file/export_bad_smells_copy.py

This will copy the file `bad_smells_info.json` from the repo root into
`writing_resource_file/bad_smells_info.json`.

Behavior and safety
-------------------
- The script only performs a single file copy; it does not modify any other
  repository files.
- If the source JSON is not found, it prints a helpful message and exits.
- The file is copied using `shutil.copy2` so file metadata (timestamps)
  are preserved; this is convenient for packaging and provenance.
"""

from pathlib import Path
import shutil


# Directory containing this script: writing_resource_file/
THIS_DIR = Path(__file__).resolve().parent

# Repository root is the parent of writing_resource_file/
REPO_ROOT = THIS_DIR.parent

# Source path (expected at repository root)
SRC_JSON = REPO_ROOT / 'bad_smells_info.json'

# Destination path inside this resource folder
DST_JSON = THIS_DIR / 'bad_smells_info.json'


def main() -> int:
    """Copy the source JSON into the resource folder.

    Returns an exit code integer suitable for sys.exit.
    """
    if not SRC_JSON.exists():
        print('Source bad_smells_info.json not found at', SRC_JSON)
        return 1

    try:
        # copy2 preserves metadata (useful when packaging artifacts)
        shutil.copy2(SRC_JSON, DST_JSON)
        print('Copied', SRC_JSON, '->', DST_JSON)
        return 0
    except Exception as exc:
        print('Failed to copy file:', exc)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
