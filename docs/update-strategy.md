# Update Strategy

The optional installer uses conservative updates.

## Default Behavior

- Never delete files.
- Never overwrite existing files by default.
- Never write or overwrite root `AGENTS.md`.
- Never overwrite existing project files.
- In git projects, write ignore protection to `.git/info/exclude`; outside git, change only `.gitignore` inside the managed marker block.

## Kit-Owned Updates

Use:

```bash
python scripts/init.py /path/to/project --overwrite-kit-files
```

This refreshes kit-owned runtime files only. Existing state and generated operational records stay protected:

- `.codebase-optimization-kit/state/`
- `.codebase-optimization-kit/reports/status.md`
- `.codebase-optimization-kit/reports/agent-plan.md`
- `.codebase-optimization-kit/reports/findings-ranked.md`
- `.codebase-optimization-kit/reports/implementation-backlog.md`
- `.codebase-optimization-kit/reports/final-report.md`

Findings, packets, validations, locks, decisions, generated reports, and project-specific state should be treated as target-project artifacts.

## Manual Copy Updates

Manual copy remains supported. When refreshing manually, copy only runtime-owned files unless the human explicitly chooses to replace state.
