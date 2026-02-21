import argparse
import os
import subprocess
import sys


def run_command(command, env):
    result = subprocess.run(command, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def _default_output_dir(code_path):
    candidate = os.path.abspath(code_path)
    if os.path.isfile(candidate) or candidate.endswith(".py"):
        candidate = os.path.dirname(candidate)
    base_name = os.path.basename(os.path.normpath(candidate))
    base_name = base_name or "code"
    return f"dataset_{base_name}"


def main():
    parser = argparse.ArgumentParser(
        description="Run code quality analysis and generate datasets (CoNLL or DETR-style)."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    parser.add_argument("--report", default="code_quality_report.json",
                        help="Output path for code_quality_report.json")
    parser.add_argument("--metadata-output", default=None,
                        help="Output path for code_metadata.json")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for generated dataset artifacts")
    parser.add_argument("--format", default="conll", choices=["conll", "detr", "detr_candidates"],
                        help="Dataset format to generate: conll (per-smell token labels), detr (thresholded set-of-Evidences JSON), or detr_candidates (detected+undetected candidates).")
    args = parser.parse_args()

    output_dir = args.output_dir or _default_output_dir(args.code_path)
    report_dir = os.path.dirname(os.path.abspath(args.report))
    if report_dir:
        os.makedirs(report_dir, exist_ok=True)

    env = os.environ.copy()
    pyexamine_src = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [env.get("PYTHONPATH"), pyexamine_src])
    )

    analyze_cmd = [
        sys.executable, "-m", "code_quality_analyzer.main",
        args.code_path, "--config", args.config, "--output", args.report
    ]
    if args.metadata_output:
        analyze_cmd.extend(["--metadata-output", args.metadata_output])
    run_command(analyze_cmd, env)


    if args.format == "conll":
        dataset_cmd = [
            sys.executable, "-m", "dataset_generator",
            args.code_path,
            "--report", args.report,
            "--output-dir", output_dir
        ]
        run_command(dataset_cmd, env)
    elif args.format == "detr":
        # Single JSON artifact per analyzed code_path
        detr_output = os.path.join(output_dir, "detr_dataset.json")
        os.makedirs(output_dir, exist_ok=True)
        dataset_cmd = [
            sys.executable, "-m", "dataset_generator.build_detr_dataset",
            args.code_path,
            "--report", args.report,
            "--output", detr_output
        ]
        run_command(dataset_cmd, env)
    else:
        detr_output = os.path.join(output_dir, "detr_candidates.json")
        os.makedirs(output_dir, exist_ok=True)
        dataset_cmd = [
            sys.executable, "-m", "dataset_generator.build_detr_candidates",
            args.code_path,
            "--config", args.config,
            "--output", detr_output,
        ]
        run_command(dataset_cmd, env)


if __name__ == "__main__":
    main()
