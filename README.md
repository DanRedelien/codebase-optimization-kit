# codebase-optimization-kit

`codebase-optimization-kit` is a temporary audit/refactor workspace installed into a project for one optimization pass. It helps agents run structured analysis, prepare safe refactor plans, validate changes, and then delete or archive the workspace.

Default install target:

```text
project/
  .optimization-kit/
```

The kit does not replace the project's `docs/`, `AGENTS.md`, `README.md`, architecture docs, or contribution rules. Those files remain the source of truth.

## Current v0.1 Scope

This repository currently contains the product skeleton, English-only artifact templates, grouped workflows, scoring policy, language adapters, the safe installer, the validator, and adoption docs for v0.1:

```text
scripts/
  init.py
  validate.py

docs/
  adoption-guide.md
  update-strategy.md
  open-source-guide.md
  mcp-roadmap.md
  removal-and-archive.md

templates/
  optimization-kit/
    START_HERE.md
    AGENTS.optimization.md
    AGENTS.merge-snippet.md
    SAFE_TO_DELETE.md
    manifest.template.json
    status.md
    workflows/
      01-discovery.md
      02-risk-and-evidence.md
      03-implementation.md
      04-validation-rollback-archive.md
      05-qa-and-review.md
    scoring/
      impact.md
      confidence.md
      risk.md
      priority.md
      risk-policy.md
    language-adapters/
      python.md
      typescript.md
      rust.md
      go.md
      java.md
      cpp.md
    templates/
    roles/
      qa-agent.md
      review-agent.md
    workspace/
```

The workflow files are grouped by operating area to reduce context noise. Detailed rules live in `templates/`, `scoring/`, and `language-adapters/`.

## Requirements

- Python 3.10 or newer on the host machine running the installer and validator.
- An existing project directory where the temporary workspace should be installed.

## Install

Run the installer from this repository:

```bash
python scripts/init.py /path/to/project
```

Optional flags:

| Flag | Meaning |
| --- | --- |
| `--dry-run` | Print the planned `CREATE`, `SKIP`, `APPEND`, and `OVERWRITE` actions without writing files. |
| `--private-workspace` | Create ignored private working folders under `.optimization-kit/workspace/`. |
| `--with-github` | Install optimization GitHub issue and pull request templates. |
| `--overwrite-kit-files` | Replace only known kit-owned files and requested GitHub templates. Project artifacts are still protected. |
| `--target-dir .optimization-kit` | Install the kit into a different relative directory. The default is `.optimization-kit`. |
| `--gitignore-all` | Ignore the entire installed kit directory instead of only private/cache/raw workspace folders. |

Safety guarantees:

The installer is conservative because it is meant to run inside existing projects. It does not remove any project file or directory, and it does not overwrite existing files unless `--overwrite-kit-files` is used for known kit-owned files.

- Files under `.optimization-kit/workspace/` are treated as project-specific artifacts and are never overwritten.
- Existing root `AGENTS.md` is never overwritten; review `.optimization-kit/AGENTS.merge-snippet.md` instead.
- `.gitignore` is changed only inside the marker block created by this installer.
- Symlinked or junction target paths are skipped instead of followed.

## Validate

Run the validator against an installed project:

```bash
python scripts/validate.py /path/to/project
```

Optional validation modes:

| Flag | Meaning |
| --- | --- |
| `--expect-github` | Require optimization GitHub issue and pull request templates. |
| `--private-workspace` | Require private/cache/raw workspace directories and ignore coverage. |
| `--check-working-tree` | Warn when changed project files are outside the active implementation packet. |
| `--target-dir .optimization-kit` | Validate a custom installed kit directory. |

The validator checks only relative Markdown links that resolve to files inside the installed kit. External links and anchor-only links are ignored in v0.1.

## Typical Workflow

1. Install `.optimization-kit/` into the target project.
2. Ask the agent to read the project's root instructions, then `.optimization-kit/START_HERE.md`.
3. Run discovery and write temporary maps, findings, and packets under `.optimization-kit/workspace/`.
4. Approve one implementation packet before any source changes.
5. Implement only the packet scope, validate, and record results.
6. Export the final summary, promote only approved durable knowledge, then delete or archive `.optimization-kit/`.

## Core Rules

- `.optimization-kit/` is temporary workflow tooling.
- Root `AGENTS.md` and project docs remain the source of truth.
- Discovery agents may only write inside `.optimization-kit/workspace/`.
- Implementation agents may only modify files listed in an approved implementation packet.
- Findings are not source of truth until approved, implemented, and validated.
- Replaced findings must be marked `superseded`, not left as orphan records.
- Risk 4 implementation requires explicit human approval recorded in an implementation packet or decision file.
- Risk 5 work requires an RFC/ADR path and no direct implementation from the kit.
- QA Agent and Review Agent responsibilities are separated in `roles/` and `workflows/05-qa-and-review.md`.
- Agents must not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently.
- Active parallel work may create advisory `.optimization-kit/workspace/locks/<id>.lock` markers; full lock automation is deferred to v0.2.
- The kit never writes to `docs/` by default.

## Finding IDs

Use stable IDs by category:

```text
ARCH-001
DEAD-001
PERF-001
TEST-001
DOCS-001
INT-001
```

## Finding Lifecycle

```text
candidate
needs-evidence
approved
rejected
superseded
implemented
validated
rolled-back
```

## Out Of Scope For v0.1

- MCP server.
- Package publishing.
- Automatic code analysis.
- Automatic refactor execution.
- Dependency graph generation.
- Coverage parsing.
- Benchmark dashboard.
- Web research automation.
- Permanent project documentation management.
