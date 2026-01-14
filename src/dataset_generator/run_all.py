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
        description="Run code quality analysis and generate per-smell CoNLL datasets."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    parser.add_argument("--report", default="code_quality_report.json",
                        help="Output path for code_quality_report.json")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for per-smell CoNLL files")
    args = parser.parse_args()

    output_dir = args.output_dir or _default_output_dir(args.code_path)

    env = os.environ.copy()
    pyexamine_src = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [env.get("PYTHONPATH"), pyexamine_src])
    )

    analyze_cmd = [
        sys.executable, "-m", "code_quality_analyzer.main",
        args.code_path, "--config", args.config, "--output", args.report
    ]
    run_command(analyze_cmd, env)

    dataset_cmd = [
        sys.executable, "-m", "dataset_generator",
        args.code_path,
        "--report", args.report,
        "--output-dir", output_dir
    ]
    run_command(dataset_cmd, env)


if __name__ == "__main__":
    main()
