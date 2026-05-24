# Adoption Guide

Use `codebase-optimization-kit` for one bounded audit/refactor pass inside an existing project.

## Manual Copy

Manual copy is the primary workflow:

```bash
cp -R templates/optimization-kit /path/to/project/.codebase-optimization-kit
```

Then ask the agent to read:

```text
.codebase-optimization-kit/AGENT.md
```

## Optional Installer

```bash
python scripts/init.py /path/to/project
```

Default result:

```text
/path/to/project/
  .codebase-optimization-kit/
```

## Validate

```bash
python scripts/validate.py /path/to/project
```

Use packet enforcement after implementation work:

```bash
python scripts/validate.py /path/to/project --enforce-packet
```

## Operating Rule

Keep permanent project docs, root `AGENTS.md`, public contracts, and tests as source of truth. The kit is temporary workflow state only.
