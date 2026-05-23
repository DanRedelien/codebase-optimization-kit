# Adoption Guide

Use `codebase-optimization-kit` for one bounded audit/refactor pass inside an existing project.

## Install

```bash
python scripts/init.py /path/to/project
```

Default result:

```text
/path/to/project/
  .optimization-kit/
```

## Choose Mode

Public or normal workspace:

```bash
python scripts/init.py /path/to/project
```

Private scratch folders:

```bash
python scripts/init.py /path/to/project --private-workspace
```

GitHub templates:

```bash
python scripts/init.py /path/to/project --with-github
```

## Validate

```bash
python scripts/validate.py /path/to/project
```

Use explicit expectations when needed:

```bash
python scripts/validate.py /path/to/project --private-workspace --expect-github
```

`--check-working-tree` is optional. In v0.1 it only warns when changed project files are outside the active implementation packet.

## Operating Rule

Keep permanent project docs, root `AGENTS.md`, and repository contribution rules as source of truth. The kit is temporary workflow structure only.
