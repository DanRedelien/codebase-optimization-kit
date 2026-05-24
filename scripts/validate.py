#!/usr/bin/env python3
"""Validate an installed .codebase-optimization-kit workspace."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path, PurePosixPath


DEFAULT_TARGET_DIR = ".codebase-optimization-kit"


def normalize(path: str | Path) -> str:
    raw = str(path).replace("\\", "/").strip()
    parts = [part for part in PurePosixPath(raw).parts if part not in {"", "."}]
    return PurePosixPath(*parts).as_posix().strip("/")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an installed codebase optimization kit runtime.")
    parser.add_argument("project", help="Project directory containing the installed kit.")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help="Relative installed kit directory.")
    parser.add_argument("--enforce-packet", action="store_true", help="Also enforce active packet scope with git status.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    project_root = Path(args.project).expanduser().absolute()
    target_dir = Path(normalize(args.target_dir))
    if target_dir.is_absolute() or any(part == ".." for part in target_dir.parts):
        print("ERROR --target-dir must be a relative path inside the project", file=sys.stderr)
        return 2
    if not project_root.is_dir():
        print(f"ERROR project directory does not exist: {project_root}", file=sys.stderr)
        return 2
    kit = project_root / target_dir
    kit_py = kit / "kit.py"
    if not kit_py.is_file():
        print(f"ERROR installed kit runtime not found: {kit_py}", file=sys.stderr)
        return 1
    commands = [[sys.executable, str(kit_py), "doctor"], [sys.executable, str(kit_py), "validate"]]
    if args.enforce_packet:
        commands[-1].append("--enforce-packet")
    final_code = 0
    for command in commands:
        result = subprocess.run(command, cwd=project_root, text=True)
        if result.returncode != 0:
            final_code = result.returncode
    return final_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
