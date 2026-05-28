"""Prompt rendering helpers for discovery agent tasks."""

from __future__ import annotations

from pathlib import Path
from typing import Any


PROMPTS_DIR_NAME = "agent-prompts"

LANE_LOOKFORS = {
    "security-risk": "Existing secrets, exposed credentials, missing authz on a sensitive path. Evidence only; do not install scanners.",
    "correctness-edge-case": "Real failure paths on empty/null/None, missing keys, wrong types, large numbers, timezone/DST, Unicode, path separators, partial failures; data-integrity risks like non-atomic writes or duplicate IDs.",
    "performance-efficiency": "Algorithmic complexity, redundant loops, repeated I/O/DB/API calls, N+1, missing batching/caching, heavy serialization or re-parsing, slow build/test flows. State a measurable cost and a cheaper existing approach.",
    "resource-lifecycle": "Unclosed files/sockets/handles, memory leaks, unbounded queues/caches, missing timeout/cancellation/retry budget.",
    "concurrency-state-safety": "Race conditions, shared mutable state, non-atomic writes, lock ordering, async tasks without await/cancel handling. High blast radius: human approval required.",
    "error-handling-recovery": "Swallowed exceptions, broad except, silent fallback, lost root cause, bad rollback after partial write, unstructured errors that block diagnosis.",
    "reinvented-capability": "Hand-rolled parsers, retry, date/path/glob handling, validation, crypto, caching, diffing, or CLI parsing where a stdlib or already-available dependency is safer. Confirm the alternative exists.",
    "dependency-risk": "Unused, risky, or unpinned dependencies using existing lockfiles and manifests only.",
    "authority-drift": "Contradictions between existing docs, tests, schemas, and public contracts. Compare authorities only.",
    "type-contract-safety": "Unchecked input/output at CLI args, JSON schema, public API, plugin interface boundaries; unsafe casts and runtime data assumptions.",
    "dynamic-usage": "Reflection, registry, config, plugin, eval, exec paths; configuration footguns like cwd/platform dependence or path-separator mismatch.",
    "test-reliability": "Missing tests for a risky hotspot or edge case that can actually break, not the absence of tests in general.",
    "dead-code": "Code with no confirmed runtime path, gated by static, entrypoint, config, test, and contract checks.",
    "duplicate-logic": "Equivalent logic in multiple places with bounded normalized-block evidence; no new clone scanner.",
    "structural-quality": "Objective maintainability signals: LOC, branch counts, ownership concentration, coupling. Lowest priority.",
}

EXAMPLE_FINDING = (
    '{"id":"PERF-001","status":"candidate","category":"performance-efficiency",'
    '"primary_lane":"performance-efficiency","related_lanes":[],"zone":"Z-example",'
    '"title":"Repeated full re-parse of config on every request",'
    '"claim":"load_config() re-reads and parses settings.json on each call inside the request loop.",'
    '"evidence":["src/app/handler.py calls load_config() per request","load_config opens and json.loads settings.json each call"],'
    '"counterevidence":["Config could change at runtime; confirm a reload path is not required."],'
    '"evidence_fields":{"root_cause":"No caching of parsed config.",'
    '"hotspot_location":"src/app/handler.py request loop","cost_signal":"one file open + json parse per request",'
    '"cheaper_alternative":"parse once at startup or memoize with an mtime check"},'
    '"affected_files":["src/app/handler.py"],"contracts_touched":[],"tests_covering":[],'
    '"metrics":{"passing_tests":null,"behavioral_parity":null,"dependency_reduction":null,'
    '"duplicate_logic_reduction":null,"dead_code_confidence":null,"complexity_reduction":null,'
    '"risk_score":{"risk_level":2,"risk_reason":"Local internal change behind same output.",'
    '"approval_path":"Packet approval before implementation."},"reversibility":null},'
    '"recommendation":"Cache parsed config; verify outputs unchanged.","created_by":"agent-id","created_at":"YYYY-MM-DD"}'
)


def task_prompt_filename(task_id: str) -> str:
    return f"{task_id}.md"


def task_lanes(task: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    for item in task.get("audit_queue") or []:
        for lane in item.get("lanes") or []:
            if lane not in ordered:
                ordered.append(str(lane))
    return ordered


def format_lane_playbook(lanes: list[str]) -> list[str]:
    if not lanes:
        return ["- None"]
    return [f"- {lane}: {LANE_LOOKFORS.get(lane, 'Report concrete, evidence-backed issues only.')}" for lane in lanes]


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
        "- Run audit_queue lanes in order for each zone (value lanes come first).",
        "- Start from the required_reads hotspots; they are the largest source files and entrypoints in scope.",
        f"- Write any findings as valid JSONL to {output_path}",
        "",
        "Quality bar:",
        "- Report only a concrete, evidence-backed defect, measurable inefficiency, or real risk. Skip cosmetic style and subjective preference.",
        "- A TODO/FIXME comment is NOT a finding by itself. File it only when it marks a concrete defect, security risk, or measurable inefficiency, and then under the matching value lane (correctness-edge-case / performance-efficiency / security-risk), never as a standalone TODO report.",
        "- Intentional placeholders for planned features are out of scope. If you cannot show impact with evidence, do not file it.",
        "- Each finding must satisfy its lane's required_evidence and include counterevidence or a stated gap. Prefer fewer strong findings over many weak ones.",
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
        "Lane playbook (what to look for):",
        *format_lane_playbook(task_lanes(task)),
        "",
        "Example finding (copy this shape, one JSON object per line):",
        EXAMPLE_FINDING,
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
