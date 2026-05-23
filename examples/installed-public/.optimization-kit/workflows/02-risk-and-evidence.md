# Workflow 02: Risk And Evidence

Use this workflow to decide whether a finding is actionable. It combines the evidence standard, public contract checks, dependency evaluation, behavioral parity requirements, scoring usage, and explicit approval rules.

## Inputs

- Candidate findings and context packets from `.optimization-kit/workspace/`.
- Relevant language adapter files.
- `.optimization-kit/scoring/impact.md`
- `.optimization-kit/scoring/confidence.md`
- `.optimization-kit/scoring/risk.md`
- `.optimization-kit/scoring/priority.md`
- `.optimization-kit/scoring/risk-policy.md`
- Project source-of-truth docs and public contract references.

## Outputs

Write outputs under `.optimization-kit/workspace/`:

- Evidence updates to findings.
- Risk and priority notes.
- Draft implementation packets.
- Decision files when a human records approval outside an implementation packet.
- Durable-knowledge promotion proposals, when a finding exposes lasting project knowledge.

## Allowed Writes

- `.optimization-kit/workspace/**`

Draft packets and decisions written here do not authorize source edits until they are approved by the required human owner.

## Forbidden Actions

- Do not implement changes from this workflow.
- Do not change dependency files.
- Do not approve Risk 4 work as an agent.
- Do not downgrade risk to avoid approval.
- Do not treat another agent's agreement as explicit approval.
- Do not write to `docs/` by default.

## Checklist

1. Restate the finding as one testable claim.
2. Collect direct evidence and counterevidence.
3. Identify all public contracts touched by the proposed change.
4. Evaluate dependency impact if package files, lockfiles, imports, or runtime loaders are involved.
5. Define behavioral parity: what must remain the same before and after the change.
6. Score impact, confidence, risk, and priority using the scoring files.
7. Apply `.optimization-kit/scoring/risk-policy.md`.
8. For Risk 4, stop until explicit human approval is recorded in an implementation packet or decision file.
9. For Risk 5, route to RFC/ADR. Do not produce an implementation packet for direct code changes.

## Evidence Standard

Every actionable finding must include:

- Claim: one concise statement.
- Evidence: file paths, command output summaries, tests, traces, or runtime observations.
- Counterevidence: why the claim might be wrong or limited.
- Affected behavior: user, maintainer, performance, security, reliability, or test impact.
- Public contracts: any API, CLI, config, schema, event, package export, file format, or documented behavior touched.
- Confidence score and reason.
- Risk score and reason.
- Validation path that can prove the change is correct.

Evidence is insufficient when it is based only on naming, age, comments, unused-looking files, or an agent's expectation of how a framework works.

## Public Contracts

Treat these as public contracts unless project authority files say otherwise:

- HTTP routes, RPC methods, GraphQL schema, webhooks, events, and background job names.
- CLI commands, flags, exit codes, stdin/stdout formats, and config files.
- Environment variables and feature flags.
- Database schema, migrations, serialized data, cache keys, and file formats.
- Package exports, generated clients, plugin APIs, and extension points.
- Documented behavior in README, docs, examples, changelogs, and tests.

If a public contract changes, the finding must explain compatibility, migration, and validation. Public contract changes usually raise risk.

## Dependency Evaluation

Before adding, removing, or upgrading a dependency:

- Identify direct and transitive dependency files, lockfiles, workspace manifests, and generated metadata.
- List import sites, runtime loading paths, CLI usage, build plugins, test fixtures, and deployment references.
- Check whether the dependency participates in public contracts, code generation, native builds, licenses, or security posture.
- Define rollback steps for package and lockfile changes.
- Require validation commands that exercise install, build, tests, and at least one runtime path affected by the dependency.

Do not remove a dependency only because static import search is empty. Dynamic loaders, plugins, configuration files, reflection, macros, framework conventions, and generated code can all create real usage.

## Behavioral Parity

For refactors and removals, define parity before implementation:

- Existing public inputs and outputs that must stay unchanged.
- Error behavior and edge cases that must remain compatible.
- Performance or resource expectations, when relevant.
- Test fixtures, snapshots, migrations, and generated artifacts that must remain stable.
- Known intentional behavior changes, if any, with approval requirements.

If parity cannot be stated, the finding is not ready for implementation.

## Scoring Usage

Use scoring to guide decisions, not to override policy:

- `impact.md`: how much the issue matters if true.
- `confidence.md`: how strong the evidence is.
- `risk.md`: how dangerous the proposed change is.
- `priority.md`: how to rank work after impact, confidence, and risk are known.
- `risk-policy.md`: required approval path by risk level.

Priority never grants permission to skip an implementation packet, validation, or explicit human approval.

## Explicit Approval Rules

Risk 4 approval means human approval only. It must be recorded before implementation in one of these places:

- The `Approval` section of an implementation packet.
- A decision file under `.optimization-kit/workspace/decisions/`.

The approval record must include:

- Human approver name or handle.
- Approval date.
- Related finding IDs.
- Approved risk level and scope.
- Allowed files or approved contract changes.
- Validation and rollback expectations.

Another agent, automated reviewer, CI result, or inferred silence does not count as approval.

## Validation Criteria

Risk and evidence review is complete enough when:

- Each actionable finding has direct evidence and counterevidence.
- Public contracts and dependency effects are explicitly listed.
- Behavioral parity is defined or the intentional behavior change is approved.
- Impact, confidence, risk, and priority are scored with reasons.
- Risk policy has been applied without exception.
