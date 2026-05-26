# Codebase Optimization Kit Agent Entry

This `.codebase-optimization-kit/` directory is temporary workflow state for one optimization pass.

1. Read root `AGENTS.md`, the project `README`, and relevant project authority docs first.
2. Treat project docs, public contracts, and tests as the source of truth.
3. Treat this kit as disposable state, not permanent project documentation.
4. Run:

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py census
python .codebase-optimization-kit/kit.py zones suggest
python .codebase-optimization-kit/kit.py agents plan
python .codebase-optimization-kit/kit.py agents prompts
```

5. Do not modify project source during discovery.
6. Write discovery findings only through structured JSON/JSONL records.
7. Read `policies/audit-criteria.json`; use `audit_queue` lanes in priority order before proposing optimization work.
8. Implementation requires one approved packet.
9. Implementation agents may edit only files listed in the approved packet.
10. Run `python .codebase-optimization-kit/kit.py validate --enforce-packet` before claiming completion.

Record contradictions between docs, tests, schemas, contracts, and observed behavior as `authority-drift` findings. Treat broad "AI slop" concerns as objective `structural-quality`, `duplicate-logic`, `test-reliability`, or `dynamic-usage` evidence instead.

Before approving dead-code or behavior-sensitive packets, read `policies/PROJECT_DEAD_CODE_POLICY.md` and `policies/PROJECT_PARITY_POLICY.md` if they contain project-specific additions.

Machine state lives in `state/`. Policies live in `policies/`. Human reports in `reports/` are generated views, not source of truth. Per-task discovery prompts, when generated, live only in `state/agent-prompts/`; use one `TASK-XXX.md` prompt per clean agent chat.
