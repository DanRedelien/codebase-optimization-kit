#!/usr/bin/env python3
"""Safe copier for the self-contained codebase optimization kit runtime."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath


GITIGNORE_START = "# === codebase-optimization-kit start ==="
GITIGNORE_END = "# === codebase-optimization-kit end ==="

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "optimization-kit"
GITHUB_TEMPLATE_ROOT = REPO_ROOT / "templates" / "github"

DEFAULT_TARGET_DIR = ".codebase-optimization-kit"
PROTECTED_PREFIXES = (
    "state/",
    "reports/status.md",
    "reports/agent-plan.md",
    "reports/findings-ranked.md",
    "reports/implementation-backlog.md",
    "reports/final-report.md",
)
GITHUB_TEMPLATE_FILES = {
    "pull-request-optimization.md": ".github/PULL_REQUEST_TEMPLATE/optimization.md",
    "issue-optimization-finding.md": ".github/ISSUE_TEMPLATE/optimization_finding.md",
    "issue-refactor-proposal.md": ".github/ISSUE_TEMPLATE/refactor_proposal.md",
}


@dataclass(frozen=True)
class Config:
    project_root: Path
    target_dir: Path
    target_display: str
    dry_run: bool
    overwrite_kit_files: bool
    with_github: bool


@dataclass
class InstallState:
    writes: int = 0
    warnings: int = 0
    planned_dirs: set[Path] = field(default_factory=set)


def normalize(path: str | Path) -> str:
    raw = str(path).replace("\\", "/").strip()
    parts = [part for part in PurePosixPath(raw).parts if part not in {"", "."}]
    return PurePosixPath(*parts).as_posix().strip("/")


def is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def log(action: str, path: str | Path, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"{action:<9} {path}{suffix}")


def warn(state: InstallState, path: str | Path, detail: str) -> None:
    state.warnings += 1
    log("WARN", path, detail)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy .codebase-optimization-kit/ into an existing project.")
    parser.add_argument("project", help="Existing project directory to install into.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without writing files.")
    parser.add_argument("--target-dir", default=DEFAULT_TARGET_DIR, help="Relative installed kit directory.")
    parser.add_argument(
        "--overwrite-kit-files",
        action="store_true",
        help="Refresh kit-owned runtime files only. State, findings, packets, reports, locks, and decisions are preserved.",
    )
    parser.add_argument("--with-github", action="store_true", help="Also copy optional GitHub templates if missing.")
    return parser.parse_args(argv)


def validate_target(raw: str) -> tuple[Path, str]:
    target = Path(raw)
    if target.is_absolute():
        raise ValueError("--target-dir must be relative")
    if not raw.strip():
        raise ValueError("--target-dir must not be empty")
    if any(part in {"", ".", ".."} for part in target.parts):
        raise ValueError("--target-dir must not contain empty, current, or parent segments")
    display = normalize(target)
    if not display:
        raise ValueError("--target-dir must not resolve to the project root")
    return target, display


def build_config(args: argparse.Namespace) -> Config:
    target, display = validate_target(args.target_dir)
    return Config(
        project_root=Path(args.project).expanduser().absolute(),
        target_dir=target,
        target_display=display,
        dry_run=args.dry_run,
        overwrite_kit_files=args.overwrite_kit_files,
        with_github=args.with_github,
    )


def rel(path: Path, root: Path) -> str:
    try:
        return normalize(path.relative_to(root))
    except ValueError:
        return str(path)


def existing_ancestors(path: Path, stop: Path) -> list[Path]:
    ancestors: list[Path] = []
    current = path
    while current != stop and current != current.parent:
        if current.exists():
            ancestors.append(current)
        current = current.parent
    if stop.exists():
        ancestors.append(stop)
    return list(reversed(ancestors))


def symlink_blocker(path: Path, project_root: Path) -> Path | None:
    for candidate in existing_ancestors(path, project_root):
        if is_link(candidate):
            return candidate
    return None


def ensure_safe_path(path: Path, config: Config, state: InstallState) -> bool:
    blocker = symlink_blocker(path, config.project_root)
    if blocker is not None:
        warn(state, rel(path, config.project_root), f"skipped because {rel(blocker, config.project_root)} is a symlink or junction")
        return False
    if path.exists() and is_link(path):
        warn(state, rel(path, config.project_root), "skipped because destination is a symlink or junction")
        return False
    return True


def ensure_dir(path: Path, config: Config, state: InstallState) -> bool:
    if config.dry_run and path in state.planned_dirs:
        return True
    if not ensure_safe_path(path, config, state):
        return False
    if path.exists():
        if path.is_dir():
            return True
        warn(state, rel(path, config.project_root), "path exists and is not a directory")
        return False
    log("CREATE", rel(path, config.project_root), "directory" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.mkdir(parents=True, exist_ok=True)
    else:
        state.planned_dirs.add(path)
    state.writes += 1
    return True


def is_protected_runtime_path(relative: str) -> bool:
    normalized = normalize(relative)
    return any(normalized == prefix.strip("/") or normalized.startswith(prefix.strip("/") + "/") for prefix in PROTECTED_PREFIXES)


def write_file(path: Path, content: str, config: Config, state: InstallState, *, allow_overwrite: bool) -> bool:
    display = rel(path, config.project_root)
    if not ensure_safe_path(path, config, state):
        return False
    if path.exists():
        if path.is_dir():
            warn(state, display, "path exists and is a directory")
            return False
        if allow_overwrite:
            log("OVERWRITE", display, "kit-owned runtime file" + (" (dry-run)" if config.dry_run else ""))
            if not config.dry_run:
                path.write_text(content, encoding="utf-8", newline="\n")
            state.writes += 1
            return True
        log("SKIP", display, "already exists")
        return False
    if not ensure_dir(path.parent, config, state):
        return False
    log("CREATE", display, "file" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.write_text(content, encoding="utf-8", newline="\n")
    state.writes += 1
    return True


def render_runtime_text(text: str, config: Config) -> str:
    return text.replace(DEFAULT_TARGET_DIR, config.target_display)


def install_runtime(config: Config, state: InstallState) -> None:
    target_root = config.project_root / config.target_dir
    if not ensure_dir(target_root, config, state):
        return
    for source in sorted(path for path in TEMPLATE_ROOT.rglob("*") if path.is_file()):
        if "__pycache__" in source.parts or source.suffix == ".pyc":
            continue
        if is_link(source):
            warn(state, source, "template symlink skipped")
            continue
        relative = normalize(source.relative_to(TEMPLATE_ROOT))
        destination = target_root / Path(relative)
        protected = is_protected_runtime_path(relative)
        allow_overwrite = config.overwrite_kit_files and not protected
        content = render_runtime_text(source.read_text(encoding="utf-8"), config)
        write_file(destination, content, config, state, allow_overwrite=allow_overwrite)


def gitignore_block(config: Config) -> str:
    return f"{GITIGNORE_START}\n{config.target_display.rstrip('/')}/\n{GITIGNORE_END}\n"


def replace_managed_block(existing: str, block: str) -> tuple[str | None, str]:
    starts = existing.count(GITIGNORE_START)
    ends = existing.count(GITIGNORE_END)
    if starts != ends:
        return None, "marker counts do not match"
    if starts > 1:
        return None, "multiple managed marker blocks found"
    if starts == 0:
        prefix = existing
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if prefix and not prefix.endswith("\n\n"):
            prefix += "\n"
        return prefix + block, "append"
    start = existing.index(GITIGNORE_START)
    end = existing.index(GITIGNORE_END) + len(GITIGNORE_END)
    while end < len(existing) and existing[end] in {"\r", "\n"}:
        end += 1
    current = existing[start:end]
    if current.rstrip("\r\n") == block.rstrip("\n"):
        return existing, "same"
    return existing[:start] + block + existing[end:], "replace"


def update_ignore_file(path: Path, config: Config, state: InstallState) -> None:
    if not ensure_safe_path(path, config, state):
        return
    block = gitignore_block(config)
    if not path.exists():
        write_file(path, block, config, state, allow_overwrite=False)
        return
    existing = path.read_text(encoding="utf-8")
    updated, mode = replace_managed_block(existing, block)
    if updated is None:
        warn(state, rel(path, config.project_root), f"managed block skipped: {mode}")
        return
    if mode == "same":
        log("SKIP", rel(path, config.project_root), "managed block already current")
        return
    action = "APPEND" if mode == "append" else "OVERWRITE"
    log(action, rel(path, config.project_root), "managed codebase-optimization-kit block" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.write_text(updated, encoding="utf-8", newline="\n")
    state.writes += 1


def handle_ignore(config: Config, state: InstallState) -> None:
    git_dir = config.project_root / ".git"
    if git_dir.is_dir() and not is_link(git_dir):
        update_ignore_file(git_dir / "info" / "exclude", config, state)
        return
    update_ignore_file(config.project_root / ".gitignore", config, state)


def install_github_templates(config: Config, state: InstallState) -> None:
    if not config.with_github:
        return
    for source_name, destination_name in GITHUB_TEMPLATE_FILES.items():
        source = GITHUB_TEMPLATE_ROOT / source_name
        if not source.exists():
            warn(state, source, "GitHub template is missing")
            continue
        destination = config.project_root / Path(destination_name)
        content = render_runtime_text(source.read_text(encoding="utf-8"), config)
        write_file(destination, content, config, state, allow_overwrite=False)


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        config = build_config(args)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    state = InstallState()
    if not TEMPLATE_ROOT.is_dir():
        print(f"ERROR missing runtime template: {TEMPLATE_ROOT}", file=sys.stderr)
        return 2
    if not config.project_root.exists() or not config.project_root.is_dir():
        print(f"ERROR project directory does not exist: {config.project_root}", file=sys.stderr)
        return 2
    if is_link(config.project_root):
        print(f"ERROR project directory is a symlink or junction: {config.project_root}", file=sys.stderr)
        return 1
    target_root = config.project_root / config.target_dir
    if target_root.exists() and (not target_root.is_dir() or is_link(target_root)):
        print(f"ERROR target path is not a real directory: {target_root}", file=sys.stderr)
        return 1
    install_runtime(config, state)
    handle_ignore(config, state)
    install_github_templates(config, state)
    print(f"DONE      writes={state.writes} warnings={state.warnings}" + (" dry-run" if config.dry_run else ""))
    return 1 if state.warnings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
