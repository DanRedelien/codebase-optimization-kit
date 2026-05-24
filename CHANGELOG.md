# Changelog

All notable changes to `codebase-optimization-kit` will be documented here.

## 1.0.0 - 2026-05-24

### Changed

- Rebuilt the installed workspace as `.codebase-optimization-kit/`, a self-contained JSON-first runtime.
- Replaced the old markdown workflow entrypoint with `AGENT.md`.
- Added `kit.py`, a standard-library CLI for doctor, census, zone suggestion, agent planning, findings, packets, validation, locks, tool detection, contract scanning, test detection, status, and report generation.
- Added schemas, generated JSON state, JSON templates, language adapter JSON, lifecycle/risk/evidence/metrics policies, and editable dead-code and behavioral-parity policy templates.
- Made generated reports views over JSON state under `reports/`.
- Rewrote `scripts/init.py` as an optional safe copier that preserves state and never touches root `AGENTS.md`.
- Rewrote `scripts/validate.py` to delegate validation to the installed runtime.
- Strengthened active packet gates, overlap checks, schema/state validation, metric evidence checks, agent planning coverage, supporting reads, and contract-candidate detection.
- Installer now writes ignore protection to `.git/info/exclude` for git projects, with `.gitignore` fallback outside git.

### Removed

- Removed the installed markdown-heavy workflow, scoring, role, and language-adapter documents from the default runtime.
- Removed `START_HERE.md` and the manual `status.md` source file from the installed template.
- Removed empty generated state files from the shipped template except `state/project.json`; `doctor` creates runtime state on first run.
