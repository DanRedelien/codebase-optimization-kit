# Codebase Optimization Kit Runtime

This folder is a temporary, JSON-first runtime for auditing and safely optimizing a large codebase with coding agents.

Start from `AGENT.md`. The normal first commands are:

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py census
python .codebase-optimization-kit/kit.py zones suggest
python .codebase-optimization-kit/kit.py agents plan
```

The source of truth is JSON/JSONL under `state/`. Markdown files are short entrypoints, editable human policies, or generated reports.

This kit does not replace root `AGENTS.md`, project docs, tests, architecture decisions, or human judgment. Delete it after the optimization pass once the final report has been exported and accepted work is merged or abandoned.
