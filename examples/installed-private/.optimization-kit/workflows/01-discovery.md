# Workflow 01: Discovery

Use this workflow to understand the project without changing source code. It combines project census, zone decomposition, parallel audit, reconciliation, context hygiene, and TODO/comment classification.

## Inputs

- Root `AGENTS.md`, if present.
- Project `README.md`, contribution docs, architecture docs, and package manifests.
- `.optimization-kit/START_HERE.md` and `.optimization-kit/status.md`.
- Relevant files from `.optimization-kit/language-adapters/`.
- Existing artifacts in `.optimization-kit/workspace/`, if any.

## Outputs

Write outputs under `.optimization-kit/workspace/`:

- `project-census.md`
- `zone-map.md`
- `audit-<zone>.md`
- `reconciliation.md`
- `todo-classification.md`
- Context packets that use `.optimization-kit/templates/context-packet.template.md`
- Candidate findings that use `.optimization-kit/templates/finding.template.md`

## Allowed Writes

- `.optimization-kit/workspace/**`

Discovery agents must not write anywhere else unless a later approved implementation packet explicitly lists the file.

## Forbidden Actions

- Do not modify project source files.
- Do not modify root `AGENTS.md`, `README.md`, or `docs/`.
- Do not install, remove, or upgrade dependencies.
- Do not mark findings as `approved`, `implemented`, or `validated`.
- Do not delete files based on dead-code suspicion.
- Do not treat generated maps or findings as project source of truth.

## Checklist

1. Read project authority files first: root `AGENTS.md`, `README.md`, contribution rules, and relevant docs.
2. Build a project census: languages, frameworks, package managers, entrypoints, tests, generated folders, deployment files, and known project-specific rules.
3. Decompose the project into zones with clear ownership and runtime boundaries.
4. Run parallel audits by zone when useful. Each audit output must name files read, assumptions, and evidence gaps.
5. Reconcile duplicate or conflicting findings into stable finding IDs.
6. Classify TODO, FIXME, HACK, XXX, deprecated, and dead-code comments before using them as evidence.
7. Keep context packets narrow enough that a later implementation agent can read only what applies to its packet.
8. Move stale or replaced candidate findings to `superseded` and link the replacement finding ID.

## Project Census

Record enough structure for a later agent to navigate quickly:

- Build and package tools.
- Test commands and likely slow or external tests.
- Runtime entrypoints and generated entrypoints.
- Public contract surfaces: APIs, CLI commands, config keys, environment variables, schemas, events, exported packages, documented behavior.
- Language-specific dead-code hazards from the relevant adapter files.
- Directories that appear generated, vendored, cached, or external.

## Zone Decomposition

A zone is a coherent area that can be audited with limited context. Prefer boundaries already present in the project:

- Application or package directories.
- Runtime services, CLI modules, jobs, plugins, or libraries.
- Frontend views, backend handlers, persistence, tests, build tooling, docs, and generated artifacts.
- Ownership boundaries from CODEOWNERS, module names, package files, or existing docs.

Each zone note must include:

- Files or globs included.
- Known public contracts.
- Primary tests or validation commands.
- Dependency or dynamic usage caveats.
- Open questions that block implementation.

## Parallel Audit

Parallel audit outputs must be mergeable:

- Use stable finding IDs only after reconciliation.
- Include file paths and command outputs as evidence.
- Separate confirmed behavior from inference.
- List counterevidence and skipped areas.
- Do not duplicate another zone finding unless the overlap is part of the evidence.

## Reconciliation

Reconciliation decides which candidate findings survive:

- Merge duplicates into one finding with the clearest evidence.
- Mark replaced findings as `superseded`.
- Move weak findings to `needs-evidence`, not `approved`.
- Reject findings that conflict with source-of-truth docs or observed behavior.
- Preserve uncertainty when evidence is incomplete.

## Context Hygiene

Context packets must be optimized for later reading:

- One packet should support one decision or one implementation packet.
- Include only files read for that decision.
- Summarize large logs instead of pasting them in full.
- Keep raw exploratory notes out of final packets unless they are needed evidence.
- Use exact file paths and short observed facts.
- Mark stale packets when source files or project instructions have changed.
- Do not copy temporary kit claims into project docs.

## TODO And Comment Classification

Do not treat TODO-style comments as proof by themselves. Classify each item before turning it into a finding:

| Class | Meaning | Allowed next step |
| --- | --- | --- |
| `active-task` | Work is intentionally pending and still relevant. | Create or link a finding only with supporting evidence. |
| `technical-debt` | Known compromise with no immediate failure. | Score impact and risk before proposing change. |
| `suspected-dead` | Comment or code may be obsolete. | Require language-adapter dead-code evidence. |
| `temporary-diagnostic` | Debug marker, logging, or workaround. | Verify runtime and tests before removal. |
| `migration-marker` | Transitional note during an upgrade. | Check migration state and public contracts. |
| `ownership-marker` | Explains ownership, compliance, or process. | Do not remove without source-of-truth confirmation. |
| `generated-artifact` | Appears in generated or vendored code. | Exclude unless project rules say otherwise. |

## Validation Criteria

Discovery is complete enough when:

- The census names entrypoints, tests, dependencies, and public contract surfaces.
- Each zone has a defined scope and validation path.
- Candidate findings have evidence, confidence, risk, and open questions.
- TODO classifications include evidence and do not authorize removal.
- No files outside `.optimization-kit/workspace/` were modified.
