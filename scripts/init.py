#!/usr/bin/env python3
"""Safe installer for codebase-optimization-kit."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath


KIT_NAME = "codebase-optimization-kit"
KIT_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1"

GITIGNORE_START = "# === codebase-optimization-kit start ==="
GITIGNORE_END = "# === codebase-optimization-kit end ==="

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "templates" / "optimization-kit"
GITHUB_TEMPLATE_ROOT = REPO_ROOT / "templates" / "github"

TEMPLATE_FILES = (
    "START_HERE.md",
    "AGENTS.optimization.md",
    "AGENTS.merge-snippet.md",
    "SAFE_TO_DELETE.md",
    "status.md",
    "workflows/README.md",
    "workflows/01-discovery.md",
    "workflows/02-risk-and-evidence.md",
    "workflows/03-implementation.md",
    "workflows/04-validation-rollback-archive.md",
    "workflows/05-qa-and-review.md",
    "roles/README.md",
    "roles/qa-agent.md",
    "roles/review-agent.md",
    "templates/README.md",
    "templates/context-packet.template.md",
    "templates/decision-record.template.md",
    "templates/durable-knowledge-promotion-proposal.template.md",
    "templates/final-summary.template.md",
    "templates/finding.template.md",
    "templates/implementation-packet.template.md",
    "templates/rollback-plan.template.md",
    "scoring/README.md",
    "scoring/confidence.md",
    "scoring/impact.md",
    "scoring/priority.md",
    "scoring/risk.md",
    "scoring/risk-policy.md",
    "language-adapters/README.md",
    "language-adapters/cpp.md",
    "language-adapters/go.md",
    "language-adapters/java.md",
    "language-adapters/python.md",
    "language-adapters/rust.md",
    "language-adapters/typescript.md",
    "workspace/README.md",
)

GENERATED_KIT_FILES = ("manifest.json",)

PROTECTED_PATHS = (
    "workspace/",
    "workspace/maps/",
    "workspace/findings/",
    "workspace/reports/",
    "workspace/context-packets/",
    "workspace/implementation-packets/",
    "workspace/decisions/",
    "workspace/locks/",
    "workspace/private/",
    "workspace/cache/",
    "workspace/raw/",
)

PRIVATE_WORKSPACE_DIRS = (
    "workspace/private",
    "workspace/cache",
    "workspace/raw",
)

GITHUB_TEMPLATE_FILES = {
    "pull-request-optimization.md": ".github/PULL_REQUEST_TEMPLATE/optimization.md",
    "issue-optimization-finding.md": ".github/ISSUE_TEMPLATE/optimization_finding.md",
    "issue-refactor-proposal.md": ".github/ISSUE_TEMPLATE/refactor_proposal.md",
}


def normalize_posix(path: str | Path) -> str:
    raw = Path(path)
    return PurePosixPath(*raw.parts).as_posix().strip("/")


@dataclass(frozen=True)
class InstallerConfig:
    project_root: Path
    target_dir: Path
    target_dir_display: str
    dry_run: bool
    private_workspace: bool
    with_github: bool
    overwrite_kit_files: bool
    gitignore_all: bool


@dataclass
class InstallState:
    overwrite_enabled: bool
    github_template_overwrite_enabled: bool = False
    warning_count: int = 0
    write_count: int = 0
    planned_dirs: set[Path] = field(default_factory=set)


def is_protected_workspace_path(relative_path: str) -> bool:
    normalized = normalize_posix(relative_path)
    return normalized == "workspace" or normalized.startswith("workspace/")


OVERWRITE_ALLOWLIST = tuple(
    sorted(
        path
        for path in (*TEMPLATE_FILES, *GENERATED_KIT_FILES)
        if not is_protected_workspace_path(path)
    )
)


def format_path(path: Path, project_root: Path | None = None) -> str:
    try:
        if project_root is not None:
            return normalize_posix(path.relative_to(project_root))
    except ValueError:
        pass
    return str(path)


def is_link_path(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def log(action: str, path: Path | str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"{action:<9} {path}{suffix}")


def warn(path: Path | str, detail: str) -> None:
    log("WARN", path, detail)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a temporary codebase optimization workspace into an existing project."
    )
    parser.add_argument("project", help="Existing project directory to install into.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without writing files.")
    parser.add_argument(
        "--private-workspace",
        action="store_true",
        help="Create ignored private/cache/raw workspace directories.",
    )
    parser.add_argument(
        "--with-github",
        action="store_true",
        help="Install optimization GitHub issue and pull request templates.",
    )
    parser.add_argument(
        "--overwrite-kit-files",
        action="store_true",
        help="Overwrite only known kit-owned files and requested GitHub templates.",
    )
    parser.add_argument(
        "--target-dir",
        default=".optimization-kit",
        help="Relative target directory for the installed kit.",
    )
    parser.add_argument(
        "--gitignore-all",
        action="store_true",
        help="Ignore the entire installed kit directory instead of only private/cache/raw paths.",
    )
    return parser.parse_args(argv)


def validate_target_dir(raw_target_dir: str) -> tuple[Path, str]:
    target_dir = Path(raw_target_dir)
    if target_dir.is_absolute():
        raise ValueError("--target-dir must be relative to the project root.")
    if not raw_target_dir.strip():
        raise ValueError("--target-dir must not be empty.")
    if any(part in {"", ".", ".."} for part in target_dir.parts):
        raise ValueError("--target-dir must not contain empty, current, or parent path segments.")
    target_display = normalize_posix(target_dir)
    if not target_display:
        raise ValueError("--target-dir must not resolve to the project root.")
    return target_dir, target_display


def build_config(args: argparse.Namespace) -> InstallerConfig:
    project_root = Path(args.project).expanduser().absolute()
    target_dir, target_display = validate_target_dir(args.target_dir)
    return InstallerConfig(
        project_root=project_root,
        target_dir=target_dir,
        target_dir_display=target_display,
        dry_run=args.dry_run,
        private_workspace=args.private_workspace,
        with_github=args.with_github,
        overwrite_kit_files=args.overwrite_kit_files,
        gitignore_all=args.gitignore_all,
    )


def validate_project_root(config: InstallerConfig) -> bool:
    root = config.project_root
    if not root.exists():
        warn(root, "project directory does not exist; no files written")
        return False
    if not root.is_dir():
        warn(root, "project path is not a directory; no files written")
        return False
    if is_link_path(root):
        warn(root, "project directory is a symlink or junction; skipped because link installs are not supported")
        return False
    return True


def existing_ancestors(path: Path, stop_at: Path) -> list[Path]:
    ancestors: list[Path] = []
    current = path
    while current != stop_at and current != current.parent:
        if current.exists():
            ancestors.append(current)
        current = current.parent
    if stop_at.exists():
        ancestors.append(stop_at)
    return list(reversed(ancestors))


def symlink_blocker(path: Path, project_root: Path) -> Path | None:
    for candidate in existing_ancestors(path, project_root):
        if is_link_path(candidate):
            return candidate
    return None


def path_is_safe_for_write(path: Path, config: InstallerConfig, state: InstallState) -> bool:
    if is_link_path(path):
        state.warning_count += 1
        warn(
            format_path(path, config.project_root),
            "skipped because the destination path is a symlink or junction",
        )
        return False
    blocker = symlink_blocker(path, config.project_root)
    if blocker is not None:
        state.warning_count += 1
        warn(
            format_path(path, config.project_root),
            f"skipped because {format_path(blocker, config.project_root)} is a symlink or junction",
        )
        return False
    return True


def ensure_directory(path: Path, config: InstallerConfig, state: InstallState) -> bool:
    display = format_path(path, config.project_root)
    if config.dry_run and path in state.planned_dirs:
        return True
    if not path_is_safe_for_write(path, config, state):
        return False
    if path.exists():
        if path.is_dir():
            log("SKIP", display, "directory already exists")
            return True
        state.warning_count += 1
        warn(display, "path exists and is not a directory")
        return False
    log("CREATE", display, "directory" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.mkdir(parents=True, exist_ok=True)
    else:
        state.planned_dirs.add(path)
    state.write_count += 1
    return True


def write_file(
    path: Path,
    content: str,
    config: InstallerConfig,
    state: InstallState,
    *,
    allow_overwrite: bool = False,
    overwrite_reason: str = "known kit-owned file",
) -> bool:
    display = format_path(path, config.project_root)
    if not path_is_safe_for_write(path, config, state):
        return False
    if path.exists():
        if path.is_dir():
            state.warning_count += 1
            warn(display, "path exists and is a directory")
            return False
        if allow_overwrite:
            log("OVERWRITE", display, overwrite_reason + (" (dry-run)" if config.dry_run else ""))
            if not config.dry_run:
                path.write_text(content, encoding="utf-8", newline="\n")
            state.write_count += 1
            return True
        log("SKIP", display, "already exists")
        return False
    parent = path.parent
    if not ensure_parent_directory(parent, config, state):
        return False
    log("CREATE", display, "file" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.write_text(content, encoding="utf-8", newline="\n")
    state.write_count += 1
    return True


def ensure_parent_directory(path: Path, config: InstallerConfig, state: InstallState) -> bool:
    display = format_path(path, config.project_root)
    if config.dry_run and path in state.planned_dirs:
        return True
    if not path_is_safe_for_write(path, config, state):
        return False
    if path.exists():
        if path.is_dir():
            return True
        state.warning_count += 1
        warn(display, "parent path exists and is not a directory")
        return False
    log("CREATE", display, "directory" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        path.mkdir(parents=True, exist_ok=True)
    else:
        state.planned_dirs.add(path)
    state.write_count += 1
    return True


def render_template_text(text: str, config: InstallerConfig) -> str:
    return text.replace(".optimization-kit", config.target_dir_display)


def read_template(relative_path: str, config: InstallerConfig, state: InstallState) -> str | None:
    source = TEMPLATE_ROOT / Path(relative_path)
    if not source.exists():
        state.warning_count += 1
        warn(source, "template file is missing")
        return None
    return render_template_text(source.read_text(encoding="utf-8"), config)


def generated_manifest(config: InstallerConfig) -> str:
    manifest = {
        "kit": KIT_NAME,
        "kit_version": KIT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "workspace_type": "temporary",
        "intended_lifetime": "single optimization pass",
        "installed_at": date.today().isoformat(),
        "target_dir": config.target_dir_display,
        "private_workspace": config.private_workspace,
        "github_templates": config.with_github,
        "safe_to_delete_after": "final summary is exported and accepted changes are merged",
        "ownership": {
            "kit_owned_paths": list(OVERWRITE_ALLOWLIST),
            "github_template_paths": list(GITHUB_TEMPLATE_FILES.values()),
            "protected_paths": list(PROTECTED_PATHS),
            "overwrite_policy": (
                "--overwrite-kit-files may overwrite only kit_owned_paths inside target_dir "
                "and github_template_paths when --with-github is used. "
                "workspace, private, cache, raw, maps, findings, reports, context packets, "
                "implementation packets, decisions, and locks are never overwritten."
            ),
        },
        "migration_policy": {
            "summary": (
                "Installer reads schema_version; unknown newer schema = warn and refuse overwrite; "
                "older schema = install only missing kit files unless update command exists."
            ),
            "reader_rule": "Installer reads schema_version before overwrite decisions.",
            "unknown_newer_schema": "Warn and refuse overwrite.",
            "older_schema": "Install only missing kit files unless an explicit update command exists.",
        },
    }
    return json.dumps(manifest, indent=2, ensure_ascii=True) + "\n"


def parse_schema_version(raw: object) -> tuple[int, ...] | None:
    if not isinstance(raw, str):
        return None
    parts: list[int] = []
    for part in raw.split("."):
        if not part.isdigit():
            return None
        parts.append(int(part))
    return tuple(parts)


def determine_overwrite(config: InstallerConfig, state: InstallState) -> None:
    if not config.overwrite_kit_files:
        state.overwrite_enabled = False
        return

    manifest_path = config.project_root / config.target_dir / "manifest.json"
    display = format_path(manifest_path, config.project_root)
    if not manifest_path.exists():
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because existing manifest metadata is missing")
        return
    if not path_is_safe_for_write(manifest_path, config, state):
        state.overwrite_enabled = False
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because manifest.json is not valid JSON")
        return

    if manifest.get("kit") != KIT_NAME:
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because manifest kit does not match")
        return

    current_schema = parse_schema_version(SCHEMA_VERSION)
    installed_schema = parse_schema_version(manifest.get("schema_version"))
    if current_schema is None or installed_schema is None:
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because schema_version is not comparable")
        return
    if installed_schema > current_schema:
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because installed schema_version is newer")
        return
    if installed_schema < current_schema:
        state.overwrite_enabled = False
        state.warning_count += 1
        warn(display, "--overwrite-kit-files ignored because installed schema_version is older and no update command exists")
        return

    state.overwrite_enabled = True
    state.github_template_overwrite_enabled = manifest.get("github_templates") is True


def can_overwrite_kit_path(relative_path: str, state: InstallState) -> bool:
    return state.overwrite_enabled and relative_path in OVERWRITE_ALLOWLIST


def install_kit_files(config: InstallerConfig, state: InstallState) -> None:
    target_root = config.project_root / config.target_dir
    if not ensure_directory(target_root, config, state):
        return

    for relative_path in TEMPLATE_FILES:
        content = read_template(relative_path, config, state)
        if content is None:
            continue
        destination = target_root / Path(relative_path)
        write_file(
            destination,
            content,
            config,
            state,
            allow_overwrite=can_overwrite_kit_path(relative_path, state),
        )

    write_file(
        target_root / "manifest.json",
        generated_manifest(config),
        config,
        state,
        allow_overwrite=can_overwrite_kit_path("manifest.json", state),
    )


def minimal_root_agents(config: InstallerConfig) -> str:
    target = config.target_dir_display
    return (
        "# Agent Instructions\n\n"
        f"This project may contain `{target}/`, a temporary audit/refactor workspace for one optimization pass.\n\n"
        "- Existing project documentation and maintainer instructions remain the source of truth.\n"
        f"- Read `{target}/START_HERE.md` before using the optimization kit.\n"
        f"- Discovery notes and temporary artifacts belong in `{target}/workspace/`.\n"
        "- Do not edit project source files without an approved implementation packet.\n"
        "- Do not promote kit findings into permanent project docs without maintainer approval.\n"
    )


def handle_root_agents(config: InstallerConfig, state: InstallState) -> None:
    agents_path = config.project_root / "AGENTS.md"
    display = format_path(agents_path, config.project_root)
    if symlink_blocker(agents_path, config.project_root) is not None:
        state.warning_count += 1
        warn(display, "skipped because AGENTS.md or its parent path is a symlink or junction")
        return
    if agents_path.exists():
        log("SKIP", display, "existing AGENTS.md is never overwritten")
        snippet = config.project_root / config.target_dir / "AGENTS.merge-snippet.md"
        state.warning_count += 1
        warn(
            display,
            f"review optional merge snippet at {format_path(snippet, config.project_root)}",
        )
        return
    write_file(agents_path, minimal_root_agents(config), config, state)


def gitignore_entries(config: InstallerConfig) -> list[str]:
    target = config.target_dir_display.rstrip("/")
    if config.gitignore_all:
        return [f"{target}/"]
    return [
        f"{target}/workspace/private/",
        f"{target}/workspace/cache/",
        f"{target}/workspace/raw/",
    ]


def gitignore_block_from_entries(entries: list[str]) -> str:
    body = "\n".join(entries)
    return f"{GITIGNORE_START}\n{body}\n{GITIGNORE_END}\n"


def gitignore_block(config: InstallerConfig) -> str:
    return gitignore_block_from_entries(gitignore_entries(config))


def marker_entries(existing: str) -> list[str] | None:
    if existing.count(GITIGNORE_START) != 1 or existing.count(GITIGNORE_END) != 1:
        return None
    start = existing.index(GITIGNORE_START) + len(GITIGNORE_START)
    end = existing.index(GITIGNORE_END)
    body = existing[start:end]
    return [line.strip() for line in body.splitlines() if line.strip()]


def desired_gitignore_block(existing: str | None, config: InstallerConfig) -> str:
    target = config.target_dir_display.rstrip("/")
    if existing is not None and not config.gitignore_all:
        entries = marker_entries(existing)
        if entries is not None and f"{target}/" in entries:
            return gitignore_block_from_entries([f"{target}/"])
    return gitignore_block(config)


def replace_marker_block(existing: str, replacement: str) -> tuple[str | None, str]:
    start_count = existing.count(GITIGNORE_START)
    end_count = existing.count(GITIGNORE_END)
    if start_count != end_count:
        return None, "marker counts do not match"
    if start_count > 1:
        return None, "multiple managed marker blocks found"
    if start_count == 0:
        prefix = existing
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if prefix and not prefix.endswith("\n\n"):
            prefix += "\n"
        return prefix + replacement, "append"
    start = existing.index(GITIGNORE_START)
    end = existing.index(GITIGNORE_END) + len(GITIGNORE_END)
    while end < len(existing) and existing[end] in {"\r", "\n"}:
        end += 1
    current = existing[start:end]
    if current.rstrip("\r\n") == replacement.rstrip("\n"):
        return existing, "same"
    return existing[:start] + replacement + existing[end:], "replace"


def handle_gitignore(config: InstallerConfig, state: InstallState) -> None:
    gitignore_path = config.project_root / ".gitignore"
    display = format_path(gitignore_path, config.project_root)
    if not path_is_safe_for_write(gitignore_path, config, state):
        return
    if not gitignore_path.exists():
        block = gitignore_block(config)
        log("CREATE", display, "file" + (" (dry-run)" if config.dry_run else ""))
        if not config.dry_run:
            gitignore_path.write_text(block, encoding="utf-8", newline="\n")
        state.write_count += 1
        return

    existing = gitignore_path.read_text(encoding="utf-8")
    block = desired_gitignore_block(existing, config)
    updated, mode = replace_marker_block(existing, block)
    if updated is None:
        state.warning_count += 1
        warn(display, f"managed .gitignore block skipped: {mode}")
        return
    if mode == "same":
        log("SKIP", display, "managed block already current")
        return
    if mode == "append":
        log("APPEND", display, "managed optimization-kit block" + (" (dry-run)" if config.dry_run else ""))
    else:
        log("OVERWRITE", display, "managed optimization-kit block" + (" (dry-run)" if config.dry_run else ""))
    if not config.dry_run:
        gitignore_path.write_text(updated, encoding="utf-8", newline="\n")
    state.write_count += 1


def handle_private_workspace(config: InstallerConfig, state: InstallState) -> None:
    if not config.private_workspace:
        return
    target_root = config.project_root / config.target_dir
    for relative_path in PRIVATE_WORKSPACE_DIRS:
        ensure_directory(target_root / Path(relative_path), config, state)


def handle_github_templates(config: InstallerConfig, state: InstallState) -> None:
    if not config.with_github:
        return
    for source_name, destination_path in GITHUB_TEMPLATE_FILES.items():
        source = GITHUB_TEMPLATE_ROOT / source_name
        if not source.exists():
            state.warning_count += 1
            warn(source, "GitHub template file is missing")
            continue
        content = render_template_text(source.read_text(encoding="utf-8"), config)
        destination = config.project_root / Path(destination_path)
        destination_matches_template = False
        if destination.exists() and not destination.is_dir() and not is_link_path(destination):
            try:
                destination_matches_template = destination.read_text(encoding="utf-8") == content
            except OSError:
                destination_matches_template = False
        write_file(
            destination,
            content,
            config,
            state,
            allow_overwrite=state.github_template_overwrite_enabled or destination_matches_template,
            overwrite_reason="known kit-owned GitHub template",
        )


def main(argv: list[str]) -> int:
    try:
        args = parse_args(argv)
        config = build_config(args)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2

    state = InstallState(overwrite_enabled=False)
    if not validate_project_root(config):
        return 1

    target_root = config.project_root / config.target_dir
    if target_root.exists() and is_link_path(target_root):
        warn(
            format_path(target_root, config.project_root),
            "target directory is a symlink or junction; no install performed",
        )
        return 1
    if target_root.exists() and not target_root.is_dir():
        warn(
            format_path(target_root, config.project_root),
            "target path exists and is not a directory; no install performed",
        )
        return 1

    determine_overwrite(config, state)
    install_kit_files(config, state)
    handle_private_workspace(config, state)
    handle_root_agents(config, state)
    handle_gitignore(config, state)
    handle_github_templates(config, state)

    print(
        f"DONE      writes={state.write_count} warnings={state.warning_count}"
        + (" dry-run" if config.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
