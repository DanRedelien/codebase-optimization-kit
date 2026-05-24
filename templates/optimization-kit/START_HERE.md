# Start Here

This `.optimization-kit/` directory is temporary workflow tooling for one audit/refactor pass. It can be deleted or archived after the final summary is exported and accepted changes are merged.

## Authority

- Root `AGENTS.md` and project docs remain the source of truth.
- This kit adds workflow structure only.
- Findings are not source of truth until approved, implemented, and validated.
- The kit never writes to `docs/` by default.

## Agent Boundaries

- Discovery agents may only write inside `.optimization-kit/workspace/`.
- Implementation agents may only modify files listed in an approved implementation packet.
- If a required file is not listed in the packet, stop and request a packet update.
- Risk 4 implementation requires explicit human approval recorded in an implementation packet or decision file.
- Risk 5 work requires an RFC/ADR path and no direct implementation from this kit.

## Workflow Read Order

Read only what applies to the current workflow step:

1. `workflows/01-discovery.md`
2. `workflows/02-risk-and-evidence.md`
3. `workflows/03-implementation.md`
4. `workflows/04-validation-rollback-archive.md`
5. `workflows/05-qa-and-review.md`

Use `scoring/risk-policy.md` as the approval authority and load only relevant language adapters.

## Finding Lifecycle

Use exactly one lifecycle status per finding:

```text
candidate
needs-evidence
approved
rejected
superseded
implemented
validated
rolled-back
```

Mark replaced findings as `superseded` and link the replacement finding ID.

## Stable Finding IDs

Examples:

```text
ARCH-001
DEAD-001
PERF-001
TEST-001
DOCS-001
INT-001
```

## First Steps

1. Read root `AGENTS.md`, `README.md`, and relevant project docs.
2. Record project-specific notes in `.optimization-kit/workspace/`.
3. Use the workflow file for the current workflow step.
4. Do not edit project source files until an implementation packet is approved.
