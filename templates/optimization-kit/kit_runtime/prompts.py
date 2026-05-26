"""Prompt rendering helpers for discovery agent tasks."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PROMPTS_DIR_NAME = "agent-prompts"


def task_prompt_filename(task_id: str) -> str:
    return f"{task_id}.md"


def format_list(items: list[Any], *, fallback: str = "- None") -> list[str]:
    clean = [str(item) for item in items if str(item).strip()]
    return [f"- {item}" for item in clean] if clean else [fallback]


def format_audit_queue(items: list[dict[str, Any]]) -> list[str]:
    if not items:
        return ["- None"]
    lines: list[str] = []
    for item in items:
        zone = item.get("zone", "<unknown-zone>")
        lanes = ", ".join(str(lane) for lane in (item.get("lanes") or [])) or "None"
        baseline = " baseline_first" if item.get("baseline_first") else ""
        lines.append(f"- {zone}: {lanes}{baseline}")
    return lines


def render_task_prompt(task: dict[str, Any], *, kit_dir_name: str = ".codebase-optimization-kit") -> str:
    task_id = str(task.get("id") or "TASK-UNKNOWN")
    output_path = f"{kit_dir_name}/state/task-findings/{task_id}.jsonl"
    zones = task.get("zones") or []
    required_reads = task.get("required_reads") or []
    optional_reads = task.get("optional_reads") or []
    allowed_reads = task.get("allowed_reads") or []
    audit_queue = task.get("audit_queue") or []
    required_outputs = task.get("required_outputs") or ["baseline_health_signals", "findings", "zone_summary"]

    lines = [
        f"# Discovery Prompt: {task_id}",
        "",
        f"Discovery pass {task_id} only.",
        "",
        "Read:",
        f"- {kit_dir_name}/AGENT.md",
        f"- {kit_dir_name}/policies/audit-criteria.json",
        f"- the {task_id} line from {kit_dir_name}/state/agent-tasks.jsonl",
        f"- required_reads from {task_id}",
        "",
        "Rules:",
        "- Do not edit project source.",
        f"- Do not edit {kit_dir_name}/state/findings.jsonl directly.",
        "- Only inspect allowed_reads, required_reads, and optional_reads from this task.",
        "- Run audit_queue lanes in order for each zone.",
        f"- Write any findings as valid JSONL to {output_path}",
        "",
        "Zones:",
        *format_list(zones),
        "",
        "Allowed Reads:",
        *format_list(allowed_reads),
        "",
        "Required Reads:",
        *format_list(required_reads),
        "",
        "Optional Reads:",
        *format_list(optional_reads),
        "",
        "Audit Queue:",
        *format_audit_queue(audit_queue),
        "",
        "Deliver:",
        *format_list(required_outputs),
        "- brief zone_summary in your response",
        "- baseline_health_signals in your response",
        f"- findings written to {output_path}",
        "",
    ]
    return "\n".join(lines)


def write_task_prompts(tasks: list[dict[str, Any]], state_dir: Path, *, kit_dir_name: str = ".codebase-optimization-kit") -> list[Path]:
    prompts_dir = state_dir / PROMPTS_DIR_NAME
    prompts_dir.mkdir(parents=True, exist_ok=True)
    for path in prompts_dir.glob("TASK-*.md"):
        path.unlink()
    (state_dir / "task-findings").mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for task in tasks:
        task_id = str(task.get("id") or "").strip()
        if not task_id:
            continue
        path = prompts_dir / task_prompt_filename(task_id)
        path.write_text(render_task_prompt(task, kit_dir_name=kit_dir_name), encoding="utf-8", newline="\n")
        written.append(path)
    return written
