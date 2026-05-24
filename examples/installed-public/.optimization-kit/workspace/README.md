# Workspace

Discovery agents may write temporary notes, maps, findings, and packets here.

Rules:

- This workspace is temporary.
- This workspace is not project source of truth.
- Do not write outside `.optimization-kit/workspace/` during discovery.
- Do not edit project source files without an approved implementation packet.
- Do not write to `docs/` by default.
- Do not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently with another active agent.
- Active work may create advisory lock markers under `.optimization-kit/workspace/locks/`.
