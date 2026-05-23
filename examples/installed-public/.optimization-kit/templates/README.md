# Artifact Templates

Use these templates for temporary optimization artifacts. They do not replace project docs or root `AGENTS.md`.

Rules:

- Discovery outputs belong in `.optimization-kit/workspace/`.
- Implementation requires an approved implementation packet.
- Findings become reliable only after acceptance and validation.
- Replaced findings must be marked `superseded`.
- Do not write to `docs/` by default.

## Templates

| File | Use |
| --- | --- |
| `finding.template.md` | Record candidate and accepted findings. |
| `context-packet.template.md` | Package only the context needed for one decision or implementation. |
| `implementation-packet.template.md` | Authorize scoped implementation work. |
| `rollback-plan.template.md` | Define rollback scope, trigger, and validation. |
| `final-summary.template.md` | Export the result of the temporary optimization pass. |
| `durable-knowledge-promotion-proposal.template.md` | Request approval to move durable knowledge into project source-of-truth files. |
| `decision-record.template.md` | Record human decisions that do not belong in source files. |
