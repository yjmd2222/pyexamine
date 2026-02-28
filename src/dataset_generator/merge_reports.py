from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON list in {path}")
    return data


def merge_reports(base_report: str, extra_report: str, output_path: str):
    base_rows = _load_json(base_report)
    extra_rows = _load_json(extra_report)
    merged = list(base_rows) + list(extra_rows)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"base_rows": len(base_rows), "extra_rows": len(extra_rows), "merged_rows": len(merged), "output": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge two report JSON files.")
    parser.add_argument("--base-report", required=True, help="Primary report JSON path")
    parser.add_argument("--extra-report", required=True, help="Additional report JSON path")
    parser.add_argument("--output", required=True, help="Merged output JSON path")
    args = parser.parse_args()
    print(json.dumps(merge_reports(args.base_report, args.extra_report, args.output), indent=2))


if __name__ == "__main__":
    main()
