import argparse
import json
import os
import tempfile
from typing import Any, Dict, Optional, Set

import yaml

from code_quality_analyzer.main import (
    analyze_architectural_smells_only,
    analyze_code_smells_only,
    analyze_project,
    analyze_structural_smells_only,
)
from dataset_generator.build_detr_dataset import (
    _build_merged_prompt,
    _collect_mentions_for_entry,
    build_detr_dataset,
)
from dataset_generator.build_dataset import _iter_code_files


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

        # Keep metric-shaping knobs intact; they are not threshold gates.
        if (
            "WEIGHT" in upper
            or "MULTIPLIER" in upper
            or "BREAKPOINT" in upper
            or "BOUND_" in upper
        ):
            return value

        # Upper-bound gates used as reject filters in a few smells.
        if upper in {
            "LAZY_CLASS_METHODS",
            "LAZY_CLASS_LINES",
            "MIDDLE_MAN_MAX_DELEGATE_TARGETS",
            "HUB_BALANCE_RATIO_MAX",
            "MAX_CYCLE_SIZE",
        }:
            return huge

        # Most MAX/MIN/THRESHOLD/RATIO/COUNT/LINES keys are gate thresholds.
        # For candidate mode we make them permissive so threshold checks don't filter out.
        if (
            upper.startswith("MAX_")
            or upper.startswith("MIN_")
            or "THRESHOLD" in upper
            or "RATIO" in upper
            or "COUNT" in upper
            or upper.endswith("_LINES")
            or upper.endswith("_METHODS")
            or upper.endswith("_CALLS")
            or upper.endswith("_FUNCTIONS")
            or upper.endswith("_SIZE")
            or upper.endswith("_OCCURRENCES")
            or upper.endswith("_ARGS")
            or upper.endswith("_DEPENDENCIES")
        ):
            return tiny
        return tiny
    return value


def _relax_thresholds(node: Any) -> Any:
    if isinstance(node, dict):
        relaxed: Dict[str, Any] = {}
        for k, v in node.items():
            # Config shape is typically THRESHOLD_KEY -> {value: <num>, explanation: ...}.
            # Apply relaxation against THRESHOLD_KEY, not the nested "value" key.
            if isinstance(v, dict) and "value" in v:
                vv: Dict[str, Any] = {}
                for kk, vv_raw in v.items():
                    if kk == "value":
                        vv[kk] = _relax_threshold_value(k, vv_raw)
                    else:
                        vv[kk] = _relax_thresholds(vv_raw)
                relaxed[k] = vv
            else:
                relaxed[k] = _relax_thresholds(_relax_threshold_value(k, v))
        return relaxed
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


def _detected_signatures_from_report(code_path: str, report_path: str) -> Set[str]:
    code_root_abs = os.path.abspath(code_path)
    all_files = sorted(_iter_code_files(code_root_abs))
    _, _, file_by_abs = _build_merged_prompt(code_root_abs, all_files)
    ast_cache: Dict[str, Dict[str, Any]] = {}
    with open(report_path, "r", encoding="utf-8") as f:
        report_entries = json.load(f)

    detected_signatures: Set[str] = set()
    for entry in report_entries:
        if not isinstance(entry, dict):
            continue
        smell_name = entry.get("name") or entry.get("Name")
        if not smell_name:
            continue
        anchor, mentions = _collect_mentions_for_entry(entry, code_root_abs, all_files, file_by_abs, ast_cache)
        detected_signatures.add(
            _signature({"smell_name": smell_name, "anchor": anchor, "mentions": mentions or []})
        )
    return detected_signatures


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
    output_path: Optional[str] = None,
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

    base_cfg = _load_yaml(config_path)
    relaxed_cfg = _relax_thresholds(base_cfg)
    _dump_yaml(relaxed_config, relaxed_cfg)

    _run_analysis(code_path, config_path, detected_report, smell_type=smell_type)
    _run_analysis(code_path, relaxed_config, candidate_report, smell_type=smell_type)

    # Single DETR export branch: build candidates once, then annotate is_detected in-place.
    candidate_obj = build_detr_dataset(code_path, candidate_report, output_path=output_path)
    detected_signatures: Set[str] = _detected_signatures_from_report(code_path, detected_report)

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
    if keep_intermediate:
        schema["detected_report_path"] = os.path.abspath(detected_report)
        schema["candidate_report_path"] = os.path.abspath(candidate_report)
    else:
        schema.pop("detected_report_path", None)
        schema.pop("candidate_report_path", None)

    # Rewrite output after adding is_detected and schema counters.
    if output_path:
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
