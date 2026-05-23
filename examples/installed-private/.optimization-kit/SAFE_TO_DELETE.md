# Safe To Delete

`.optimization-kit/` is safe to delete when:

- The final summary has been exported.
- Accepted changes have been merged or intentionally abandoned.
- Rollback plans for merged changes are no longer needed.
- Any durable knowledge has been promoted through an approved proposal.

Deleting this directory must not break the project. The kit is temporary workflow tooling and must not be required by runtime code, tests, builds, docs, or release processes.

Before deletion, preserve only the artifacts maintainers explicitly want to keep. Do not copy findings into `docs/` unless a durable-knowledge promotion proposal has been approved.
