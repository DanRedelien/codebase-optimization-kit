#!/usr/bin/env python3
"""Self-contained runtime for .codebase-optimization-kit."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

KIT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0"
KIT_DIR_NAME = ".codebase-optimization-kit"
MIN_PYTHON = (3, 10)

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
STATE = HERE / "state"
REPORTS = HERE / "reports"
SCHEMA = HERE / "schema"

FINDING_STATUSES = {
    "candidate",
    "needs-evidence",
    "approved",
    "rejected",
    "superseded",
    "implemented",
    "validated",
    "rolled-back",
}
PACKET_STATUSES = {
    "draft",
    "needs-approval",
    "approved",
    "in-progress",
    "implemented",
    "validated",
    "rejected",
    "rolled-back",
    "superseded",
}
ACTIVE_PACKET_STATUSES = {"approved", "in-progress", "implemented"}
IMPLEMENTATION_PACKET_STATUSES = {"approved", "in-progress", "implemented", "validated"}
ROLES = [
    "architecture-auditor",
    "dead-code-auditor",
    "dependency-auditor",
    "duplicate-logic-auditor",
    "test-coverage-auditor",
    "performance-auditor",
    "integration-auditor",
    "domain-risk-auditor",
    "todo-assumption-auditor",
]
DEAD_CODE_CLASSES = {
    "truly_unreachable",
    "unused_internal_export",
    "unused_public_export",
    "legacy_branch",
    "duplicate_implementation",
    "dormant_planned_code",
    "external_contract_code",
    "dynamic_usage_unknown",
    "generated_or_vendor_code",
}
DEAD_CODE_CHECKS = [
    "static_reference_check",
    "entrypoint_check",
    "config_check",
    "test_or_runtime_check",
    "public_contract_check",
    "generated_vendor_check",
    "counterevidence_and_gaps",
]
METRICS = [
    "passing_tests",
    "behavioral_parity",
    "dependency_reduction",
    "duplicate_logic_reduction",
    "dead_code_confidence",
    "complexity_reduction",
    "risk_score",
    "reversibility",
]
POLICIES = HERE / "policies"

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".scala": "scala",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
}
PACKAGE_MANIFESTS = {
    "package.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "go.mod",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Gemfile",
    "composer.json",
    "Makefile",
    "CMakeLists.txt",
}
LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "go.sum",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
}
CONFIG_NAMES = {
    ".env.example",
    ".eslintrc",
    ".prettierrc",
    "tsconfig.json",
    "pytest.ini",
    "tox.ini",
    "ruff.toml",
    "mypy.ini",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "Makefile",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "bower_components",
    "vendor",
    "third_party",
    "external",
    "dist",
    "build",
    "out",
    "target",
    "coverage",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    "__pycache__",
}
GENERATED_DIRS = {"generated", "gen", "dist", "build", "out", "target", "coverage"}
VENDOR_DIRS = {"node_modules", "vendor", "third_party", "external", "bower_components"}
ZONE_BOUNDARIES = {"packages", "apps", "services", "crates", "cmd", "modules", "plugins"}
JSON_DEFAULTS: dict[str, Any] = {
    "project.json": {},
    "census.json": {"summary": {}, "language_mix": {}, "loc_by_directory": {}, "largest_files": []},
    "zones.json": {"zones": []},
    "contracts.json": {"contracts": []},
    "tests.json": {"test_files": [], "commands": []},
    "metrics.json": {"metrics": {}},
}
JSONL_FILES = [
    "file-tree.jsonl",
    "agent-tasks.jsonl",
    "findings.jsonl",
    "packets.jsonl",
    "validations.jsonl",
    "locks.jsonl",
    "decisions.jsonl",
]
GITIGNORE_START = "# === codebase-optimization-kit start ==="
GITIGNORE_END = "# === codebase-optimization-kit end ==="


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def norm(raw: str | Path) -> str:
    value = str(raw).replace("\\", "/").strip()
    value = re.sub(r"^\./+", "", value)
    parts = [part for part in PurePosixPath(value).parts if part not in {"", "."}]
    return PurePosixPath(*parts).as_posix() if parts else "."


def rel(path: Path) -> str:
    try:
        return norm(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def state(name: str) -> Path:
    return STATE / name


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return records, errors
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{rel(path)}:{line_no}: invalid JSONL record: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{rel(path)}:{line_no}: JSONL record must be an object")
            continue
        records.append(record)
    return records, errors


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def ensure_runtime() -> None:
    for directory in [STATE, REPORTS, SCHEMA, HERE / "policies", HERE / "templates"]:
        directory.mkdir(parents=True, exist_ok=True)
    for filename, default in JSON_DEFAULTS.items():
        path = state(filename)
        if not path.exists():
            save_json(path, default)
    for filename in JSONL_FILES:
        path = state(filename)
        if not path.exists():
            path.write_text("", encoding="utf-8", newline="\n")
    project = load_json(state("project.json"), {})
    if not isinstance(project, dict):
        project = {}
    project.setdefault("kit_version", KIT_VERSION)
    project.setdefault("schema_version", SCHEMA_VERSION)
    project.setdefault("workspace_type", "temporary")
    project.setdefault("project_root", ".")
    project["target_dir"] = HERE.name
    project.setdefault("created_at", today())
    if project.get("created_at") == "YYYY-MM-DD":
        project["created_at"] = today()
    project.setdefault("source_of_truth", {"root_agents": "AGENTS.md", "project_readme": "README.md", "project_docs": []})
    save_json(state("project.json"), project)


def non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"todo", "tbd", "unknown", "null", "none"}
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def load_metrics_policy() -> dict[str, Any]:
    value = load_json(POLICIES / "metrics-policy.json", {})
    return value if isinstance(value, dict) else {}


def metric_value_errors(name: str, value: Any, policy: dict[str, Any], label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, dict):
        return [f"{label} metric {name} must be an evidence object when claimed"]
    required = policy.get(name, {}).get("required_evidence", [])
    errors = []
    for key in required:
        if not non_empty(value.get(key)):
            errors.append(f"{label} metric {name} missing evidence field: {key}")
    return errors


def print_errors(errors: list[str], warnings: list[str] | None = None) -> int:
    warnings = warnings or []
    for warning in warnings:
        print(f"WARN  {warning}")
    for error in errors:
        print(f"ERROR {error}")
    print(f"DONE  errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


def validate_json_state() -> list[str]:
    errors: list[str] = []
    for path in sorted(STATE.glob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel(path)} is not valid JSON: {exc.msg}")
    for path in sorted(STATE.glob("*.jsonl")):
        _, read_errors = read_jsonl(path)
        errors.extend(read_errors)
    return errors


def load_schema(name: str) -> tuple[dict[str, Any] | None, list[str]]:
    path = SCHEMA / name
    if not path.exists():
        return None, [f"missing schema: {rel(path)}"]
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{rel(path)} is not valid JSON: {exc.msg}"]
    if not isinstance(schema, dict):
        return None, [f"{rel(path)} must contain a JSON object"]
    return schema, []


def validate_schemas() -> list[str]:
    names = [
        "project.schema.json",
        "census.schema.json",
        "file-record.schema.json",
        "zone.schema.json",
        "agent-task.schema.json",
        "finding.schema.json",
        "packet.schema.json",
        "validation.schema.json",
        "metric.schema.json",
        "lock.schema.json",
    ]
    errors: list[str] = []
    for name in names:
        _, schema_errors = load_schema(name)
        errors.extend(schema_errors)
    return errors


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return True


def validate_schema_value(schema: dict[str, Any], value: Any, label: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        if not any(isinstance(item, str) and type_matches(value, item) for item in expected_type):
            errors.append(f"{label} must be one of types: {', '.join(str(item) for item in expected_type)}")
            return errors
    elif isinstance(expected_type, str) and not type_matches(value, expected_type):
        errors.append(f"{label} must be type {expected_type}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(f"{label} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label} must be one of: {', '.join(str(item) for item in schema['enum'])}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{label} missing required field: {key}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    errors.extend(validate_schema_value(child_schema, value[key], f"{label}.{key}"))
    if isinstance(value, list) and isinstance(schema.get("items"), dict):
        item_schema = schema["items"]
        for index, item in enumerate(value):
            errors.extend(validate_schema_value(item_schema, item, f"{label}[{index}]"))
    return errors


def validate_json_file_with_schema(filename: str, schema_name: str) -> list[str]:
    schema, errors = load_schema(schema_name)
    if errors or schema is None:
        return errors
    path = state(filename)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{rel(path)} is not valid JSON: {exc.msg}"]
    return validate_schema_value(schema, value, rel(path))


def validate_json_array_with_schema(filename: str, key: str, schema_name: str) -> list[str]:
    schema, errors = load_schema(schema_name)
    if errors or schema is None:
        return errors
    path = state(filename)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{rel(path)} is not valid JSON: {exc.msg}"]
    if not isinstance(value, dict) or not isinstance(value.get(key), list):
        return [f"{rel(path)} must contain array field: {key}"]
    result: list[str] = []
    for index, item in enumerate(value[key]):
        result.extend(validate_schema_value(schema, item, f"{rel(path)}.{key}[{index}]"))
    return result


def validate_jsonl_with_schema(filename: str, schema_name: str) -> list[str]:
    schema, errors = load_schema(schema_name)
    if errors or schema is None:
        return errors
    path = state(filename)
    records, read_errors = read_jsonl(path)
    result = list(read_errors)
    for index, record in enumerate(records, 1):
        result.extend(validate_schema_value(schema, record, f"{rel(path)}:{index}"))
    return result


def validate_state_schemas() -> list[str]:
    errors: list[str] = []
    errors.extend(validate_json_file_with_schema("project.json", "project.schema.json"))
    errors.extend(validate_json_file_with_schema("census.json", "census.schema.json"))
    errors.extend(validate_json_array_with_schema("zones.json", "zones", "zone.schema.json"))
    errors.extend(validate_jsonl_with_schema("file-tree.jsonl", "file-record.schema.json"))
    errors.extend(validate_jsonl_with_schema("agent-tasks.jsonl", "agent-task.schema.json"))
    errors.extend(validate_jsonl_with_schema("findings.jsonl", "finding.schema.json"))
    errors.extend(validate_jsonl_with_schema("packets.jsonl", "packet.schema.json"))
    errors.extend(validate_jsonl_with_schema("validations.jsonl", "validation.schema.json"))
    errors.extend(validate_jsonl_with_schema("locks.jsonl", "lock.schema.json"))
    return errors


def validate_policy_drift() -> list[str]:
    errors: list[str] = []
    lifecycle = load_json(POLICIES / "lifecycle.json", {})
    if isinstance(lifecycle, dict):
        if set(lifecycle.get("finding_statuses", [])) != FINDING_STATUSES:
            errors.append("policies/lifecycle.json finding_statuses drift from kit.py")
        if set(lifecycle.get("packet_statuses", [])) != PACKET_STATUSES:
            errors.append("policies/lifecycle.json packet_statuses drift from kit.py")
        if set(lifecycle.get("specialist_roles", [])) != set(ROLES):
            errors.append("policies/lifecycle.json specialist_roles drift from kit.py")
    metrics_policy = load_json(POLICIES / "metrics-policy.json", {})
    if isinstance(metrics_policy, dict) and set(metrics_policy.keys()) != set(METRICS):
        errors.append("policies/metrics-policy.json keys drift from kit.py metrics")
    finding_schema, schema_errors = load_schema("finding.schema.json")
    errors.extend(schema_errors)
    if finding_schema:
        status_enum = finding_schema.get("properties", {}).get("status", {}).get("enum", [])
        if set(status_enum) != FINDING_STATUSES:
            errors.append("schema/finding.schema.json status enum drifts from kit.py")
    packet_schema, schema_errors = load_schema("packet.schema.json")
    errors.extend(schema_errors)
    if packet_schema:
        status_enum = packet_schema.get("properties", {}).get("status", {}).get("enum", [])
        if set(status_enum) != PACKET_STATUSES:
            errors.append("schema/packet.schema.json status enum drifts from kit.py")
    task_schema, schema_errors = load_schema("agent-task.schema.json")
    errors.extend(schema_errors)
    if task_schema:
        role_enum = task_schema.get("properties", {}).get("role", {}).get("enum", [])
        if set(role_enum) != set(ROLES):
            errors.append("schema/agent-task.schema.json role enum drifts from kit.py")
    return errors


def validate_managed_gitignore() -> list[str]:
    path = PROJECT_ROOT / ".gitignore"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if GITIGNORE_START not in text and GITIGNORE_END not in text:
        return []
    errors: list[str] = []
    if text.count(GITIGNORE_START) != 1 or text.count(GITIGNORE_END) != 1:
        return ["managed .gitignore block must have exactly one start and one end marker"]
    start = text.index(GITIGNORE_START) + len(GITIGNORE_START)
    end = text.index(GITIGNORE_END)
    entries = [line.strip() for line in text[start:end].splitlines() if line.strip()]
    expected = f"{HERE.name}/"
    if expected not in entries:
        errors.append(f"managed .gitignore block must include {expected}")
    if len(entries) != len(set(entries)):
        errors.append("managed .gitignore block contains duplicate entries")
    return errors


def strip_managed_ignore_block(text: str) -> str | None:
    if GITIGNORE_START not in text and GITIGNORE_END not in text:
        return text
    if text.count(GITIGNORE_START) != 1 or text.count(GITIGNORE_END) != 1:
        return None
    start = text.index(GITIGNORE_START)
    end = text.index(GITIGNORE_END) + len(GITIGNORE_END)
    while end < len(text) and text[end] in {"\r", "\n"}:
        end += 1
    return text[:start] + text[end:]


def git_head_file(path: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "show", f"HEAD:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def managed_gitignore_only_change(path: str) -> bool:
    if path != ".gitignore":
        return False
    current_path = PROJECT_ROOT / ".gitignore"
    if not current_path.exists():
        return False
    current = current_path.read_text(encoding="utf-8")
    stripped_current = strip_managed_ignore_block(current)
    if stripped_current is None:
        return False
    stripped_base = strip_managed_ignore_block(git_head_file(".gitignore"))
    if stripped_base is None:
        stripped_base = git_head_file(".gitignore")
    return stripped_current.strip() == stripped_base.strip()


def doctor(_: argparse.Namespace) -> int:
    ensure_runtime()
    errors: list[str] = []
    warnings: list[str] = []
    if sys.version_info < MIN_PYTHON:
        errors.append(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required")
    if HERE.name != KIT_DIR_NAME:
        warnings.append(f"kit directory is {HERE.name}; expected {KIT_DIR_NAME}")
    for directory in [STATE, REPORTS, SCHEMA, HERE / "policies", HERE / "templates"]:
        if not directory.is_dir():
            errors.append(f"missing runtime directory: {rel(directory)}")
    errors.extend(validate_schemas())
    errors.extend(validate_state_schemas())
    errors.extend(validate_policy_drift())
    errors.extend(validate_json_state())
    errors.extend(validate_managed_gitignore())
    if not (PROJECT_ROOT / ".git").exists():
        warnings.append("project does not contain .git; packet scope enforcement requires git")
    if not errors:
        print("OK    runtime directories, schemas, and state files are valid")
    return print_errors(errors, warnings)


def parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in norm(path).split("/") if part and part != ".")


def is_test(path: str) -> bool:
    path_parts = parts(path)
    name = path_parts[-1].lower() if path_parts else ""
    return (
        any(part.lower() in {"test", "tests", "spec", "specs", "__tests__"} for part in path_parts)
        or name.startswith("test_")
        or name.endswith(("_test.py", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx", "_test.go", "test.rs"))
    )


def is_generated(path: str) -> bool:
    path_parts = parts(path)
    name = path_parts[-1].lower() if path_parts else ""
    return bool({part.lower() for part in path_parts} & GENERATED_DIRS) or ".min." in name or name.endswith((".generated.ts", ".pb.go"))


def is_vendor(path: str) -> bool:
    return bool({part.lower() for part in parts(path)} & VENDOR_DIRS)


def loc_for(path: Path) -> tuple[int, bool]:
    try:
        data = path.read_bytes()
    except OSError:
        return 0, False
    if b"\0" in data[:4096]:
        return 0, False
    text = data.decode("utf-8", errors="ignore")
    return len(text.splitlines()), True


def skip_dir(path: Path) -> bool:
    return (path.name == HERE.name and path.resolve() == HERE) or path.name in SKIP_DIRS or path.is_symlink()


def tool_info(paths: list[str]) -> dict[str, Any]:
    names = {PurePosixPath(path).name for path in paths}
    available = {tool: shutil.which(tool) is not None for tool in ["python", "pytest", "node", "npm", "pnpm", "yarn", "go", "cargo", "mvn", "gradle", "make", "cmake"]}
    commands: list[dict[str, Any]] = []
    if {"pyproject.toml", "setup.py", "pytest.ini", "tox.ini"} & names or any(PurePosixPath(path).name.startswith("requirements") for path in paths):
        commands.append({"name": "python tests", "command": "python -m pytest", "available": available["python"]})
    if "package.json" in names:
        command = "pnpm test" if "pnpm-lock.yaml" in names else "yarn test" if "yarn.lock" in names else "npm test"
        commands.append({"name": "node tests", "command": command, "available": available["npm"] or available["pnpm"] or available["yarn"]})
    if "go.mod" in names:
        commands.append({"name": "go tests", "command": "go test ./...", "available": available["go"]})
    if "Cargo.toml" in names:
        commands.append({"name": "rust tests", "command": "cargo test", "available": available["cargo"]})
    if "pom.xml" in names:
        commands.append({"name": "maven tests", "command": "mvn test", "available": available["mvn"]})
    if "build.gradle" in names or "build.gradle.kts" in names:
        commands.append({"name": "gradle tests", "command": "gradle test", "available": available["gradle"]})
    if "Makefile" in names:
        commands.append({"name": "make tests", "command": "make test", "available": available["make"]})
    return {"available_tools": available, "commands": commands}


def collect_files() -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        kept = []
        for directory_name in dirs:
            directory = root_path / directory_name
            if skip_dir(directory):
                skipped.append(rel(directory))
            else:
                kept.append(directory_name)
        dirs[:] = kept
        for filename in files:
            path = root_path / filename
            if path.is_symlink() or not path.is_file():
                continue
            relative = rel(path)
            if relative == HERE.name or relative.startswith(HERE.name + "/"):
                continue
            loc, text = loc_for(path)
            signals: list[str] = []
            language = LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "unknown")
            name = PurePosixPath(relative).name
            if language not in {"unknown", "json", "yaml", "toml", "markdown", "xml"}:
                signals.append("source")
            if name in PACKAGE_MANIFESTS:
                signals.append("package-manifest")
            if name in LOCKFILES:
                signals.append("lockfile")
            if is_test(relative):
                signals.append("test")
            if is_generated(relative):
                signals.append("generated")
            if is_vendor(relative):
                signals.append("vendor")
            records.append({"path": relative, "language": language, "bytes": path.stat().st_size, "loc": loc if text else 0, "is_test": is_test(relative), "is_generated": is_generated(relative), "is_vendor": is_vendor(relative), "zone": None, "signals": sorted(set(signals))})
    return sorted(records, key=lambda item: item["path"]), sorted(set(skipped))


def census(_: argparse.Namespace) -> int:
    ensure_runtime()
    records, skipped = collect_files()
    write_jsonl(state("file-tree.jsonl"), records)
    lang: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "loc": 0})
    by_dir: Counter[str] = Counter()
    for record in records:
        lang[record["language"]]["files"] += 1
        lang[record["language"]]["loc"] += int(record["loc"])
        path_parts = parts(record["path"])
        by_dir[path_parts[0] if len(path_parts) > 1 else "."] += int(record["loc"])
    paths = [record["path"] for record in records]
    manifests = [path for path in paths if PurePosixPath(path).name in PACKAGE_MANIFESTS]
    locks = [path for path in paths if PurePosixPath(path).name in LOCKFILES]
    tests = [record["path"] for record in records if record["is_test"]]
    configs = [path for path in paths if PurePosixPath(path).name in CONFIG_NAMES or path.startswith(".github/")]
    entrypoints = [path for path in paths if PurePosixPath(path).name.lower() in {"main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs", "server.js", "server.ts"}]
    tools = tool_info(paths)
    contract_candidates = contract_candidates_from_records(records)
    largest = sorted(records, key=lambda item: (int(item["loc"]), int(item["bytes"])), reverse=True)[:25]
    doc = {
        "kit_version": KIT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_by": "kit.py census",
        "summary": {"total_files": len(records), "total_loc": sum(int(record["loc"]) for record in records), "test_files": len(tests), "package_manifests": len(manifests), "lockfiles": len(locks)},
        "language_mix": dict(sorted(lang.items())),
        "loc_by_directory": dict(sorted(by_dir.items())),
        "largest_files": [{"path": item["path"], "loc": item["loc"], "bytes": item["bytes"], "language": item["language"]} for item in largest],
        "package_manifests": manifests,
        "lockfiles": locks,
        "likely_generated_vendor_cache_folders": skipped,
        "test_files": tests,
        "config_files": configs,
        "entrypoint_candidates": entrypoints,
        "contract_candidates": contract_candidates,
        "detected_tools": tools,
    }
    save_json(state("census.json"), doc)
    save_json(state("contracts.json"), {"contracts": contract_candidates})
    save_json(state("tests.json"), {"test_files": tests, "commands": tools["commands"]})
    save_json(state("metrics.json"), {"metrics": {"census": doc["summary"], "language_mix": doc["language_mix"]}})
    print(f"OK    wrote {len(records)} file records")
    return 0


def zone_key(path: str) -> str:
    path_parts = parts(path)
    if not path_parts:
        return "root"
    if len(path_parts) >= 2 and path_parts[0] in ZONE_BOUNDARIES:
        return f"{path_parts[0]}/{path_parts[1]}"
    if len(path_parts) >= 2 and path_parts[0] in {"src", "lib", "app", "internal"}:
        return f"{path_parts[0]}/{path_parts[1]}"
    return "root" if len(path_parts) == 1 else path_parts[0]


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower() or "root"


def agent_count(files: int, loc: int) -> int:
    if loc >= 75000 or files >= 600:
        return 4
    if loc >= 35000 or files >= 300:
        return 3
    if loc >= 12000 or files >= 120:
        return 2
    return 1


def zones_suggest(_: argparse.Namespace) -> int:
    ensure_runtime()
    records, errors = read_jsonl(state("file-tree.jsonl"))
    if errors:
        return print_errors(errors)
    if not records:
        census(argparse.Namespace())
        records, _ = read_jsonl(state("file-tree.jsonl"))
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if not record.get("is_vendor"):
            groups[zone_key(str(record.get("path", "")))].append(record)
    zones = []
    for key, items in sorted(groups.items()):
        loc = sum(int(item.get("loc") or 0) for item in items)
        files = len(items)
        zone_id = "Z-" + slug(key)
        tests = [item["path"] for item in items if item.get("is_test")]
        entrypoints = [item["path"] for item in items if PurePosixPath(str(item["path"])).name.lower() in {"main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs", "server.js", "server.ts"}]
        risk_notes = []
        if loc >= 35000 or files >= 300:
            risk_notes.append("oversized-zone")
        if any(PurePosixPath(str(item["path"])).name in LOCKFILES for item in items):
            risk_notes.append("dependency-metadata")
        for item in items:
            item["zone"] = zone_id
        zones.append({"id": zone_id, "name": key, "globs": ["*"] if key == "root" else [key.rstrip("/") + "/**"], "loc": loc, "files": files, "entrypoints": entrypoints, "tests": tests[:100], "risk_notes": risk_notes, "recommended_agents": agent_count(files, loc)})
    save_json(state("zones.json"), {"zones": zones})
    write_jsonl(state("file-tree.jsonl"), records)
    print(f"OK    wrote {len(zones)} zones")
    return 0


def contract_candidates_from_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(path: str, kind: str, notes: list[str] | None = None) -> None:
        key = (path, kind)
        if key in seen:
            return
        seen.add(key)
        candidates.append({"path": path, "kind": kind, "notes": notes or []})

    for record in records:
        path = str(record.get("path", ""))
        path_parts = parts(path)
        name = PurePosixPath(path).name.lower()
        lowered = path.lower()
        if path in {"README.md", "AGENTS.md"} or (path_parts and path_parts[0] in {"docs", "proto", "schema", "schemas"}) or name in {"openapi.yaml", "openapi.json"}:
            add(path, "authority-or-contract-candidate")
        if name in {"package.json", "pyproject.toml", "setup.py", "go.mod", "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts"}:
            add(path, "package-or-build-contract-candidate")
        if name in CONFIG_NAMES or name.startswith(".env") or "config" in lowered:
            add(path, "config-contract-candidate")
        if name in {"index.ts", "index.js", "__init__.py", "lib.rs", "mod.rs"}:
            add(path, "public-export-candidate")
        if name.startswith("main.") or name.startswith("cli.") or (path_parts and path_parts[0] in {"bin", "cmd"}):
            add(path, "cli-entrypoint-candidate")
        if name.split(".", 1)[0] in {"routes", "pages", "api", "controllers", "handlers", "endpoints"} or any(part.lower() in {"routes", "pages", "api", "controllers", "handlers", "endpoints"} for part in path_parts):
            add(path, "route-or-handler-candidate")
    return sorted(candidates, key=lambda item: (item["kind"], item["path"]))


def dedupe_limited(items: list[str], limit: int) -> list[str]:
    clean: list[str] = []
    for item in items:
        normalized = norm(item)
        if normalized not in clean:
            clean.append(normalized)
        if len(clean) >= limit:
            break
    return clean


def authority_doc_candidates(records: list[dict[str, Any]]) -> list[str]:
    candidates: list[str] = []
    for authority in ["AGENTS.md", "README.md", "CONTRIBUTING.md"]:
        if (PROJECT_ROOT / authority).exists():
            candidates.append(authority)
    for record in records:
        path = str(record.get("path", ""))
        name = PurePosixPath(path).name.lower()
        if not path.startswith("docs/"):
            continue
        if name in {"readme.md", "architecture.md", "api.md", "contracts.md", "testing.md"} or any(token in name for token in ["architecture", "contract", "api", "testing", "integration"]):
            candidates.append(path)
    return dedupe_limited(candidates, 10)


def context_reads_for_zone(zone: dict[str, Any], records: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    zone_id = zone.get("id")
    required: list[str] = authority_doc_candidates(records)[:4]
    optional: list[str] = authority_doc_candidates(records)[4:]
    census_doc = load_json(state("census.json"), {})
    if isinstance(census_doc, dict):
        required.extend((census_doc.get("package_manifests", []) or [])[:8])
        optional.extend((census_doc.get("config_files", []) or [])[:12])
    required.extend((zone.get("tests") or [])[:12])
    required.extend(record["path"] for record in records if record.get("zone") == zone_id and "test" in (record.get("signals") or []))
    contracts = load_json(state("contracts.json"), {"contracts": []})
    contract_records = contracts.get("contracts", []) if isinstance(contracts, dict) else []
    if not contract_records:
        contract_records = contract_candidates_from_records(records)
    optional.extend(str(item.get("path")) for item in contract_records if item.get("path"))
    return dedupe_limited(required, 24), dedupe_limited(optional, 32)


def roles_for(zone: dict[str, Any]) -> list[str]:
    loc = int(zone.get("loc") or 0)
    files = int(zone.get("files") or 0)
    risk_notes = set(zone.get("risk_notes") or [])
    roles = ["architecture-auditor", "dead-code-auditor", "test-coverage-auditor", "duplicate-logic-auditor", "integration-auditor"]
    if "dependency-metadata" in set(zone.get("risk_notes") or []):
        roles.append("dependency-auditor")
    if loc >= 12000 or files >= 120 or "oversized-zone" in risk_notes:
        roles.append("performance-auditor")
    if risk_notes:
        roles.append("domain-risk-auditor")
    if loc >= 12000 or files >= 120:
        roles.append("todo-assumption-auditor")
    unique = []
    for role in roles:
        if role not in unique:
            unique.append(role)
    return unique


def recommended_agent_total(zones: list[dict[str, Any]]) -> int:
    total_loc = sum(int(zone.get("loc") or 0) for zone in zones)
    total_files = sum(int(zone.get("files") or 0) for zone in zones)
    high_risk = sum(1 for zone in zones if zone.get("risk_notes"))
    if total_loc >= 150000 or total_files >= 1200:
        base = 8
    elif total_loc >= 75000 or total_files >= 600:
        base = 6
    elif total_loc >= 35000 or total_files >= 300:
        base = 4
    elif total_loc >= 12000 or total_files >= 120:
        base = 3
    elif len(zones) >= 12 or total_files >= 40:
        base = 2
    else:
        base = 1
    return min(12, max(1, base + min(high_risk, 2)))


def assign_zones_to_slots(zones: list[dict[str, Any]], slots: int) -> list[list[dict[str, Any]]]:
    assignments: list[list[dict[str, Any]]] = [[] for _ in range(slots)]
    weights = [0 for _ in range(slots)]
    for zone in sorted(zones, key=lambda item: (int(item.get("loc") or 0), int(item.get("files") or 0)), reverse=True):
        slot = min(range(slots), key=lambda index: weights[index])
        assignments[slot].append(zone)
        weights[slot] += int(zone.get("loc") or 0) + int(zone.get("files") or 0) * 25
    return assignments


def agents_plan(_: argparse.Namespace) -> int:
    ensure_runtime()
    zones = load_json(state("zones.json"), {"zones": []}).get("zones", [])
    if not zones:
        zones_suggest(argparse.Namespace())
        zones = load_json(state("zones.json"), {"zones": []}).get("zones", [])
    records, _ = read_jsonl(state("file-tree.jsonl"))
    slots = recommended_agent_total(zones)
    tasks = []
    for index, assigned_zones in enumerate(assign_zones_to_slots(zones, slots), start=1):
        required_reads: list[str] = []
        optional_reads: list[str] = []
        allowed_reads: list[str] = []
        role_queue: list[dict[str, Any]] = []
        for zone in assigned_zones:
            zone_required, zone_optional = context_reads_for_zone(zone, records)
            required_reads.extend(zone_required)
            optional_reads.extend(zone_optional)
            allowed_reads.extend(zone.get("globs") or [])
            role_queue.append({"zone": zone["id"], "roles": roles_for(zone)})
        primary_role = role_queue[0]["roles"][0] if role_queue else "architecture-auditor"
        tasks.append({"id": f"TASK-{index:03d}", "role": primary_role, "zone": ",".join(zone["id"] for zone in assigned_zones), "zones": [zone["id"] for zone in assigned_zones], "objective": "Work the role_queue for assigned zones with evidence only; do not edit source files.", "allowed_reads": dedupe_limited(allowed_reads, 80), "required_reads": dedupe_limited(required_reads, 40), "optional_reads": dedupe_limited(optional_reads, 60), "role_queue": role_queue, "allowed_writes": [f"{HERE.name}/state/findings.jsonl"], "required_outputs": ["findings", "zone_summary"], "forbidden_actions": ["source_edit", "dependency_change", "delete_code"], "recommended_agent_slot": index, "max_context_files": min(sum(int(zone.get("files") or 0) for zone in assigned_zones) + 40, 240), "max_context_tokens": 120000, "status": "open"})
    write_jsonl(state("agent-tasks.jsonl"), tasks)
    write_reports()
    print(f"OK    wrote {len(tasks)} agent-slot tasks")
    return 0


def deletion_claim(finding: dict[str, Any]) -> bool:
    text = " ".join(str(finding.get(key, "")) for key in ["title", "claim", "recommendation"])
    return bool(re.search(r"\b(delete|deletion|remove|removal|safe to delete|removable)\b", text, re.IGNORECASE))


def validate_finding(finding: dict[str, Any], validations: list[dict[str, Any]] | None = None) -> list[str]:
    fid = finding.get("id", "<unknown>")
    errors = []
    for key in ["id", "status", "category", "zone", "title", "claim", "evidence", "counterevidence", "affected_files", "metrics", "recommendation", "created_by", "created_at"]:
        if key not in finding:
            errors.append(f"finding {fid} missing required field: {key}")
    status = finding.get("status")
    if status not in FINDING_STATUSES:
        errors.append(f"finding {fid} has unknown status: {status}")
    for key in ["evidence", "counterevidence", "affected_files"]:
        if key in finding and not isinstance(finding[key], list):
            errors.append(f"finding {fid} {key} must be a list")
    metrics = finding.get("metrics")
    if not isinstance(metrics, dict):
        errors.append(f"finding {fid} metrics must be an object")
    else:
        metrics_policy = load_metrics_policy()
        required_metrics = list(metrics_policy.keys()) or METRICS
        for key in required_metrics:
            if key not in metrics:
                errors.append(f"finding {fid} metrics missing key: {key}")
            else:
                errors.extend(metric_value_errors(key, metrics[key], metrics_policy, f"finding {fid}"))
    if status in {"candidate", "approved", "implemented", "validated"}:
        if not non_empty(finding.get("claim")):
            errors.append(f"finding {fid} must include a concrete claim")
        if not non_empty(finding.get("evidence")):
            errors.append(f"finding {fid} cannot be {status} without evidence")
        if not non_empty(finding.get("counterevidence")):
            errors.append(f"finding {fid} must record counterevidence, uncertainty, or gaps")
    if status == "validated" and validations is not None:
        if not any(fid in item.get("related_findings", []) or item.get("finding") == fid for item in validations):
            errors.append(f"validated finding {fid} has no validation record")
    if finding.get("category") == "dead-code":
        dead = finding.get("dead_code")
        if not isinstance(dead, dict):
            errors.append(f"dead-code finding {fid} missing dead_code object")
            return errors
        if dead.get("classification") not in DEAD_CODE_CLASSES:
            errors.append(f"dead-code finding {fid} has invalid classification: {dead.get('classification')}")
        checks = dead.get("required_checks")
        if not isinstance(checks, dict):
            checks = {}
            errors.append(f"dead-code finding {fid} missing required_checks object")
        missing = [key for key in DEAD_CODE_CHECKS if not non_empty(checks.get(key))]
        if deletion_claim(finding) and missing:
            errors.append(f"dead-code finding {fid} recommends deletion without required evidence: {', '.join(missing)}")
        if missing and status not in {"candidate", "needs-evidence", "rejected", "superseded"}:
            errors.append(f"dead-code finding {fid} must be needs-evidence until checks are filled: {', '.join(missing)}")
    return errors


def findings_add(args: argparse.Namespace) -> int:
    ensure_runtime()
    try:
        finding = json.loads(Path(args.file).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR cannot read finding JSON: {exc}")
        return 1
    if not isinstance(finding, dict):
        print("ERROR finding file must contain an object")
        return 1
    errors = validate_finding(finding)
    if errors:
        return print_errors(errors)
    append_jsonl(state("findings.jsonl"), finding)
    print(f"OK    appended finding {finding.get('id')}")
    return 0


def findings_validate(_: argparse.Namespace) -> int:
    ensure_runtime()
    findings, errors = read_jsonl(state("findings.jsonl"))
    validations, validation_errors = read_jsonl(state("validations.jsonl"))
    errors.extend(validation_errors)
    seen = set()
    for finding in findings:
        fid = str(finding.get("id", ""))
        if fid in seen:
            errors.append(f"duplicate finding id: {fid}")
        seen.add(fid)
        errors.extend(validate_finding(finding, validations))
    for error in errors:
        print(f"ERROR {error}")
    print(f"DONE  findings={len(findings)} errors={len(errors)}")
    return 1 if errors else 0


def next_id(path: Path, prefix: str) -> str:
    records, _ = read_jsonl(path)
    highest = 0
    for record in records:
        match = re.fullmatch(re.escape(prefix) + r"-(\d+)", str(record.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def reconcile(_: argparse.Namespace) -> int:
    ensure_runtime()
    findings, errors = read_jsonl(state("findings.jsonl"))
    if errors:
        return print_errors(errors)
    changed = 0
    by_key: dict[str, dict[str, Any]] = {}
    for finding in findings:
        key = json.dumps([finding.get("category"), sorted(finding.get("affected_files") or []), finding.get("claim")], sort_keys=True)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = finding
            continue
        weaker = finding if len(finding.get("evidence") or []) <= len(existing.get("evidence") or []) else existing
        stronger = existing if weaker is finding else finding
        if weaker.get("status") not in {"superseded", "rejected"}:
            weaker["status"] = "superseded"
            weaker["superseded_by"] = stronger.get("id")
            changed += 1
        by_key[key] = stronger
    for finding in findings:
        if finding.get("category") == "dead-code" and finding.get("status") == "approved" and validate_finding(finding):
            finding["status"] = "needs-evidence"
            changed += 1
    if changed:
        write_jsonl(state("findings.jsonl"), findings)
    append_jsonl(state("decisions.jsonl"), {"id": next_id(state("decisions.jsonl"), "DEC"), "type": "reconcile", "changed_records": changed, "created_at": now()})
    print(f"OK    reconcile complete; changed_records={changed}")
    return 0


def packets_create(args: argparse.Namespace) -> int:
    ensure_runtime()
    findings, errors = read_jsonl(state("findings.jsonl"))
    if errors:
        return print_errors(errors)
    finding = next((item for item in findings if item.get("id") == args.finding), None)
    if not finding:
        print(f"ERROR finding not found: {args.finding}")
        return 1
    metrics = finding.get("metrics") if isinstance(finding.get("metrics"), dict) else {}
    risk_metric = metrics.get("risk_score")
    risk_score = risk_metric.get("risk_level") if isinstance(risk_metric, dict) else risk_metric
    packet = {
        "id": next_id(state("packets.jsonl"), "PKT"),
        "status": "draft",
        "related_findings": [finding.get("id")],
        "objective": finding.get("recommendation") or finding.get("claim") or "Implement approved finding.",
        "allowed_files": [norm(path) for path in finding.get("affected_files") or []],
        "forbidden_files": [],
        "dependency_files": [],
        "generated_files": [],
        "docs_files": [],
        "public_contracts": finding.get("contracts_touched") or [],
        "behavioral_parity_requirements": {"inputs_compatible": [], "outputs_compatible": [], "error_behavior_compatible": [], "performance_expectations": [], "known_acceptable_differences": []},
        "validation_commands": [],
        "rollback_plan": [],
        "risk_score": risk_score,
        "human_approval": None,
        "durable_knowledge_decisions": [],
        "created_at": now(),
    }
    append_jsonl(state("packets.jsonl"), packet)
    print(f"OK    created packet {packet['id']}")
    return 0


def packet_has_result(packet_id: str, validations: list[dict[str, Any]]) -> bool:
    for validation in validations:
        if validation.get("packet") != packet_id and packet_id not in validation.get("related_packets", []):
            continue
        commands = validation.get("commands")
        if isinstance(commands, list):
            for command in commands:
                if isinstance(command, dict) and non_empty(command.get("command")) and command.get("actual_result") is not None:
                    return True
    return False


def validate_packet(packet: dict[str, Any], validations: list[dict[str, Any]]) -> list[str]:
    pid = packet.get("id", "<unknown>")
    errors = []
    for key in ["id", "status", "related_findings", "objective", "allowed_files", "forbidden_files", "public_contracts", "behavioral_parity_requirements", "validation_commands", "rollback_plan", "risk_score", "human_approval"]:
        if key not in packet:
            errors.append(f"packet {pid} missing required field: {key}")
    status = packet.get("status")
    if status not in PACKET_STATUSES:
        errors.append(f"packet {pid} has unknown status: {status}")
    for key in ["related_findings", "allowed_files", "forbidden_files", "public_contracts", "validation_commands", "rollback_plan"]:
        if key in packet and not isinstance(packet[key], list):
            errors.append(f"packet {pid} {key} must be a list")
    risk = packet.get("risk_score")
    if risk is not None and not isinstance(risk, int):
        errors.append(f"packet {pid} risk_score must be integer 1-5 or null")
    if isinstance(risk, int) and not 1 <= risk <= 5:
        errors.append(f"packet {pid} risk_score must be between 1 and 5")
    if status in IMPLEMENTATION_PACKET_STATUSES and not packet.get("allowed_files"):
        errors.append(f"{status} packet {pid} has no allowed_files")
    if status in IMPLEMENTATION_PACKET_STATUSES:
        parity = packet.get("behavioral_parity_requirements")
        if not isinstance(parity, dict):
            errors.append(f"{status} packet {pid} must state behavioral parity requirements")
        else:
            for key in ["inputs_compatible", "outputs_compatible", "error_behavior_compatible", "known_acceptable_differences"]:
                if key not in parity or not non_empty(parity.get(key)):
                    errors.append(f"{status} packet {pid} must state parity field: {key}")
        if not non_empty(packet.get("validation_commands")):
            errors.append(f"{status} packet {pid} must include validation commands or manual checks")
    if isinstance(risk, int) and risk >= 3 and status in {"in-progress", "implemented", "validated"} and not packet.get("related_findings"):
        errors.append(f"risk {risk} packet {pid} must be traceable to a finding")
    if risk == 4 and status in {"approved", "in-progress", "implemented", "validated"} and not non_empty(packet.get("human_approval")):
        errors.append(f"risk 4 packet {pid} requires human_approval")
    if risk == 5 and status in {"approved", "in-progress", "implemented", "validated"}:
        errors.append(f"risk 5 packet {pid} cannot be approved for direct implementation from the kit")
    if status in {"implemented", "validated"} and not packet_has_result(str(pid), validations):
        errors.append(f"implemented packet {pid} has no validation command result")
    return errors


def overlap_errors(packets: list[dict[str, Any]]) -> list[str]:
    owners: dict[str, str] = {}
    conflict_ok = {norm(path) for packet in packets if non_empty(packet.get("conflict_approval")) for path in packet.get("allowed_files") or []}
    errors = []
    for packet in packets:
        if packet.get("status") not in ACTIVE_PACKET_STATUSES:
            continue
        pid = str(packet.get("id"))
        for raw in packet.get("allowed_files") or []:
            path = norm(raw)
            if path in owners and path not in conflict_ok:
                errors.append(f"active packets {owners[path]} and {pid} both touch {path} without conflict approval")
            owners[path] = pid
    return errors


def load_packets() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    packets, packet_errors = read_jsonl(state("packets.jsonl"))
    validations, validation_errors = read_jsonl(state("validations.jsonl"))
    return packets, validations, packet_errors + validation_errors


def packets_validate(_: argparse.Namespace) -> int:
    ensure_runtime()
    packets, validations, errors = load_packets()
    seen = set()
    for packet in packets:
        pid = str(packet.get("id", ""))
        if pid in seen:
            errors.append(f"duplicate packet id: {pid}")
        seen.add(pid)
        errors.extend(validate_packet(packet, validations))
    errors.extend(overlap_errors(packets))
    for error in errors:
        print(f"ERROR {error}")
    print(f"DONE  packets={len(packets)} errors={len(errors)}")
    return 1 if errors else 0


def changed_files() -> tuple[list[str], str | None]:
    result = subprocess.run(["git", "-c", "core.excludesfile=", "-C", str(PROJECT_ROOT), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return [], (result.stderr or result.stdout or "git status failed").strip()
    changed = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = norm(path)
        if path != HERE.name and not path.startswith(HERE.name + "/"):
            changed.append(path)
    return sorted(set(changed)), None


def is_dependency(path: str) -> bool:
    name = PurePosixPath(path).name
    return name in PACKAGE_MANIFESTS or name in LOCKFILES or (name.startswith("requirements") and name.endswith(".txt"))


def is_doc(path: str) -> bool:
    return path.lower().endswith((".md", ".rst", ".adoc")) or path.lower().startswith("docs/")


def enforce_scope(packets: list[dict[str, Any]]) -> list[str]:
    changed, error = changed_files()
    if error:
        return ["packet scope enforcement requires git status: " + error]
    active = [packet for packet in packets if packet.get("status") in ACTIVE_PACKET_STATUSES]
    if not active:
        return [f"project files changed but there are zero active approved packets: {', '.join(changed)}"] if changed else []
    errors = overlap_errors(active)
    allowed = {norm(path) for packet in active for path in packet.get("allowed_files") or []}
    deps = {norm(path) for packet in active for path in packet.get("dependency_files") or []}
    generated = {norm(path) for packet in active for path in packet.get("generated_files") or []}
    docs = {norm(path) for packet in active for path in packet.get("docs_files") or []}
    durable = {norm(path) for packet in active for path in packet.get("durable_knowledge_decisions") or []}
    for path in changed:
        if managed_gitignore_only_change(path):
            continue
        if is_dependency(path):
            if path not in deps:
                errors.append(f"changed dependency file is not listed in packet dependency_files: {path}")
        elif is_generated(path):
            if path not in generated and path not in deps:
                errors.append(f"changed generated metadata is not listed in packet generated_files or dependency_files: {path}")
        elif is_doc(path):
            if path not in docs and path not in allowed and path not in durable:
                errors.append(f"changed docs file is not listed in packet docs_files, allowed_files, or durable knowledge decisions: {path}")
        elif path not in allowed:
            errors.append(f"changed project file outside active packet allowed_files: {path}")
    return errors


def validate(args: argparse.Namespace) -> int:
    ensure_runtime()
    errors = validate_schemas() + validate_json_state() + validate_state_schemas() + validate_policy_drift()
    findings, finding_errors = read_jsonl(state("findings.jsonl"))
    validations, validation_errors = read_jsonl(state("validations.jsonl"))
    packets, packet_validations, packet_errors = load_packets()
    errors.extend(finding_errors + validation_errors + packet_errors)
    for finding in findings:
        errors.extend(validate_finding(finding, validations))
    for packet in packets:
        errors.extend(validate_packet(packet, packet_validations))
    errors.extend(overlap_errors(packets))
    if args.enforce_packet:
        errors.extend(enforce_scope(packets))
    for error in errors:
        print(f"ERROR {error}")
    if not errors:
        print("OK    validation passed")
    print(f"DONE  errors={len(errors)} warnings=0")
    return 1 if errors else 0


def md_list(items: list[str], empty: str = "None detected.") -> str:
    return "\n".join(f"- `{item}`" for item in items) if items else empty


def write_reports() -> None:
    ensure_runtime()
    census_doc = load_json(state("census.json"), {})
    zones = load_json(state("zones.json"), {"zones": []}).get("zones", [])
    tasks, _ = read_jsonl(state("agent-tasks.jsonl"))
    findings, _ = read_jsonl(state("findings.jsonl"))
    packets, _ = read_jsonl(state("packets.jsonl"))
    tests = load_json(state("tests.json"), {"commands": []})
    summary = census_doc.get("summary", {}) if isinstance(census_doc, dict) else {}
    lines = ["# Agent Plan", "", f"Recommended discovery agents: {len(tasks)}", ""]
    for index, task in enumerate(tasks, 1):
        required = task.get("required_reads", [])
        optional = task.get("optional_reads", [])
        role_queue = task.get("role_queue", [])
        queue_summary = "; ".join(f"{item.get('zone')}: {', '.join(item.get('roles', []))}" for item in role_queue[:6])
        lines += [
            f"Agent {index}: {task.get('role')} across {len(task.get('zones', []))} zone(s)",
            f"- Files/globs: {', '.join('`' + item + '`' for item in task.get('allowed_reads', []))}",
            f"- Required reads: {', '.join('`' + item + '`' for item in required[:12]) if required else 'None'}",
            f"- Optional reads: {', '.join('`' + item + '`' for item in optional[:12]) if optional else 'None'}",
            f"- Role queue: {queue_summary or 'None'}",
            f"- Expected output: {', '.join(task.get('required_outputs', []))}",
            "",
        ]
    high_risk = [zone for zone in zones if zone.get("risk_notes")]
    lines += ["## High-risk zones", md_list([f"{zone.get('id')} ({', '.join(zone.get('risk_notes', []))})" for zone in high_risk]), "", "## Large files"]
    lines.append(md_list([f"{item.get('path')} ({item.get('loc')} LOC)" for item in (census_doc.get("largest_files", []) if isinstance(census_doc, dict) else [])[:10]]))
    lines += ["", "## Likely generated/vendor areas", md_list((census_doc.get("likely_generated_vendor_cache_folders", []) if isinstance(census_doc, dict) else [])[:20]), "", "## Detected test commands"]
    commands = tests.get("commands", []) if isinstance(tests, dict) else []
    lines += [f"- `{item.get('command')}`" for item in commands] if commands else ["None detected."]
    lines += ["", "## Suggested next step", "Ask the human/orchestrator how many discovery agents to spawn and which zones to assign."]
    (REPORTS / "agent-plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    def finding_risk(item: dict[str, Any]) -> int:
        risk = (item.get("metrics", {}) or {}).get("risk_score")
        if isinstance(risk, dict):
            raw = risk.get("risk_level")
            return raw if isinstance(raw, int) else 0
        return risk if isinstance(risk, int) else 0

    ranked = sorted(findings, key=finding_risk, reverse=True)
    lines = ["# Findings Ranked", ""]
    lines += [f"- `{item.get('id')}` [{item.get('status')}] risk={finding_risk(item)}: {item.get('title')}" for item in ranked] or ["No findings recorded."]
    (REPORTS / "findings-ranked.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    backlog = [packet for packet in packets if packet.get("status") in {"draft", "needs-approval", "approved"}]
    lines = ["# Implementation Backlog", ""]
    lines += [f"- `{packet.get('id')}` [{packet.get('status')}] risk={packet.get('risk_score')}: {packet.get('objective')}" for packet in backlog] or ["No implementation packets are ready."]
    (REPORTS / "implementation-backlog.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Final Report", "", "## Summary", f"- Files indexed: {summary.get('total_files', 0)}", f"- Zones: {len(zones)}", f"- Findings: {len(findings)}", f"- Packets: {len(packets)}", "", "## Validated Work"]
    validated_packets = [packet for packet in packets if packet.get("status") == "validated"]
    lines += [f"- `{packet.get('id')}`: {packet.get('objective')}" for packet in validated_packets] or ["No packets are marked validated."]
    lines += ["", "## Rollback", "Review packet rollback plans in `state/packets.jsonl` before deleting this kit."]
    (REPORTS / "final-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def report(_: argparse.Namespace) -> int:
    write_reports()
    print("OK    generated reports")
    return 0


def contracts_candidates(_: argparse.Namespace) -> int:
    ensure_runtime()
    records, _ = read_jsonl(state("file-tree.jsonl"))
    if not records:
        records, _ = collect_files()
    contracts = contract_candidates_from_records(records)
    save_json(state("contracts.json"), {"contracts": contracts})
    print(f"OK    wrote {len(contracts)} contract candidates")
    return 0


def locks_acquire(args: argparse.Namespace) -> int:
    ensure_runtime()
    locks, errors = read_jsonl(state("locks.jsonl"))
    if errors:
        return print_errors(errors)
    for lock in reversed(locks):
        if lock.get("scope") == args.scope:
            if lock.get("status") == "acquired":
                print(f"ERROR scope already locked: {args.scope}")
                return 1
            break
    record = {"id": next_id(state("locks.jsonl"), "LOCK"), "scope": args.scope, "status": "acquired", "owner": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown", "created_at": now()}
    append_jsonl(state("locks.jsonl"), record)
    print(f"OK    acquired lock {record['id']}")
    return 0


def locks_release(args: argparse.Namespace) -> int:
    ensure_runtime()
    append_jsonl(state("locks.jsonl"), {"id": next_id(state("locks.jsonl"), "LOCK"), "scope": args.scope, "status": "released", "owner": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown", "created_at": now()})
    print(f"OK    released lock for {args.scope}")
    return 0


def status(_: argparse.Namespace) -> int:
    ensure_runtime()
    census_doc = load_json(state("census.json"), {})
    zones = load_json(state("zones.json"), {"zones": []}).get("zones", [])
    findings, _ = read_jsonl(state("findings.jsonl"))
    packets, _ = read_jsonl(state("packets.jsonl"))
    tasks, _ = read_jsonl(state("agent-tasks.jsonl"))
    summary = census_doc.get("summary", {}) if isinstance(census_doc, dict) else {}
    print(f"files={summary.get('total_files', 0)} loc={summary.get('total_loc', 0)} zones={len(zones)} tasks={len(tasks)} findings={len(findings)} packets={len(packets)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Codebase Optimization Kit runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor").set_defaults(func=doctor)
    sub.add_parser("census").set_defaults(func=census)
    zones = sub.add_parser("zones").add_subparsers(dest="zones_command", required=True)
    zones.add_parser("suggest").set_defaults(func=zones_suggest)
    agents = sub.add_parser("agents").add_subparsers(dest="agents_command", required=True)
    agents.add_parser("plan").set_defaults(func=agents_plan)
    findings = sub.add_parser("findings").add_subparsers(dest="findings_command", required=True)
    finding_add = findings.add_parser("add")
    finding_add.add_argument("--file", required=True)
    finding_add.set_defaults(func=findings_add)
    findings.add_parser("validate").set_defaults(func=findings_validate)
    sub.add_parser("reconcile").set_defaults(func=reconcile)
    packets = sub.add_parser("packets").add_subparsers(dest="packets_command", required=True)
    packet_create = packets.add_parser("create")
    packet_create.add_argument("--finding", required=True)
    packet_create.set_defaults(func=packets_create)
    packets.add_parser("validate").set_defaults(func=packets_validate)
    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("--enforce-packet", action="store_true")
    validate_parser.set_defaults(func=validate)
    sub.add_parser("report").set_defaults(func=report)
    contracts = sub.add_parser("contracts").add_subparsers(dest="contracts_command", required=True)
    contracts.add_parser("candidates").set_defaults(func=contracts_candidates)
    locks = sub.add_parser("locks").add_subparsers(dest="locks_command", required=True)
    acquire = locks.add_parser("acquire")
    acquire.add_argument("--scope", required=True)
    acquire.set_defaults(func=locks_acquire)
    release = locks.add_parser("release")
    release.add_argument("--scope", required=True)
    release.set_defaults(func=locks_release)
    sub.add_parser("status").set_defaults(func=status)
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
