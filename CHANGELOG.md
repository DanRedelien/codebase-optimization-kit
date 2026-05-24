# Changelog

All notable changes to `codebase-optimization-kit` will be documented here.

## 0.1.0 - Unreleased

### Added

- Phase 1 product skeleton.
- Temporary `.optimization-kit/` workspace templates.
- Core safety rules for discovery and implementation agents.
- Finding lifecycle with `superseded` status for replaced findings.
- Manifest template with schema version and migration policy.
- Artifact templates for findings, context packets, implementation packets, final summaries, rollback plans, and durable-knowledge promotion proposals.
- Grouped Phase 2 workflows for discovery, risk/evidence, implementation, and validation/rollback/archive.
- Scoring contracts for impact, confidence, risk, priority, and risk policy.
- Risk 4 explicit human approval rule and Risk 5 RFC/ADR rule.
- Language adapters for Python, TypeScript/JavaScript, Rust, Go, Java/JVM, and C/C++.
- Decision-record template for human approvals and other temporary kit decisions.
- Phase 3 safe installer at `scripts/init.py`.
- Generated install manifest with kit-owned overwrite allowlist and protected workspace paths.
- Marker-managed `.gitignore` block for optimization-kit ignore rules.
- Phase 4 validator at `scripts/validate.py`.
- Optional GitHub issue and pull request templates for `--with-github`.
- Public and private installed examples.
- Adoption, update, open-source, MCP roadmap, and removal/archive docs.
- Separate QA Agent and Review Agent role guidance.
- Phase 5 QA/review workflow with advisory v0.1 lock guidance.
