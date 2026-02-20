import argparse
import json
import os
import tempfile
from typing import Any, Dict, Set

import yaml

from code_quality_analyzer.main import (
    analyze_architectural_smells_only,
    analyze_code_smells_only,
    analyze_project,
    analyze_structural_smells_only,
)
from dataset_generator.build_detr_dataset import build_detr_dataset


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping at {path}")
    return data


def _dump_yaml(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def _relax_threshold_value(key: str, value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        upper = key.upper()
        is_int = isinstance(value, int) and not isinstance(value, bool)
        tiny = 1 if is_int else 1e-9
        huge = 10**9 if is_int else 1e9

        # Explicit "max allowed delegate targets" style keys should stay permissive high.
        if "MAX_DELEGATE_TARGETS" in upper:
            return huge
        if "MAX" in upper or "BOUND_HIGH" in upper:
            return huge
        if "MULTIPLIER_HIGH" in upper:
            return 10**6 if is_int else 1e6
        if "MULTIPLIER_LOW" in upper:
            return tiny
        if (
            "MIN" in upper
            or "THRESHOLD" in upper
            or "RATIO" in upper
            or "BOUND_LOW" in upper
            or "BREAKPOINT" in upper
        ):
            return tiny
        return tiny
    return value


def _relax_thresholds(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _relax_thresholds(_relax_threshold_value(k, v)) for k, v in node.items()}
    if isinstance(node, list):
        return [_relax_thresholds(v) for v in node]
    return node


def _signature(entry: Dict[str, Any]) -> str:
    payload = {
        "smell_name": entry.get("smell_name"),
        "anchor": entry.get("anchor"),
        "mentions": entry.get("mentions", []),
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _run_analysis(
    code_path: str,
    config_path: str,
    output_report: str,
    smell_type: str = None,
) -> None:
    # Reuse existing analyzer entrypoints directly.
    if smell_type == "code":
        analyze_code_smells_only(code_path, config_path=config_path, output=output_report)
    elif smell_type == "architectural":
        analyze_architectural_smells_only(code_path, config_path=config_path, output=output_report)
    elif smell_type == "structural":
        analyze_structural_smells_only(code_path, config_path=config_path, output=output_report)
    else:
        # analyze_project uses argparse; invoke through module-like defaults by emulating argv
        import sys

        argv_backup = sys.argv
        try:
            sys.argv = [
                "code_quality_analyzer.main",
                code_path,
                "--config",
                config_path,
                "--output",
                output_report,
            ]
            analyze_project()
        finally:
            sys.argv = argv_backup


def build_detr_candidates(
    code_path: str,
    config_path: str,
    output_path: str,
    smell_type: str = None,
    keep_intermediate: bool = False,
    intermediate_dir: str = None,
) -> Dict[str, Any]:
    if intermediate_dir:
        os.makedirs(intermediate_dir, exist_ok=True)
        work_dir_ctx = None
        work_dir = intermediate_dir
    else:
        work_dir_ctx = tempfile.TemporaryDirectory(prefix="pyexamine_detr_candidates_")
        work_dir = work_dir_ctx.name

    detected_report = os.path.join(work_dir, "detected_report.json")
    candidate_report = os.path.join(work_dir, "candidate_report.json")
    relaxed_config = os.path.join(work_dir, "relaxed_config.yaml")
    detected_detr = os.path.join(work_dir, "detected_detr.json")
    candidate_detr = os.path.join(work_dir, "candidate_detr.json")

    base_cfg = _load_yaml(config_path)
    relaxed_cfg = _relax_thresholds(base_cfg)
    _dump_yaml(relaxed_config, relaxed_cfg)

    _run_analysis(code_path, config_path, detected_report, smell_type=smell_type)
    _run_analysis(code_path, relaxed_config, candidate_report, smell_type=smell_type)

    detected_obj = build_detr_dataset(code_path, detected_report, detected_detr)
    candidate_obj = build_detr_dataset(code_path, candidate_report, candidate_detr)

    detected_signatures: Set[str] = {_signature(e) for e in detected_obj.get("Evidences", [])}
    detected_count = 0
    for ev in candidate_obj.get("Evidences", []):
        is_detected = _signature(ev) in detected_signatures
        ev["is_detected"] = is_detected
        if is_detected:
            detected_count += 1

    total = len(candidate_obj.get("Evidences", []))
    schema = candidate_obj.setdefault("schema", {})
    schema["candidate_mode"] = True
    schema["detected_count"] = detected_count
    schema["undetected_count"] = max(0, total - detected_count)
    schema["detected_report_path"] = os.path.abspath(detected_report) if keep_intermediate else None
    schema["candidate_report_path"] = os.path.abspath(candidate_report) if keep_intermediate else None

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(candidate_obj, f, ensure_ascii=False, indent=2)

    schema_path = os.path.splitext(output_path)[0] + ".schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)

    if not keep_intermediate:
        try:
            os.remove(detected_report)
            os.remove(candidate_report)
            os.remove(relaxed_config)
            os.remove(detected_detr)
            os.remove(os.path.splitext(detected_detr)[0] + ".schema.json")
            os.remove(candidate_detr)
            os.remove(os.path.splitext(candidate_detr)[0] + ".schema.json")
        except OSError:
            pass

    if work_dir_ctx is not None:
        work_dir_ctx.cleanup()

    return candidate_obj


def _default_output_path(code_path: str) -> str:
    candidate = os.path.abspath(code_path)
    if os.path.isfile(candidate) or candidate.endswith(".py"):
        candidate = os.path.dirname(candidate)
    base_name = os.path.basename(os.path.normpath(candidate)) or "code"
    outdir = f"dataset_{base_name}"
    return os.path.join(outdir, "detr_candidates.json")


def main():
    parser = argparse.ArgumentParser(
        description="Build a DETR-style candidate dataset (detected + undetected) independent from thresholded report generation."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    parser.add_argument("--output", default=None, help="Output JSON path (default: dataset_<code>/detr_candidates.json)")
    parser.add_argument("--type", choices=["code", "architectural", "structural"], default=None,
                        help="Restrict analysis to a smell category (default: all).")
    parser.add_argument("--keep-intermediate", action="store_true",
                        help="Keep detected/candidate intermediate reports and DETR files.")
    parser.add_argument("--intermediate-dir", default=None,
                        help="Directory to place intermediate artifacts (implies persisted workspace).")
    args = parser.parse_args()

    output_path = args.output or _default_output_path(args.code_path)
    build_detr_candidates(
        code_path=args.code_path,
        config_path=args.config,
        output_path=output_path,
        smell_type=args.type,
        keep_intermediate=args.keep_intermediate,
        intermediate_dir=args.intermediate_dir,
    )


if __name__ == "__main__":
    main()
