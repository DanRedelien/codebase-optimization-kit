# codebase-optimization-kit

`codebase-optimization-kit` is a disposable, JSON-first agent-ops runtime for large codebase optimization passes.

The primary artifact is the installed folder:

```text
.codebase-optimization-kit/
```

Copy that folder into a target project, then tell the coding agent to read:

```text
.codebase-optimization-kit/AGENT.md
```

The kit helps agents build a project census, suggest zones, plan multi-agent discovery, record evidence-backed findings, create implementation packets, and enforce packet scope before completion.

It is not a permanent project dependency, documentation system, MCP server, autonomous refactoring engine, or LOC reduction bot. Delete it after the optimization pass once final reports are exported and accepted work is merged or abandoned.

## Runtime Layout

```text
templates/optimization-kit/
  AGENT.md
  README.md
  SAFE_TO_DELETE.md
  kit.py
  schema/
  state/
  adapters/
  policies/
  templates/
  reports/
```

When installed, this becomes:

```text
project/
  .codebase-optimization-kit/
```

JSON and JSONL files under `state/` are the source of truth. Only `state/project.json` ships by default; `doctor` creates the remaining state files on first run. Markdown files are short entrypoints, editable policy templates, or generated reports.

## Manual Copy Workflow

Manual copy is the first-class workflow:

```bash
cp -R templates/optimization-kit /path/to/project/.codebase-optimization-kit
```

Then, in the target project:

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py census
python .codebase-optimization-kit/kit.py zones suggest
python .codebase-optimization-kit/kit.py agents plan
```

## Optional Installer

The optional safe copier preserves existing project and kit state files:

```bash
python scripts/init.py /path/to/project
```

Useful flags:

| Flag | Meaning |
| --- | --- |
| `--dry-run` | Print planned actions without writing files. |
| `--target-dir .codebase-optimization-kit` | Use a custom relative target directory. |
| `--overwrite-kit-files` | Refresh kit-owned runtime files only. State, findings, packets, reports, locks, and decisions are preserved. |
| `--with-github` | Copy optional GitHub issue/PR templates if missing. |

Installer safety rules:

- It never deletes project files.
- It never writes or overwrites root `AGENTS.md`.
- It never overwrites existing project files.
- It preserves existing kit state, findings, packets, reports, locks, and decisions.
- In git projects, it writes the managed ignore block to `.git/info/exclude`; outside git it falls back to `.gitignore`.
- It refuses symlink or junction installs.

## Runtime Commands

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py census
python .codebase-optimization-kit/kit.py zones suggest
python .codebase-optimization-kit/kit.py agents plan
python .codebase-optimization-kit/kit.py findings add --file finding.json
python .codebase-optimization-kit/kit.py findings validate
python .codebase-optimization-kit/kit.py reconcile
python .codebase-optimization-kit/kit.py packets create --finding DEAD-001
python .codebase-optimization-kit/kit.py packets validate
python .codebase-optimization-kit/kit.py validate
python .codebase-optimization-kit/kit.py validate --enforce-packet
python .codebase-optimization-kit/kit.py report
python .codebase-optimization-kit/kit.py tools detect
python .codebase-optimization-kit/kit.py contracts scan
python .codebase-optimization-kit/kit.py tests detect
python .codebase-optimization-kit/kit.py locks acquire --scope Z-core
python .codebase-optimization-kit/kit.py locks release --scope Z-core
python .codebase-optimization-kit/kit.py status
```

Core runtime behavior uses Python 3.10+ and the standard library. It may detect existing project tools, but baseline census, zones, planning, validation, and reporting do not require package installation.

## Validation

Validate an installed runtime through the wrapper:

```bash
python scripts/validate.py /path/to/project
```

The wrapper delegates to:

```bash
python .codebase-optimization-kit/kit.py doctor
python .codebase-optimization-kit/kit.py validate
```

Use `--enforce-packet` to fail when changed project files are outside the active approved packet.

## Core Rules

- Project docs, tests, and public contracts remain the source of truth.
- Discovery agents do not modify project source.
- Findings must be structured JSON/JSONL records.
- Implementation requires an approved packet.
- Implementation agents may edit only packet-listed files.
- Risk 4 packets require explicit human approval.
- Risk 5 work cannot be implemented directly from the kit.
- Dead-code deletion and behavioral parity require structured evidence.
- Reports are generated views over JSON state, not source of truth.

## Maintainer Docs

Maintainer notes live under `docs/` and are not installed into target projects.
