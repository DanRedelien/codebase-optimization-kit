# Update Strategy

v0.1 uses conservative updates.

## Default Behavior

- Never delete files.
- Never overwrite existing files by default.
- Never overwrite root `AGENTS.md`.
- Never overwrite workspace artifacts.
- Only change `.gitignore` inside the managed marker block.

## Kit-Owned Updates

Use:

```bash
python scripts/init.py /path/to/project --overwrite-kit-files
```

This may overwrite known kit-owned files only when the existing manifest is compatible. If `--with-github` is also used, it may overwrite the known optimization GitHub templates.

Protected artifacts stay protected:

- `.optimization-kit/workspace/maps/`
- `.optimization-kit/workspace/findings/`
- `.optimization-kit/workspace/reports/`
- `.optimization-kit/workspace/context-packets/`
- `.optimization-kit/workspace/implementation-packets/`
- `.optimization-kit/workspace/decisions/`
- `.optimization-kit/workspace/private/`
- `.optimization-kit/workspace/cache/`
- `.optimization-kit/workspace/raw/`

## Schema Rule

If an installed manifest has a newer schema, the installer warns and refuses overwrite. If it has an older schema, the installer installs only missing files unless a future update command exists.
