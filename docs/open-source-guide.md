# Open Source Guide

The kit is safe to include in public repositories when the workspace does not contain private scratch data.

## Public Install

```bash
python scripts/init.py /path/to/project --with-github
python scripts/validate.py /path/to/project --expect-github
```

GitHub templates are optional and installed only when requested.

## Private Data

Do not commit private notes, raw logs, cache files, credentials, customer data, or proprietary audit dumps.

When private scratch space is needed:

```bash
python scripts/init.py /path/to/project --private-workspace
python scripts/validate.py /path/to/project --private-workspace
```

The installer adds ignore entries for private, cache, and raw workspace folders.

## Link Validation

v0.1 validates only relative Markdown links that resolve to files inside `.optimization-kit/`. External links and anchor-only links are ignored.
