import argparse
import os
import subprocess
import sys


def run_command(command, env):
    result = subprocess.run(command, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Run code quality analysis and generate per-smell CoNLL datasets."
    )
    parser.add_argument("code_path", help="Path to a code file or directory to include.")
    parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    parser.add_argument("--report", default="code_quality_report.json",
                        help="Output path for code_quality_report.json")
    parser.add_argument("--labels", default="master-thesis-materials/data/labels.json",
                        help="Path to labels.json")
    parser.add_argument("--output-dir", default="dataset_conll",
                        help="Output directory for per-smell CoNLL files")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [env.get("PYTHONPATH"), "master-thesis-materials/pyexamine/src"])
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
        "--labels", args.labels,
        "--output-dir", args.output_dir
    ]
    run_command(dataset_cmd, env)


if __name__ == "__main__":
    main()
