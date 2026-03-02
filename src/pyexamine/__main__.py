import argparse
import os
import subprocess
import sys


def _with_pythonpath(env):
    pyexamine_src = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [env.get("PYTHONPATH"), pyexamine_src])
    )
    return env


def _run(command):
    result = subprocess.run(command, env=_with_pythonpath(os.environ.copy()), check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    parser = argparse.ArgumentParser(prog="pyexamine", description="PyExamine command line interface.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze code quality and produce a report."
    )
    analyze_parser.add_argument("code_path", help="Path to a code file or directory to include.")
    analyze_parser.add_argument("--config", default="code_quality_config.yaml",
                                help="Path to the configuration file")
    analyze_parser.add_argument("--output", help="Path to the output report (.json/.csv/.txt)")
    analyze_parser.add_argument("--type", choices=["code", "architectural", "structural"],
                                help="Type of smell to analyze (default: all)")
    analyze_parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    dataset_parser = subparsers.add_parser(
        "smell_dataset",
        help="Analyze code quality and generate per-smell CoNLL datasets."
    )
    dataset_parser.add_argument("code_path", help="Path to a code file or directory to include.")
    dataset_parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    dataset_parser.add_argument("--report", default="code_quality_report.json",
                                help="Output path for code_quality_report.json")
    dataset_parser.add_argument("--metadata-output", default=None,
                                help="Output path for code_metadata.json")
    dataset_parser.add_argument("--output-dir", default=None,
                                help="Output directory for per-smell CoNLL files")

    index_parser = subparsers.add_parser(
        "build_smell_index",
        help="Build a bidirectional smell index from report files."
    )
    index_parser.add_argument("code_path", help="Path to a code file or directory to include.")
    index_parser.add_argument("--config", required=True, help="Path to code quality config YAML")
    index_parser.add_argument("--report", default="code_quality_report.json",
                              help="Path to code_quality_report.json or a directory of reports.")
    index_parser.add_argument("--output", default=None,
                              help="Output path for smell_index.json")
    index_parser.add_argument("--no-analyze", action="store_true",
                              help="Skip running analyze_code_quality before building the index.")

    role_excerpt_parser = subparsers.add_parser(
        "build_role_section_excerpts",
        help="Build line-level ROLE0/ROLE1/ROLE2 packed excerpt CoNLL."
    )
    role_excerpt_parser.add_argument("code_path", help="Path to a code file or directory to include.")
    role_excerpt_parser.add_argument("--report", required=True, help="Path to code_quality_report.json")
    role_excerpt_parser.add_argument("--templates", required=True,
                                     help="Path to templates_with_roles.json")
    role_excerpt_parser.add_argument("--output-conll", default="role_section_excerpts.line.conll",
                                     help="Output path for excerpt CoNLL")
    role_excerpt_parser.add_argument("--context-lines", type=int, default=2,
                                     help="Context lines to include around each role span")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd = [
            sys.executable, "-m", "code_quality_analyzer.main",
            args.code_path,
            "--config", args.config
        ]
        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            cmd.extend(["--output", args.output])
        if args.type:
            cmd.extend(["--type", args.type])
        if args.debug:
            cmd.append("--debug")
        _run(cmd)
        return

    if args.command == "smell_dataset":
        cmd = [
            sys.executable, "-m", "dataset_generator.run_all",
            args.code_path,
            "--config", args.config,
            "--report", args.report,
        ]
        if args.metadata_output:
            cmd.extend(["--metadata-output", args.metadata_output])
        if args.output_dir:
            cmd.extend(["--output-dir", args.output_dir])
        _run(cmd)
        return

    if args.command == "build_smell_index":
        cmd = [
            sys.executable, "-m", "dataset_generator.build_smell_index",
            args.code_path,
            "--config", args.config,
            "--report", args.report,
        ]
        if args.no_analyze:
            cmd.append("--no-analyze")
        if args.output:
            cmd.extend(["--output", args.output])
        _run(cmd)
        return

    if args.command == "build_role_section_excerpts":
        cmd = [
            sys.executable, "-m", "dataset_generator.build_role_section_excerpts",
            args.code_path,
            "--report", args.report,
            "--templates", args.templates,
            "--output-conll", args.output_conll,
            "--context-lines", str(args.context_lines),
        ]
        _run(cmd)
        return


if __name__ == "__main__":
    main()
