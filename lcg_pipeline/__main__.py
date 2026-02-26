"""CLI entry point: python -m lcg_pipeline <command> [options]"""

import argparse
import sys
from pathlib import Path

from . import scaffold


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lcg_pipeline",
        description="LCG project and task directory scaffolding",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- build command ---------------------------------------------------
    build_p = sub.add_parser(
        "build",
        help="Scaffold a project or task directory",
    )
    build_p.add_argument(
        "type",
        choices=["base", "task"],
        help=(
            "'base' = top-level project structure (01–07 folders); "
            "'task' = technical task structure + lcg.toml config"
        ),
    )
    build_p.add_argument(
        "--dir",
        default=".",
        metavar="PATH",
        help="Target directory (default: current directory)",
    )
    build_p.add_argument(
        "--project",
        metavar="NAME",
        help="Exact name of the project root folder (required for task build)",
    )
    build_p.add_argument(
        "--task",
        metavar="NAME",
        help="Exact name of this task folder (default: the target directory name)",
    )

    args = parser.parse_args()
    root = Path(args.dir).resolve()

    if args.command == "build":
        if args.type == "base":
            scaffold.build_base(root)
        else:
            project = args.project or _prompt(
                "Project folder name (e.g. '01 25NEM Water Quality'): "
            )
            task = args.task or root.name
            scaffold.build_task(root, project, task)


def _prompt(msg: str) -> str:
    try:
        value = input(msg).strip()
    except KeyboardInterrupt:
        print()
        sys.exit(0)
    if not value:
        print("Value cannot be empty.", file=sys.stderr)
        sys.exit(1)
    return value


if __name__ == "__main__":
    main()
