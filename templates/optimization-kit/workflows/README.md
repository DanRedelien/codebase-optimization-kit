# Workflows

These workflows make `.optimization-kit/` operational for one audit/refactor pass. They are temporary process guidance only. Root `AGENTS.md`, project docs, and existing project contracts remain the source of truth.

## Read Order

Read only the workflow needed for the current workflow step, then load the linked scoring or language-adapter files as needed.

| File | Covers |
| --- | --- |
| `01-discovery.md` | Project census, zone decomposition, parallel audit, reconciliation, context hygiene, TODO/comment classification. |
| `02-risk-and-evidence.md` | Evidence standard, public contracts, dependency evaluation, behavioral parity, scoring usage, explicit approval rules. |
| `03-implementation.md` | Implementation packets, allowed file scope, small diffs, implementation constraints, review checklist. |
| `04-validation-rollback-archive.md` | Validation, rollback, final summary export, durable knowledge promotion, archive/delete workflow. |

## Non-Negotiable Boundaries

- Discovery agents may only write inside `.optimization-kit/workspace/`.
- Implementation agents may only modify files listed in an approved implementation packet.
- Findings are not source of truth until approved, implemented, and validated.
- Risk 4 implementation requires explicit human approval recorded in an implementation packet or decision file.
- Risk 5 work requires an RFC/ADR path and no direct implementation.
- Agents must not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently.
- The kit never writes to `docs/` by default.
