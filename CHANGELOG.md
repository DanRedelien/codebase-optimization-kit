# Changelog

All notable changes to `codebase-optimization-kit` will be documented here.

## 0.1.0 - Unreleased

### Added

- Initial v0.1.0 release of the temporary `.optimization-kit/` audit/refactor workspace.
- English-only workspace templates for agent startup, safety boundaries, status tracking, safe deletion, and optional `AGENTS.md` merge guidance.
- Grouped workflow guidance for discovery, risk and evidence review, implementation, validation, rollback, archive, QA, and review.
- Core agent safety rules: discovery writes stay inside `.optimization-kit/workspace/`, implementation writes stay within approved packet scope, and project docs remain the source of truth.
- Stable finding IDs and lifecycle statuses, including `superseded` for replaced findings.
- Manifest template with schema version, migration policy, kit-owned overwrite allowlist, GitHub template metadata, and protected workspace paths.
- Artifact templates for findings, context packets, implementation packets, final summaries, rollback plans, durable-knowledge promotion proposals, and decision records.
- Scoring contracts for impact, confidence, risk, priority, and risk policy.
- Risk 4 explicit human approval rule and Risk 5 RFC/ADR rule.
- Language adapters for Python, TypeScript/JavaScript, Rust, Go, Java/JVM, and C/C++.
- Safe installer at `scripts/init.py` with dry-run, private workspace, GitHub templates, custom target directory, marker-managed `.gitignore`, and conservative overwrite behavior.
- Validator at `scripts/validate.py` for manifest fields, required files, protected artifacts, migration policy, ignore rules, GitHub templates, English text, internal Markdown links, and optional working-tree packet checks.
- Adoption, update, open-source, MCP roadmap, and removal/archive docs.
- Separate QA Agent and Review Agent role guidance with advisory v0.1 lock markers.
