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

## Review Agent

- Verifies changed files match the approved packet.
- Checks risk-policy compliance, public contracts, dependency changes, validation, and rollback readiness.
- Requests fixes or reconciliation before findings move to `validated`.

## Validation And Archive Agent

- Uses `workflows/04-validation-rollback-archive.md`.
- Records validation and rollback evidence.
- Prepares the final summary.
- Promotes durable knowledge only through approved proposals.
- Deletes or archives `.optimization-kit/` only after cleanup criteria are met.
