# Optional Root AGENTS.md Snippet

Use this snippet only when the project already has a root `AGENTS.md`. Paste it into the root file if maintainers approve. It must not replace existing project instructions.

```md
## Temporary Optimization Kit

This repository may contain `.optimization-kit/`, a temporary audit/refactor workspace for one optimization pass.

- Root `AGENTS.md` and project docs remain the source of truth.
- Discovery agents may only write inside `.optimization-kit/workspace/`.
- Implementation agents may only modify files listed in an approved implementation packet.
- Findings are not source of truth until approved, implemented, and validated.
- Replaced findings must be marked `superseded`.
- The kit never writes to `docs/` by default.
```
