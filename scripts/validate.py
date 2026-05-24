#!/usr/bin/env python3
"""Validate an installed codebase-optimization-kit workspace."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from urllib.parse import unquote


KIT_NAME = "codebase-optimization-kit"
GITIGNORE_START = "# === codebase-optimization-kit start ==="
GITIGNORE_END = "# === codebase-optimization-kit end ==="

REQUIRED_MANIFEST_FIELDS = {
    "kit": str,
    "kit_version": str,
    "schema_version": str,
    "workspace_type": str,
    "intended_lifetime": str,
    "installed_at": str,
    "target_dir": str,
    "private_workspace": bool,
    "github_templates": bool,
    "safe_to_delete_after": str,
    "ownership": dict,
    "migration_policy": dict,
}

REQUIRED_KIT_FILES = (
    "START_HERE.md",
    "status.md",
)

REQUIRED_KIT_DIRS = (
    "workflows",
    "roles",
    "templates",
    "scoring",
    "language-adapters",
    "workspace",
)

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

GITHUB_TEMPLATE_PATHS = (
    ".github/PULL_REQUEST_TEMPLATE/optimization.md",
    ".github/ISSUE_TEMPLATE/optimization_finding.md",
    ".github/ISSUE_TEMPLATE/refactor_proposal.md",
)

ACTIVE_PACKET_STATUSES = {"approved"}

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SCRIPT_RE = re.compile(
    "["
    "\u0370-\u03ff"
    "\u0400-\u052f"
    "\u3040-\u30ff"
    "\u3400-\u4dbf"
    "\u4e00-\u9fff"
    "\uac00-\ud7af"
    "]"
)


def normalize_posix(path: str | Path) -> str:
    raw = Path(path)
    return PurePosixPath(*raw.parts).as_posix().strip("/")


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


@dataclass
class Finding:
    level: str
    path: str
    message: str


@dataclass
class ValidationState:
    project_root: Path
    target_dir: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def kit_root(self) -> Path:
        return self.project_root / Path(self.target_dir)

    def error(self, path: str | Path, message: str) -> None:
        self.findings.append(Finding("ERROR", str(path), message))

    def warn(self, path: str | Path, message: str) -> None:
        self.findings.append(Finding("WARN", str(path), message))

    def ok(self, path: str | Path, message: str) -> None:
        self.findings.append(Finding("OK", str(path), message))

    def rel(self, path: Path) -> str:
        try:
            return normalize_posix(path.relative_to(self.project_root))
        except ValueError:
            return str(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate an installed codebase-optimization-kit workspace."
    )
    parser.add_argument("project", help="Project directory containing the installed kit.")
    parser.add_argument(
        "--target-dir",
        help="Relative installed kit directory. Defaults to .optimization-kit or manifest target_dir when found.",
    )
    parser.add_argument(
        "--expect-github",
        action="store_true",
        help="Require optimization GitHub issue and pull request templates.",
    )
    parser.add_argument(
        "--private-workspace",
        action="store_true",
        help="Require private/cache/raw workspace directories and ignore coverage.",
    )
    parser.add_argument(
        "--check-working-tree",
        action="store_true",
        help="Warn when changed project files are outside the active implementation packet.",
    )
    return parser.parse_args(argv)


def load_manifest(path: Path) -> dict[str, object] | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def detect_target_dir(project_root: Path, explicit_target_dir: str | None) -> str:
    if explicit_target_dir:
        return normalize_posix(explicit_target_dir)
    default_manifest = project_root / ".optimization-kit" / "manifest.json"
    manifest = load_manifest(default_manifest)
    if manifest and isinstance(manifest.get("target_dir"), str):
        return normalize_posix(str(manifest["target_dir"]))
    return ".optimization-kit"


def read_manifest(state: ValidationState) -> dict[str, object] | None:
    manifest_path = state.kit_root / "manifest.json"
    if not manifest_path.exists():
        state.error(state.rel(manifest_path), "manifest.json is missing")
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        state.error(state.rel(manifest_path), f"manifest.json is not valid JSON: {exc}")
        return None
    if not isinstance(manifest, dict):
        state.error(state.rel(manifest_path), "manifest.json must contain a JSON object")
        return None
    state.ok(state.rel(manifest_path), "manifest exists")
    return manifest


def validate_manifest(state: ValidationState, manifest: dict[str, object] | None) -> bool:
    if manifest is None:
        return False

    manifest_path = state.kit_root / "manifest.json"
    for field_name, expected_type in REQUIRED_MANIFEST_FIELDS.items():
        if field_name not in manifest:
            state.error(state.rel(manifest_path), f"required manifest field is missing: {field_name}")
            continue
        if not isinstance(manifest[field_name], expected_type):
            state.error(state.rel(manifest_path), f"manifest field has wrong type: {field_name}")

    if manifest.get("kit") != KIT_NAME:
        state.error(state.rel(manifest_path), f"manifest kit must be {KIT_NAME}")
    if manifest.get("workspace_type") != "temporary":
        state.error(state.rel(manifest_path), "workspace_type must be temporary")
    if normalize_posix(str(manifest.get("target_dir", ""))) != state.target_dir:
        state.error(state.rel(manifest_path), "target_dir does not match the validated kit directory")

    installed_at = manifest.get("installed_at")
    if isinstance(installed_at, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", installed_at):
        state.error(state.rel(manifest_path), "installed_at must use YYYY-MM-DD")

    state.ok(state.rel(manifest_path), "required manifest fields checked")
    return True


def validate_required_paths(state: ValidationState) -> None:
    for relative_path in REQUIRED_KIT_FILES:
        path = state.kit_root / Path(relative_path)
        if path.is_file():
            state.ok(state.rel(path), "required file exists")
        else:
            state.error(state.rel(path), "required file is missing")

    for relative_path in REQUIRED_KIT_DIRS:
        path = state.kit_root / Path(relative_path)
        if path.is_dir():
            state.ok(state.rel(path), "required directory exists")
        else:
            state.error(state.rel(path), "required directory is missing")


def extract_gitignore_entries(content: str) -> tuple[list[str] | None, str | None]:
    start_count = content.count(GITIGNORE_START)
    end_count = content.count(GITIGNORE_END)
    if start_count != 1 or end_count != 1:
        return None, f"expected exactly one managed block, found start={start_count} end={end_count}"
    start = content.index(GITIGNORE_START) + len(GITIGNORE_START)
    end = content.index(GITIGNORE_END)
    if start > end:
        return None, "managed block markers are out of order"
    entries = [line.strip() for line in content[start:end].splitlines() if line.strip()]
    return entries, None


def private_entries(target_dir: str) -> list[str]:
    target = target_dir.rstrip("/")
    return [
        f"{target}/workspace/private/",
        f"{target}/workspace/cache/",
        f"{target}/workspace/raw/",
    ]


def validate_gitignore(state: ValidationState) -> set[str]:
    gitignore_path = state.project_root / ".gitignore"
    if not gitignore_path.exists():
        state.error(state.rel(gitignore_path), ".gitignore is missing")
        return set()

    content = gitignore_path.read_text(encoding="utf-8")
    entries, error = extract_gitignore_entries(content)
    if error:
        state.error(state.rel(gitignore_path), error)
        return set()

    assert entries is not None
    duplicates = sorted({entry for entry in entries if entries.count(entry) > 1})
    if duplicates:
        state.error(state.rel(gitignore_path), "managed block contains duplicate entries: " + ", ".join(duplicates))
    else:
        state.ok(state.rel(gitignore_path), "managed block entries are not duplicated")

    target_entry = f"{state.target_dir.rstrip('/')}/"
    expected_private = private_entries(state.target_dir)
    if target_entry in entries or all(entry in entries for entry in expected_private):
        state.ok(state.rel(gitignore_path), "private/cache/raw paths are ignored")
    else:
        state.error(
            state.rel(gitignore_path),
            "managed block must ignore the whole kit or private/cache/raw workspace paths",
        )

    return set(entries)


def validate_private_workspace(state: ValidationState, manifest: dict[str, object] | None, cli_expected: bool) -> None:
    manifest_expected = bool(manifest and manifest.get("private_workspace") is True)
    expected = cli_expected or manifest_expected
    if not expected:
        return

    for relative_path in PRIVATE_WORKSPACE_DIRS:
        path = state.kit_root / Path(relative_path)
        if path.is_dir():
            state.ok(state.rel(path), "private workspace directory exists")
        else:
            state.error(state.rel(path), "private workspace directory is missing")


def path_is_protected(relative_path: str) -> bool:
    normalized = normalize_posix(relative_path)
    return any(
        normalized == protected.strip("/") or normalized.startswith(protected.strip("/") + "/")
        for protected in PROTECTED_PATHS
    )


def validate_artifact_protection(state: ValidationState, manifest: dict[str, object] | None) -> None:
    manifest_path = state.kit_root / "manifest.json"
    ownership = manifest.get("ownership") if manifest else None
    if not isinstance(ownership, dict):
        state.error(state.rel(manifest_path), "ownership metadata is missing")
        return

    protected_paths = ownership.get("protected_paths")
    kit_owned_paths = ownership.get("kit_owned_paths")
    github_template_paths = ownership.get("github_template_paths")
    overwrite_policy = ownership.get("overwrite_policy")
    if not isinstance(protected_paths, list) or not all(isinstance(item, str) for item in protected_paths):
        state.error(state.rel(manifest_path), "ownership.protected_paths must be a string list")
        return
    if not isinstance(kit_owned_paths, list) or not all(isinstance(item, str) for item in kit_owned_paths):
        state.error(state.rel(manifest_path), "ownership.kit_owned_paths must be a string list")
        return
    if not isinstance(github_template_paths, list) or not all(isinstance(item, str) for item in github_template_paths):
        state.error(state.rel(manifest_path), "ownership.github_template_paths must be a string list")
        return
    if not isinstance(overwrite_policy, str) or not overwrite_policy.strip():
        state.error(state.rel(manifest_path), "ownership.overwrite_policy must be a non-empty string")
        return

    missing = [path for path in PROTECTED_PATHS if path not in protected_paths]
    if missing:
        state.error(state.rel(manifest_path), "protected workspace paths missing from manifest: " + ", ".join(missing))
    else:
        state.ok(state.rel(manifest_path), "project artifact paths are protected")

    protected_owned = [path for path in kit_owned_paths if path_is_protected(path)]
    if protected_owned:
        state.error(
            state.rel(manifest_path),
            "kit_owned_paths must not include project artifacts: " + ", ".join(protected_owned),
        )
    else:
        state.ok(state.rel(manifest_path), "kit-owned overwrite list excludes project artifacts")

    missing_github_paths = [path for path in GITHUB_TEMPLATE_PATHS if path not in github_template_paths]
    if missing_github_paths:
        state.error(state.rel(manifest_path), "GitHub template paths missing from manifest: " + ", ".join(missing_github_paths))
    else:
        state.ok(state.rel(manifest_path), "GitHub template paths are recorded")

    if "locks" not in overwrite_policy:
        state.error(state.rel(manifest_path), "ownership.overwrite_policy must mention lock protection")
    else:
        state.ok(state.rel(manifest_path), "overwrite policy mentions lock protection")


def validate_migration_policy(state: ValidationState, manifest: dict[str, object] | None) -> None:
    manifest_path = state.kit_root / "manifest.json"
    migration_policy = manifest.get("migration_policy") if manifest else None
    if not isinstance(migration_policy, dict):
        state.error(state.rel(manifest_path), "migration_policy metadata is missing")
        return
    required = ("summary", "reader_rule", "unknown_newer_schema", "older_schema")
    missing = [key for key in required if not isinstance(migration_policy.get(key), str) or not migration_policy.get(key)]
    if missing:
        state.error(state.rel(manifest_path), "migration_policy fields are missing or empty: " + ", ".join(missing))
    else:
        state.ok(state.rel(manifest_path), "migration policy is present")


def generated_markdown_files(state: ValidationState) -> list[Path]:
    files: list[Path] = []
    if state.kit_root.exists():
        for path in state.kit_root.rglob("*.md"):
            relative = normalize_posix(path.relative_to(state.kit_root))
            if relative.startswith("workspace/") and relative != "workspace/README.md":
                continue
            files.append(path)
    for relative_path in GITHUB_TEMPLATE_PATHS:
        path = state.project_root / Path(relative_path)
        if path.exists():
            files.append(path)
    return files


def validate_english_text(state: ValidationState) -> None:
    offenders: list[str] = []
    for path in generated_markdown_files(state):
        text = path.read_text(encoding="utf-8")
        if SCRIPT_RE.search(text):
            offenders.append(state.rel(path))
    if offenders:
        for path in offenders:
            state.error(path, "generated user-facing text contains non-English script characters")
    else:
        state.ok(state.target_dir, "generated user-facing text uses English-compatible scripts")


def clean_markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target


def should_ignore_link(target: str) -> bool:
    lowered = target.lower()
    return (
        not target
        or target.startswith("#")
        or target.startswith("/")
        or "://" in target
        or lowered.startswith("mailto:")
        or lowered.startswith("tel:")
    )


def validate_markdown_links(state: ValidationState) -> None:
    checked = 0
    for markdown_file in generated_markdown_files(state):
        text = markdown_file.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            raw_target = clean_markdown_target(match.group(1))
            if should_ignore_link(raw_target):
                continue
            target_without_anchor = raw_target.split("#", 1)[0]
            if not target_without_anchor:
                continue
            resolved = (markdown_file.parent / Path(unquote(target_without_anchor))).resolve()
            kit_root = state.kit_root.resolve()
            if not is_relative_to(resolved, kit_root):
                continue
            checked += 1
            if not resolved.is_file():
                state.error(
                    state.rel(markdown_file),
                    f"relative kit markdown link target is missing: {raw_target}",
                )
    state.ok(state.target_dir, f"relative markdown links inside the kit checked: {checked}")


def validate_github_templates(state: ValidationState, manifest: dict[str, object] | None, expect_github: bool) -> None:
    manifest_expected = bool(manifest and manifest.get("github_templates") is True)
    if not (expect_github or manifest_expected):
        return
    for relative_path in GITHUB_TEMPLATE_PATHS:
        path = state.project_root / Path(relative_path)
        if path.is_file():
            state.ok(state.rel(path), "GitHub optimization template exists")
        else:
            state.error(state.rel(path), "GitHub optimization template is missing")


def run_git_status(project_root: Path) -> tuple[list[str], str | None]:
    result = subprocess.run(
        ["git", "-C", str(project_root), "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return [], (result.stderr or result.stdout or "git status failed").strip()
    changed: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        changed.append(normalize_posix(path))
    return changed, None


def packet_status(text: str) -> str | None:
    match = re.search(r"(?im)^\s*-\s*Status:\s*`?([^`\n]+?)`?\s*$", text)
    return match.group(1).strip().lower() if match else None


def allowed_files_from_packet(text: str) -> set[str]:
    allowed: set[str] = set()
    in_section = False
    for line in text.splitlines():
        if re.match(r"^##\s+Allowed Files\s*$", line, re.IGNORECASE):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0].lower() in {"file", "---", ""} or set(cells[0]) == {"-"}:
            continue
        allowed.add(normalize_posix(cells[0]))
    return allowed


def active_packet_allowed_files(state: ValidationState) -> tuple[set[str], list[Path]]:
    packet_dir = state.kit_root / "workspace" / "implementation-packets"
    if not packet_dir.exists():
        return set(), []

    allowed: set[str] = set()
    active_packets: list[Path] = []
    for path in packet_dir.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        status = packet_status(text)
        if status not in ACTIVE_PACKET_STATUSES:
            continue
        active_packets.append(path)
        allowed.update(allowed_files_from_packet(text))
    return allowed, active_packets


def validate_working_tree(state: ValidationState) -> None:
    changed_files, error = run_git_status(state.project_root)
    if error:
        state.warn(state.project_root, "--check-working-tree skipped: " + error)
        return

    allowed, packets = active_packet_allowed_files(state)
    if not packets:
        state.warn(state.target_dir, "--check-working-tree found no active implementation packet")
        return
    if len(packets) > 1:
        packet_list = ", ".join(state.rel(path) for path in packets)
        state.warn(state.target_dir, "multiple active implementation packets found: " + packet_list)
    if not allowed:
        state.warn(state.target_dir, "active implementation packet has no allowed files")
        return

    target_prefix = state.target_dir.rstrip("/") + "/"
    project_changes = [
        path
        for path in changed_files
        if path != state.target_dir.rstrip("/") and not path.startswith(target_prefix)
    ]
    outside_packet = [path for path in project_changes if path not in allowed]
    if outside_packet:
        state.warn(
            state.target_dir,
            "changed files outside active implementation packet: " + ", ".join(outside_packet),
        )
    else:
        state.ok(state.target_dir, "changed project files match the active implementation packet")


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(f"{finding.level:<5} {finding.path} - {finding.message}")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    project_root = Path(args.project).expanduser().absolute()
    if not project_root.exists() or not project_root.is_dir():
        print(f"ERROR {project_root} - project directory does not exist", file=sys.stderr)
        return 2

    target_dir = detect_target_dir(project_root, args.target_dir)
    state = ValidationState(project_root=project_root, target_dir=target_dir)

    manifest = read_manifest(state)
    validate_manifest(state, manifest)
    validate_required_paths(state)
    validate_gitignore(state)
    validate_private_workspace(state, manifest, args.private_workspace)
    validate_artifact_protection(state, manifest)
    validate_migration_policy(state, manifest)
    validate_english_text(state)
    validate_markdown_links(state)
    validate_github_templates(state, manifest, args.expect_github)
    if args.check_working_tree:
        validate_working_tree(state)

    print_findings(state.findings)
    error_count = sum(1 for finding in state.findings if finding.level == "ERROR")
    warning_count = sum(1 for finding in state.findings if finding.level == "WARN")
    print(f"DONE  errors={error_count} warnings={warning_count}")
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
