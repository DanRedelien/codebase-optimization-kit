# Changelog

All notable changes to `codebase-optimization-kit` will be documented here.

## 1.0.0 - 2026-05-26

Initial open-source release.

`codebase-optimization-kit` is a disposable, JSON-first runtime for evidence-backed codebase optimization passes. Install `.codebase-optimization-kit/` into a target project, run the local CLI, let agents discover findings, then implement only through approved packets with validation and scope enforcement.

### Added

- Added the installed `.codebase-optimization-kit/` runtime template with `AGENT.md`, `kit.py`, schemas, policies, JSON templates, and minimal seeded state.
- Added a standard-library CLI for `doctor`, `census`, `zones suggest`, `agents plan`, `findings`, `packets`, `validate`, `report`, `contracts candidates`, `locks`, and `status`.
- Added an optional safe installer in `scripts/init.py` that preserves existing kit state, avoids root `AGENTS.md`, refuses symlink/junction installs, and writes ignore protection to `.git/info/exclude` for git projects.
- Added `scripts/validate.py` as a wrapper around installed runtime validation.
- Added JSON and JSONL schemas for project state, file records, zones, agent tasks, findings, packets, validations, locks, and metrics.
- Added generated reports for agent plans, ranked findings, implementation backlog, and final summaries.
- Added contract-candidate discovery for docs, public exports, routes/handlers, configs, package/build files, and CLI entrypoints.
- Added bounded baseline audit classification after census/zones, with explicit caps and truncation/evidence-gap reporting.
- Added compact audit lanes through `policies/audit-criteria.json`: `structural-quality`, `duplicate-logic`, `dead-code`, `dynamic-usage`, `test-reliability`, `type-contract-safety`, `security-risk`, `dependency-risk`, and `authority-drift`.
- Added generated `audit_queue` entries to agent tasks while preserving existing role labels for compatibility.
- Added category-specific finding evidence validation, including unknown-category rejection unless a project declares `custom_finding_categories`.
- Added policy-driven risk floors and packet gates for audit lanes.
- Added audit process metrics such as critical risks found before packets, blocked packets for missing evidence, duplicate findings suppressed, scan truncation, blockers, evidence completeness, and task count.
- Added `kit_runtime/audit.py` and `kit_runtime/io.py` to keep policy heuristics and runtime IO helpers out of the main CLI file.

### Changed

- Treats generated reports as views over JSON/JSONL state, not source of truth.
- Keeps `AGENT.md` short and points agents to commands and machine-readable policy.
- Uses audit lanes as compact criteria instead of shipping standalone skill markdown files.
- Maps severity into existing `risk_score`, finding status, and packet rules instead of adding a separate pass/warn/fail system.
- Queues `security-risk` only for security-sensitive path signals such as auth, session, secret, token, credential, permission, crypto, payment, env, and webhook paths.
- Preserves existing metrics: `passing_tests`, `behavioral_parity`, `dependency_reduction`, `duplicate_logic_reduction`, `dead_code_confidence`, `complexity_reduction`, `risk_score`, and `reversibility`.
- Requires risk 4 packets to carry human approval and blocks risk 5 direct implementation from the kit.
- Keeps dead-code deletion guarded by structured evidence checks across references, entrypoints, configs, tests/runtime, public contracts, generated/vendor status, and counterevidence.
- Deduplicates findings by normalized affected files, normalized root cause, and primary lane, with overlapping concerns recorded in `related_lanes`.
- Validates `audit_queue` lanes and finding categories as hard errors instead of silently falling back to broad categories.
- Keeps baseline scans bounded and incomplete-by-design when caps are hit, recording `truncated` and evidence gaps.
- Strengthened QA coverage for runtime contents, bounded task generation, audit queues, missing category evidence, security risk blocking, risk 4 approvals, and packet scope enforcement.

### Removed

- Removed the installed markdown-heavy workflow, scoring, role, and language-adapter documents from the default runtime.
- Removed standalone skill/prose criteria from the shipped runtime in favor of enforced JSON policy.
- Removed `START_HERE.md`, runtime `README.md`, generated report placeholders, adapter folders, and manual status source files from the installed template.
- Removed empty generated state files from the shipped template except `state/project.json`; `doctor` creates runtime state on first run.
- Removed temporary deep-research cache material from the release surface.

### Notes

- The runtime does not install or require external scanners.
- Project docs, tests, schemas, and contracts remain authoritative inputs, but contradictions should be recorded as `authority-drift` findings.
- Security findings are discovery/blocker signals for escalation; the kit is not a security remediation framework.

## 1.0.1 - 2026-05-26

Local maintenance update.

- Improved zone splitting for deeper `src`, `lib`, `app`, `internal`, and test trees without turning filenames such as `README.md` or `__init__.py` into zones.
- Increased agent planning scale to 24 slots and capped normal packing at 3 zones per agent slot.
- Added QA regression coverage for deep zones, file-like path segments, and large-zone-count agent planning.

## 1.0.2 - 2026-05-26

Local prompt generation update.

- Added `agents prompts` to generate one canonical copy-paste prompt per planned discovery task under `state/agent-prompts/`.
- Keeps generated prompt files in one managed location and removes stale `TASK-*.md` files before regenerating them.
- Directs each discovery agent to write findings into its own `state/task-findings/TASK-XXX.jsonl` file instead of editing `state/findings.jsonl` directly.
- Moved prompt rendering into `kit_runtime/prompts.py` so `kit.py` stays a CLI wrapper instead of growing another embedded generator.
