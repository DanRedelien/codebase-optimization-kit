# Open Source Guide

The kit is safe to include in public repositories when its state does not contain private scratch data.

## Public Install

```bash
python scripts/init.py /path/to/project
python scripts/validate.py /path/to/project
```

## Private Data

Do not commit private notes, raw logs, cache files, credentials, customer data, or proprietary audit dumps.

The runtime is designed to be temporary. In git projects, the installer-managed ignore block is written to `.git/info/exclude`; outside git it falls back to `.gitignore`.

## Validation

`scripts/validate.py` delegates to the installed runtime:

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py validate
```

Use `--enforce-packet` when reviewing implementation work.
