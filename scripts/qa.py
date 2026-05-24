#!/usr/bin/env python3
"""Scripted QA fixtures for the codebase optimization kit runtime."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "optimization-kit"
INIT = ROOT / "scripts" / "init.py"
PYTHON = sys.executable


class QAError(AssertionError):
    pass


def run(command: list[str], cwd: Path, *, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != expect:
        detail = "\n".join(
            [
                "command: " + " ".join(command),
                f"cwd: {cwd}",
                f"expected: {expect}",
                f"actual: {result.returncode}",
                "stdout:",
                result.stdout,
                "stderr:",
                result.stderr,
            ]
        )
        raise QAError(detail)
    return result


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, record: dict[str, object]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")


def create_project(root: Path) -> Path:
    project = root / "project"
    project.mkdir()
    write(project / "README.md", "# Sample\n")
    write(project / "src" / "core" / "app.py", "def add(a, b):\n    return a + b\n")
    write(project / "src" / "core" / "routes.py", "ROUTES = ['/health']\n")
    write(project / "tests" / "test_app.py", "from src.core.app import add\n\ndef test_add():\n    assert add(1, 2) == 3\n")
    write(project / ".env.example", "APP_ENV=test\n")
    write(project / "package.json", "{\"scripts\":{\"test\":\"echo ok\"}}\n")
    write(project / "package-lock.json", "{}\n")
    run(["git", "init"], project)
    run(["git", "add", "README.md", "src/core/app.py", "src/core/routes.py", "tests/test_app.py", ".env.example", "package.json", "package-lock.json"], project)
    run(["git", "-c", "user.email=qa@example.com", "-c", "user.name=QA", "commit", "-m", "initial"], project)
    return project


def copy_kit(project: Path) -> Path:
    kit = project / ".codebase-optimization-kit"
    shutil.copytree(TEMPLATE, kit)
    return kit


def kit_cmd(kit: Path, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
    return run([PYTHON, str(kit / "kit.py"), *args], kit.parent, expect=expect)


def approved_packet(path: str = "src/core/app.py", **extra: object) -> dict[str, object]:
    packet: dict[str, object] = {
        "id": "PKT-001",
        "status": "approved",
        "related_findings": ["ARCH-001"],
        "objective": "Scoped internal change.",
        "allowed_files": [path],
        "forbidden_files": [],
        "dependency_files": [],
        "generated_files": [],
        "docs_files": [],
        "public_contracts": [],
        "behavioral_parity_requirements": {
            "inputs_compatible": ["No public inputs touched."],
            "outputs_compatible": ["No public outputs touched."],
            "error_behavior_compatible": ["No public error behavior touched."],
            "performance_expectations": [],
            "known_acceptable_differences": ["None."],
        },
        "validation_commands": [{"command": "manual: review scoped diff", "expected_result": "only packet files changed"}],
        "rollback_plan": [],
        "risk_score": 2,
        "human_approval": None,
        "durable_knowledge_decisions": [],
    }
    packet.update(extra)
    return packet


def finding(**extra: object) -> dict[str, object]:
    record: dict[str, object] = {
        "id": "ARCH-001",
        "status": "candidate",
        "category": "architecture",
        "zone": "Z-src-core",
        "title": "Example",
        "claim": "Example claim.",
        "evidence": [],
        "counterevidence": [],
        "affected_files": ["src/core/app.py"],
        "contracts_touched": [],
        "tests_covering": [],
        "metrics": {
            "passing_tests": None,
            "behavioral_parity": None,
            "dependency_reduction": None,
            "duplicate_logic_reduction": None,
            "dead_code_confidence": None,
            "complexity_reduction": None,
            "risk_score": 2,
            "reversibility": None,
        },
        "recommendation": "needs-evidence",
        "created_by": "qa",
        "created_at": "2026-05-24",
    }
    record.update(extra)
    return record


def qa_runtime() -> None:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        project = create_project(temp)
        kit = copy_kit(project)

        for relative in [
            "AGENT.md",
            "kit.py",
            "schema/finding.schema.json",
            "state/project.json",
            "policies/metrics-policy.json",
            "templates/packet.json",
            "reports/README.md",
        ]:
            if not (kit / relative).exists():
                raise QAError(f"missing installed runtime path: {relative}")
        if (kit / "state" / "findings.jsonl").exists():
            raise QAError("template should not ship empty findings.jsonl")

        kit_cmd(kit, "doctor")
        if not (kit / "state" / "findings.jsonl").exists():
            raise QAError("doctor did not create findings.jsonl")
        kit_cmd(kit, "census")
        kit_cmd(kit, "zones", "suggest")
        kit_cmd(kit, "agents", "plan")
        tasks = [(json.loads(line)) for line in (kit / "state" / "agent-tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        roles = {task["role"] for task in tasks}
        for role in {"architecture-auditor", "dead-code-auditor", "test-coverage-auditor", "duplicate-logic-auditor", "integration-auditor"}:
            if role not in roles:
                raise QAError(f"agents plan did not include role: {role}")
        if not any("README.md" in task.get("supporting_reads", []) for task in tasks):
            raise QAError("agent tasks missing authority supporting reads")
        if not any("package.json" in task.get("supporting_reads", []) for task in tasks):
            raise QAError("agent tasks missing manifest supporting reads")
        kit_cmd(kit, "tools", "detect")
        kit_cmd(kit, "contracts", "scan")
        contracts = json.loads((kit / "state" / "contracts.json").read_text(encoding="utf-8"))["contracts"]
        contract_kinds = {item["kind"] for item in contracts}
        for kind in {"package-or-build-contract-candidate", "config-contract-candidate", "route-or-handler-candidate"}:
            if kind not in contract_kinds:
                raise QAError(f"contracts scan missing {kind}")
        kit_cmd(kit, "tests", "detect")
        first_report = (kit / "reports" / "agent-plan.md").read_text(encoding="utf-8")
        kit_cmd(kit, "report")
        second_report = (kit / "reports" / "agent-plan.md").read_text(encoding="utf-8")
        if first_report != second_report:
            raise QAError("agent-plan report is not reproducible")
        census = json.loads((kit / "state" / "census.json").read_text(encoding="utf-8"))
        if "detected_tools" not in census:
            raise QAError("tools detect did not record detected_tools")

        findings_path = kit / "state" / "findings.jsonl"
        write(findings_path, "{bad json\n")
        kit_cmd(kit, "findings", "validate", expect=1)

        write(findings_path, "")
        append_jsonl(findings_path, finding())
        kit_cmd(kit, "findings", "validate", expect=1)

        write(findings_path, "")
        append_jsonl(findings_path, finding(metrics={}))
        kit_cmd(kit, "findings", "validate", expect=1)

        write(findings_path, "")
        append_jsonl(findings_path, finding(status="approved", evidence=[]))
        kit_cmd(kit, "findings", "validate", expect=1)

        dead = finding(
            id="DEAD-001",
            category="dead-code",
            title="Remove unused module",
            claim="src/core/app.py is removable.",
            recommendation="delete file",
            dead_code={
                "classification": "dynamic_usage_unknown",
                "required_checks": {
                    "static_reference_check": None,
                    "entrypoint_check": None,
                    "config_check": None,
                    "test_or_runtime_check": None,
                    "public_contract_check": None,
                    "generated_vendor_check": None,
                    "counterevidence_and_gaps": None,
                },
            },
        )
        write(findings_path, "")
        append_jsonl(findings_path, dead)
        kit_cmd(kit, "findings", "validate", expect=1)

        packets_path = kit / "state" / "packets.jsonl"
        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(risk_score=4))
        kit_cmd(kit, "packets", "validate", expect=1)

        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(risk_score=5, human_approval={"approved_by": "qa"}))
        kit_cmd(kit, "packets", "validate", expect=1)

        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(allowed_files=[]))
        kit_cmd(kit, "packets", "validate", expect=1)

        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(status="in-progress", allowed_files=[]))
        kit_cmd(kit, "packets", "validate", expect=1)

        write(packets_path, "")
        append_jsonl(packets_path, approved_packet())
        append_jsonl(packets_path, approved_packet(id="PKT-002"))
        kit_cmd(kit, "packets", "validate", expect=1)

        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(status="in-progress"))
        append_jsonl(packets_path, approved_packet(id="PKT-002", status="implemented"))
        kit_cmd(kit, "packets", "validate", expect=1)


def qa_scope() -> None:
    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        project = create_project(temp)
        kit = copy_kit(project)
        packets_path = kit / "state" / "packets.jsonl"
        write(packets_path, "")
        append_jsonl(packets_path, approved_packet())
        write(project / "src" / "core" / "other.py", "x = 1\n")
        kit_cmd(kit, "validate", "--enforce-packet", expect=1)

    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        project = create_project(temp)
        kit = copy_kit(project)
        packets_path = kit / "state" / "packets.jsonl"
        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(path="src\\core\\app.py"))
        write(project / "src" / "core" / "app.py", "def add(a, b):\n    return a + b + 0\n")
        kit_cmd(kit, "validate", "--enforce-packet")

    with tempfile.TemporaryDirectory() as raw:
        temp = Path(raw)
        project = create_project(temp)
        kit = copy_kit(project)
        packets_path = kit / "state" / "packets.jsonl"
        write(packets_path, "")
        append_jsonl(packets_path, approved_packet(path="package.json"))
        write(project / "package.json", "{\"scripts\":{\"test\":\"echo changed\"}}\n")
        kit_cmd(kit, "validate", "--enforce-packet", expect=1)


def qa_installer() -> None:
    with tempfile.TemporaryDirectory() as raw:
        project = Path(raw) / "dry"
        project.mkdir()
        run([PYTHON, str(INIT), str(project), "--dry-run"], ROOT)
        if (project / ".codebase-optimization-kit").exists():
            raise QAError("dry-run wrote the kit directory")

    with tempfile.TemporaryDirectory() as raw:
        project = Path(raw) / "install"
        project.mkdir()
        write(project / "AGENTS.md", "keep me\n")
        run([PYTHON, str(INIT), str(project)], ROOT)
        run([PYTHON, str(ROOT / "scripts" / "validate.py"), str(project)], ROOT)
        if (project / "AGENTS.md").read_text(encoding="utf-8") != "keep me\n":
            raise QAError("installer overwrote root AGENTS.md")
        findings = project / ".codebase-optimization-kit" / "state" / "findings.jsonl"
        write(findings, '{"id":"KEEP"}\n')
        run([PYTHON, str(INIT), str(project), "--overwrite-kit-files"], ROOT)
        if findings.read_text(encoding="utf-8") != '{"id":"KEEP"}\n':
            raise QAError("installer overwrote existing findings")
        run([PYTHON, str(INIT), str(project)], ROOT)
        gitignore = (project / ".gitignore").read_text(encoding="utf-8")
        if gitignore.count("# === codebase-optimization-kit start ===") != 1:
            raise QAError(".gitignore managed block is not idempotent")

    with tempfile.TemporaryDirectory() as raw:
        project = create_project(Path(raw))
        run([PYTHON, str(INIT), str(project)], ROOT)
        if (project / ".gitignore").exists():
            raise QAError("installer should use .git/info/exclude for git projects")
        status = run(["git", "-C", str(project), "status", "--porcelain"], ROOT).stdout
        if ".gitignore" in status:
            raise QAError("installer dirtied .gitignore in a git project")
        kit = project / ".codebase-optimization-kit"
        packets_path = kit / "state" / "packets.jsonl"
        write(packets_path, "")
        append_jsonl(packets_path, approved_packet())
        write(project / "src" / "core" / "app.py", "def add(a, b):\n    return a + b + 0\n")
        kit_cmd(kit, "validate", "--enforce-packet")


def main() -> int:
    try:
        qa_runtime()
        qa_scope()
        qa_installer()
    except QAError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("QA passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
