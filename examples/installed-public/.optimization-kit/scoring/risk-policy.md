# Risk Policy

This file is the authority for implementation approval paths. Workflows may summarize it, but they must not weaken it.

## Policy Table

| Risk | Implementation path | Approval requirement |
| --- | --- | --- |
| 1 | Local implementation allowed with validation. | No extra risk approval beyond project or task authorization; source edits must still respect the active approved scope. |
| 2 | Local implementation allowed with validation. | No extra risk approval beyond project or task authorization; source edits must still respect the active approved scope. |
| 3 | Implementation packet required. | Packet must be approved before source edits. |
| 4 | Explicit approval required before implementation. | Human approval only, recorded in an implementation packet or decision file. |
| 5 | RFC/ADR required. | No direct implementation from this kit workflow. |

## Explicit Approval

Risk 4 approval must be human approval. Another agent, automated reviewer, CI result, inferred silence, or model-generated approval does not count.

The approval record must include:

- Human approver name or handle.
- Approval date.
- Related finding IDs.
- Approved scope and risk level.
- Allowed files or contract changes.
- Required validation.
- Rollback expectations.

Valid approval locations:

- The `Approval` section of an implementation packet.
- A decision file under `.optimization-kit/workspace/decisions/`.

Approval must exist before implementation begins.

## Risk 5 Handling

Risk 5 findings are not implemented directly from the optimization kit. Route them to the project's RFC, ADR, design review, or equivalent governance process.

Risk 5 examples:

- Cross-system architecture changes.
- Public compatibility breaks without migration design.
- Data model or migration strategy changes with irreversible effects.
- Authentication, authorization, privacy, or security posture redesign.
- Build, release, or deployment model changes affecting multiple teams or environments.

## Escalation Rules

- If new evidence raises risk during implementation, stop and follow the higher risk path.
- If a Risk 1-2 change grows beyond local scope, create an implementation packet.
- If Risk 3 touches public contracts or dependencies, rescore for Risk 4.
- If approval scope is narrower than the needed change, request a packet or decision update.

## Validation Requirement

Every implemented risk level requires validation. Validation must be recorded with the command or check, expected result, actual result, and gaps.
