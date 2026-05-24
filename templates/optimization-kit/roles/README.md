# Roles

Roles describe responsibilities for one optimization pass. They do not grant write permissions beyond the workflows, implementation packets, or root project instructions.

## Coordinator

- Maintains finding IDs and lifecycle status.
- Assigns zones and prevents duplicate findings.
- Ensures Risk 4 approval is human-only and recorded before implementation.
- Ensures Risk 5 work routes to RFC/ADR instead of direct implementation.

## Discovery Agent

- Uses `workflows/01-discovery.md`.
- Writes only inside `.optimization-kit/workspace/`.
- Produces census, zone, audit, reconciliation, context, and candidate finding artifacts.
- Does not edit project source files.

## Evidence Reviewer

- Uses `workflows/02-risk-and-evidence.md`.
- Checks evidence, counterevidence, public contracts, dependencies, and behavioral parity.
- Applies scoring files and `scoring/risk-policy.md`.
- Does not implement changes.

## Implementation Agent

- Uses `workflows/03-implementation.md`.
- Modifies only files listed in an approved implementation packet.
- Stops when packet scope is incomplete, stale, or narrower than the required change.
- Runs or records validation commands.

## QA Agent

- Uses `workflows/05-qa-and-review.md` and `roles/qa-agent.md`.
- Checks commands, idempotency, filesystem behavior, installer recovery, and validator behavior.
- Verifies partial installs are completed without overwriting existing workspace artifacts.
- Does not decide safety policy and does not implement changes unless separately assigned by an approved packet.

## Review Agent

- Uses `workflows/05-qa-and-review.md` and `roles/review-agent.md`.
- Checks safety policy, wording clarity, agent ambiguity, overwrite risks, public contracts, dependency changes, and rollback readiness.
- Verifies changed files match the approved packet.
- Does not edit source files or move findings to `validated`; it records review notes and requests reconciliation.
- Requests fixes or reconciliation before findings move to `validated`.

## v0.1 Parallel Work Rule

- Agents must not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently.
- Active work may create `.optimization-kit/workspace/locks/<id>.lock` as an advisory marker.
- Full lock acquisition, stale-lock detection, and release automation are deferred to v0.2.

## Validation And Archive Agent

- Uses `workflows/04-validation-rollback-archive.md`.
- Records validation and rollback evidence.
- Prepares the final summary.
- Promotes durable knowledge only through approved proposals.
- Deletes or archives `.optimization-kit/` only after cleanup criteria are met.
