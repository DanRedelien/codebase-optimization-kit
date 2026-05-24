# Optimization Kit Agent Instructions

These instructions apply only to work inside `.optimization-kit/`. They do not replace root `AGENTS.md` or project documentation.

## Source Of Truth

- Root `AGENTS.md` controls repository behavior.
- Project docs and existing architecture notes control durable project knowledge.
- This kit is temporary workflow tooling for one optimization pass.

## Write Boundaries

- Discovery agents may only write inside `.optimization-kit/workspace/`.
- Implementation agents may only modify files listed in an approved implementation packet.
- The kit never writes to `docs/` by default.
- Do not create permanent project documentation from kit findings without an approved durable-knowledge promotion proposal.
- Do not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently with another active agent.
- Active parallel work may create `.optimization-kit/workspace/locks/<id>.lock` as an advisory v0.1 marker.

## Findings

- Findings must use stable IDs such as `ARCH-001`, `DEAD-001`, `PERF-001`, `TEST-001`, `DOCS-001`, or `INT-001`.
- Findings must use one lifecycle status: `candidate`, `needs-evidence`, `approved`, `rejected`, `superseded`, `implemented`, `validated`, or `rolled-back`.
- Replaced findings must be marked `superseded` and linked to the replacement.
- Findings are not source of truth until approved, implemented, and validated.

## Implementation

- Implement only from an approved implementation packet.
- Modify only files listed in the packet.
- Run the validation commands listed in the packet.
- If the packet is incomplete or stale, stop and request reconciliation.
- Risk 4 implementation requires explicit human approval recorded in the packet or a decision file.
- Risk 5 work requires the project's RFC, ADR, or equivalent governance path and must not be implemented directly from this kit.

## Scoring

- Use `scoring/impact.md`, `scoring/confidence.md`, `scoring/risk.md`, and `scoring/priority.md` to evaluate findings.
- Use `scoring/risk-policy.md` as the controlling approval policy.
- Priority never overrides risk policy.

## Language

All user-facing kit content must be written in English.
