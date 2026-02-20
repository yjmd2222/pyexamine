import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


_SRC_ROOT = Path(__file__).resolve().parents[2]
_PYEXAMINE_ROOT = _SRC_ROOT.parent
_DEFAULT_OUTPUT = _PYEXAMINE_ROOT / "samples" / "smell_index.json"


def _run_analyzer(code_path, config_path, report_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [env.get("PYTHONPATH"), str(_SRC_ROOT)]))
    command = [
        sys.executable,
        "-m",
        "code_quality_analyzer.main",
        code_path,
        "--config",
        config_path,
        "--output",
        report_path,
    ]
    result = subprocess.run(command, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _load_report(report_path):
    report_path = Path(report_path)
    if report_path.is_dir():
        entries = []
        for path in sorted(report_path.glob("*.json")):
            with open(path, "r", encoding="utf-8") as handle:
                entries.extend(json.load(handle))
        return entries
    with open(report_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _get_value(entry, *keys):
    for key in keys:
        if key in entry:
            return entry[key]
        if isinstance(key, str):
            k1 = key.replace("/", "_")
            if k1 in entry:
                return entry[k1]
            k2 = key.replace("_", "/")
            if k2 in entry:
                return entry[k2]
    return None


def _normalize_type(value):
    if not value:
        return ""
    return str(value).strip().lower()


def _normalize_path(file_path, base_dir):
    if not file_path:
        return ""
    try:
        candidate = Path(file_path).resolve()
    except Exception:
        candidate = Path(file_path)
    base_dir = Path(base_dir).resolve()
    try:
        common_root = Path(os.path.commonpath([base_dir, candidate]))
    except ValueError:
        common_root = None
    if common_root and common_root == base_dir:
        return candidate.relative_to(base_dir).as_posix()
    return str(file_path)


def _build_index(report_entries, code_root):
    all_smells = sorted({
        _get_value(entry, "name", "Name")
        for entry in report_entries
        if _get_value(entry, "name", "Name")
    })
    smell_set = set(all_smells)
    samples_root = Path(code_root).resolve()
    if samples_root.is_file() or samples_root.suffix == ".py":
        samples_root = samples_root.parent

    file_to_smells = {}
    for entry in report_entries:
        file_path = _get_value(entry, "file_path", "File")
        smell_name = _get_value(entry, "name", "Name")
        if not file_path or not smell_name:
            continue
        normalized_path = _normalize_path(file_path, samples_root)
        if not normalized_path:
            continue
        bucket = file_to_smells.setdefault(normalized_path, {"positive": set(), "negative": set()})
        bucket["positive"].add(smell_name)

    for file_path, bucket in file_to_smells.items():
        bucket["negative"] = smell_set - bucket["positive"]

    smell_to_files = {smell: {"positive": set(), "negative": set()} for smell in all_smells}
    for file_path, bucket in file_to_smells.items():
        for smell in bucket["positive"]:
            smell_to_files[smell]["positive"].add(file_path)
        for smell in bucket["negative"]:
            smell_to_files[smell]["negative"].add(file_path)

    file_to_smells = {
        path: {
            "positive": sorted(bucket["positive"]),
            "negative": sorted(bucket["negative"]),
        }
        for path, bucket in sorted(file_to_smells.items())
    }
    smell_to_files = {
        smell: {
            "positive": sorted(bucket["positive"]),
            "negative": sorted(bucket["negative"]),
        }
        for smell, bucket in sorted(smell_to_files.items())
    }

    return {
        "file_to_smells": file_to_smells,
        "smell_to_files": smell_to_files,
    }


def build_smell_index(code_path, config_path, report_path, output_path, run_analysis):
    if run_analysis:
        _run_analyzer(code_path, config_path, report_path)
    report_entries = _load_report(report_path)
    index = _build_index(report_entries, code_path)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Build a bidirectional smell index from a report.")
    parser.add_argument("code_path", help="Path to a code file or directory to analyze.")
    parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    parser.add_argument("--report", default="code_quality_report.json",
                        help="Path to code_quality_report.json (used or regenerated).")
    parser.add_argument("--output", default=str(_DEFAULT_OUTPUT),
                        help="Output path for smell_index.json")
    parser.add_argument("--no-analyze", action="store_true",
                        help="Skip running analyze_code_quality before building the index.")
    args = parser.parse_args()

    build_smell_index(
        args.code_path,
        args.config,
        args.report,
        args.output,
        run_analysis=not args.no_analyze,
    )


if __name__ == "__main__":
    main()


