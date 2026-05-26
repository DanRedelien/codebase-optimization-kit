"""Audit policy helpers.

Keep this module small and mechanical: policy data only matters when it affects
validation, task generation, risk floors, or dedupe.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any, Callable


AUDIT_LANE_PRIORITY = [
    "security-risk",
    "dependency-risk",
    "authority-drift",
    "dynamic-usage",
    "test-reliability",
    "type-contract-safety",
    "dead-code",
    "duplicate-logic",
    "structural-quality",
]
AUDIT_LANES = set(AUDIT_LANE_PRIORITY)
AUDIT_POLICY_ORDER = ["discovery-only", "packet-ok", "human-approval", "blocked-direct"]
AUDIT_LANE_TO_ROLE = {
    "security-risk": "domain-risk-auditor",
    "dependency-risk": "dependency-auditor",
    "authority-drift": "integration-auditor",
    "dynamic-usage": "integration-auditor",
    "test-reliability": "test-coverage-auditor",
    "type-contract-safety": "architecture-auditor",
    "dead-code": "dead-code-auditor",
    "duplicate-logic": "duplicate-logic-auditor",
    "structural-quality": "architecture-auditor",
}
DEFAULT_BASELINE_CAPS = {
    "max_bytes_per_text_file": 262144,
    "total_content_read_bytes": 67108864,
    "max_content_sampled_files": 20000,
    "structural_top_files_per_zone": 50,
    "duplicate_top_files_project": 200,
    "duplicate_top_files_per_zone": 20,
    "soft_time_budget_seconds": 60,
    "hard_time_budget_seconds": 120,
}
SECURITY_NAME_TOKENS = {
    "auth",
    "authorization",
    "credential",
    "credentials",
    "crypto",
    "csrf",
    "decrypt",
    "encrypt",
    "jwt",
    "oauth",
    "password",
    "payment",
    "permission",
    "permissions",
    "rbac",
    "saml",
    "secret",
    "security",
    "session",
    "signin",
    "signup",
    "sso",
    "token",
    "webhook",
}
SECURITY_PATH_HINTS = {
    ".env",
    "auth",
    "crypto",
    "oauth",
    "payments",
    "permissions",
    "secrets",
    "security",
    "sessions",
    "webhooks",
}


def policy_lanes(policy: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    lanes = policy.get("lanes", {}) if isinstance(policy, dict) else {}
    return {str(key): value for key, value in lanes.items() if isinstance(value, dict)}


def known_categories(policy: dict[str, Any], custom: set[str]) -> set[str]:
    return {str(item.get("finding_category")) for item in policy_lanes(policy).values() if isinstance(item.get("finding_category"), str)} | custom


def risk_floor_for_lanes(lanes: list[str], policy: dict[str, Any]) -> int:
    configs = policy_lanes(policy)
    floor = 1
    for lane in lanes:
        config = configs.get(lane, {})
        raw = config.get("default_risk_floor", 1)
        if isinstance(raw, int):
            floor = max(floor, raw)
        implementation_policy = config.get("implementation_policy")
        if implementation_policy == "human-approval":
            floor = max(floor, 4)
        elif implementation_policy == "blocked-direct":
            floor = max(floor, 5)
    return floor


def baseline_caps(policy: dict[str, Any]) -> dict[str, int]:
    caps = policy.get("baseline_caps", {}) if isinstance(policy, dict) else {}
    result = dict(DEFAULT_BASELINE_CAPS)
    for key in result:
        raw = caps.get(key)
        if isinstance(raw, int) and raw > 0:
            result[key] = raw
    return result


def metric_risk_level(metrics: Any) -> int | None:
    if not isinstance(metrics, dict):
        return None
    risk = metrics.get("risk_score")
    if isinstance(risk, dict):
        raw = risk.get("risk_level")
        return raw if isinstance(raw, int) else None
    return risk if isinstance(risk, int) else None


def finding_audit_lanes(finding: dict[str, Any], policy: dict[str, Any]) -> tuple[str | None, list[str], list[str]]:
    errors: list[str] = []
    category = finding.get("category")
    lanes = policy_lanes(policy)
    primary = finding.get("primary_lane")
    if primary is None and isinstance(finding.get("audit"), dict):
        primary = finding["audit"].get("primary_lane")
    if primary is None and isinstance(category, str) and category in lanes:
        primary = category
    if primary is not None and primary not in lanes:
        errors.append(f"finding {finding.get('id', '<unknown>')} has unknown primary_lane: {primary}")

    related = finding.get("related_lanes")
    if related is None and isinstance(finding.get("audit"), dict):
        related = finding["audit"].get("related_lanes")
    if related is None:
        related = []
    if not isinstance(related, list):
        errors.append(f"finding {finding.get('id', '<unknown>')} related_lanes must be a list")
        related_lanes: list[str] = []
    else:
        related_lanes = [str(item) for item in related]
        for lane in related_lanes:
            if lane not in lanes:
                errors.append(f"finding {finding.get('id', '<unknown>')} has unknown related lane: {lane}")
    if primary is not None:
        related_lanes = [lane for lane in related_lanes if lane != primary]
    return str(primary) if primary is not None else None, related_lanes, errors


def evidence_container(finding: dict[str, Any]) -> dict[str, Any]:
    containers: list[dict[str, Any]] = []
    for key in ["evidence_fields", "category_evidence"]:
        value = finding.get(key)
        if isinstance(value, dict):
            containers.append(value)
    audit = finding.get("audit")
    if isinstance(audit, dict):
        for key in ["evidence_fields", "category_evidence", "evidence"]:
            value = audit.get(key)
            if isinstance(value, dict):
                containers.append(value)
        containers.append(audit)
    merged: dict[str, Any] = {}
    for container in containers:
        merged.update(container)
    return merged


def evidence_value(finding: dict[str, Any], key: str, dead_code_checks: list[str]) -> Any:
    if key == "affected_files":
        return finding.get("affected_files")
    if key == "counterevidence_or_gap":
        audit = finding.get("audit") if isinstance(finding.get("audit"), dict) else {}
        fields = evidence_container(finding)
        return finding.get("counterevidence") or fields.get("evidence_gap") or fields.get("counterevidence_or_gap") or audit.get("evidence_gap")
    if key in finding:
        return finding.get(key)
    fields = evidence_container(finding)
    if key in fields:
        return fields.get(key)
    if key in dead_code_checks:
        dead = finding.get("dead_code")
        checks = dead.get("required_checks") if isinstance(dead, dict) else None
        if isinstance(checks, dict):
            return checks.get(key)
    return None


def required_evidence_errors(
    finding: dict[str, Any],
    primary_lane: str | None,
    policy: dict[str, Any],
    non_empty: Callable[[Any], bool],
    dead_code_checks: list[str],
) -> list[str]:
    if primary_lane is None:
        return []
    lane = policy_lanes(policy).get(primary_lane, {})
    required = lane.get("required_evidence", [])
    if not isinstance(required, list):
        return [f"finding {finding.get('id', '<unknown>')} audit lane {primary_lane} required_evidence must be a list in policy"]
    errors = []
    for key in required:
        if isinstance(key, str) and not non_empty(evidence_value(finding, key, dead_code_checks)):
            errors.append(f"finding {finding.get('id', '<unknown>')} category {primary_lane} missing category-specific evidence field: {key}")
    return errors


def normalized_root_cause(finding: dict[str, Any], dead_code_checks: list[str]) -> str:
    root = evidence_value(finding, "root_cause", dead_code_checks) or finding.get("claim") or ""
    return re.sub(r"\s+", " ", str(root)).strip().lower()


def normalize_path(raw: str | Any) -> str:
    value = str(raw).replace("\\", "/").strip()
    value = re.sub(r"^\./+", "", value)
    parts = [part for part in PurePosixPath(value).parts if part not in {"", "."}]
    return PurePosixPath(*parts).as_posix() if parts else "."


def finding_dedupe_key(finding: dict[str, Any], policy: dict[str, Any], dead_code_checks: list[str]) -> str:
    primary, _, _ = finding_audit_lanes(finding, policy)
    paths = sorted(normalize_path(path) for path in finding.get("affected_files") or [])
    return json.dumps([paths, normalized_root_cause(finding, dead_code_checks), primary or finding.get("category")], sort_keys=True)


def lane_priority_key(lane: str) -> int:
    try:
        return AUDIT_LANE_PRIORITY.index(lane)
    except ValueError:
        return len(AUDIT_LANE_PRIORITY)


def zone_records(zone: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("zone") == zone.get("id")]


def security_signals_for_zone(zone: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    signals: list[str] = []
    for record in zone_records(zone, records):
        path = str(record.get("path", ""))
        lowered = path.lower()
        path_parts = [part.lower() for part in PurePosixPath(path).parts]
        name = PurePosixPath(path).name.lower()
        stem_tokens = {token for token in re.split(r"[^a-z0-9]+", PurePosixPath(name).stem) if token}
        if name == ".env" or (name.startswith(".env.") and not name.endswith((".example", ".sample", ".template", ".dist"))):
            signals.append(f"{path}:env-file")
        if SECURITY_PATH_HINTS & set(path_parts):
            signals.append(f"{path}:security-path")
        if SECURITY_NAME_TOKENS & stem_tokens:
            signals.append(f"{path}:security-name")
        if any(token in lowered for token in ["/auth/", "/oauth/", "/permissions/", "/secrets/", "/webhooks/"]):
            signals.append(f"{path}:security-boundary")
    return sorted(set(signals))[:25]


def audit_lanes_for_zone(
    zone: dict[str, Any],
    records: list[dict[str, Any]],
    package_manifests: set[str],
    lockfiles: set[str],
    config_names: set[str],
) -> list[str]:
    loc = int(zone.get("loc") or 0)
    files = int(zone.get("files") or 0)
    risk_notes = set(zone.get("risk_notes") or [])
    items = zone_records(zone, records)
    names = {PurePosixPath(str(item.get("path", ""))).name for item in items}
    has_source = any("source" in (item.get("signals") or []) for item in items)
    has_config = any(
        PurePosixPath(str(item.get("path", ""))).name in config_names or str(item.get("path", "")).startswith(".github/")
        for item in items
    )
    has_entrypoint = bool(zone.get("entrypoints"))
    lanes = ["structural-quality", "test-reliability", "authority-drift"]
    if security_signals_for_zone(zone, records):
        lanes.append("security-risk")
    if has_source or has_config or has_entrypoint:
        lanes.append("dynamic-usage")
    if "dependency-metadata" in risk_notes or any(name in package_manifests or name in lockfiles for name in names):
        lanes.append("dependency-risk")
    if loc >= 12000 or files >= 120 or "oversized-zone" in risk_notes:
        lanes.extend(["structural-quality", "duplicate-logic"])
    if loc >= 12000 or files >= 120:
        lanes.append("type-contract-safety")
    unique = []
    for lane in sorted(lanes, key=lane_priority_key):
        if lane not in unique:
            unique.append(lane)
    return unique


def roles_for_lanes(lanes: list[str]) -> list[str]:
    roles: list[str] = []
    for lane in lanes:
        role = AUDIT_LANE_TO_ROLE.get(lane, "architecture-auditor")
        if role not in roles:
            roles.append(role)
    return roles
