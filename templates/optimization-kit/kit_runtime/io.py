"""Small IO/state helpers for the optimization kit runtime."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


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


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def norm(raw: str | Path) -> str:
    value = str(raw).replace("\\", "/").strip()
    value = re.sub(r"^\./+", "", value)
    parts = [part for part in PurePosixPath(value).parts if part not in {"", "."}]
    return PurePosixPath(*parts).as_posix() if parts else "."


def rel(path: Path, project_root: Path) -> str:
    try:
        return norm(path.relative_to(project_root))
    except ValueError:
        return str(path)


def state(state_dir: Path, name: str) -> Path:
    return state_dir / name


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def read_jsonl(path: Path, project_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
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
            errors.append(f"{rel(path, project_root)}:{line_no}: invalid JSONL record: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{rel(path, project_root)}:{line_no}: JSONL record must be an object")
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


def ensure_runtime(
    here: Path,
    project_root: Path,
    state_dir: Path,
    reports_dir: Path,
    schema_dir: Path,
    kit_version: str,
    schema_version: str,
) -> None:
    for directory in [state_dir, reports_dir, schema_dir, here / "policies", here / "templates"]:
        directory.mkdir(parents=True, exist_ok=True)
    for filename, default in JSON_DEFAULTS.items():
        path = state(state_dir, filename)
        if not path.exists():
            save_json(path, default)
    for filename in JSONL_FILES:
        path = state(state_dir, filename)
        if not path.exists():
            path.write_text("", encoding="utf-8", newline="\n")
    project = load_json(state(state_dir, "project.json"), {})
    if not isinstance(project, dict):
        project = {}
    project.setdefault("kit_version", kit_version)
    project.setdefault("schema_version", schema_version)
    project.setdefault("workspace_type", "temporary")
    project.setdefault("project_root", ".")
    project["target_dir"] = here.name
    project.setdefault("created_at", today())
    if project.get("created_at") == "YYYY-MM-DD":
        project["created_at"] = today()
    project.setdefault("source_of_truth", {"root_agents": "AGENTS.md", "project_readme": "README.md", "project_docs": []})
    project.setdefault("custom_finding_categories", [])
    save_json(state(state_dir, "project.json"), project)
