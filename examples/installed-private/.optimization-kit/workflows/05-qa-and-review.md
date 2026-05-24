# Workflow 05: QA And Review

Use this workflow after implementation changes and before final validation or archive. It separates command and filesystem QA from policy and wording review so one agent does not blur operational checks with product-safety review.

## Inputs

- Approved implementation packet and related findings.
- Installer, validator, or project changes under review.
- Validation commands and expected results.
- Relevant role files in `roles/`.
- Root `AGENTS.md`, project docs, and active project constraints.

## Outputs

- QA notes for command behavior, idempotency, and filesystem effects.
- Review notes for safety policy, wording, ambiguity, and overwrite risk.
- Updated finding, packet, or final-summary notes when the review result changes status.
- Explicit unresolved questions before any finding is marked `validated`.

## Agent Split

Use two separate review roles when possible:

- QA Agent: checks commands, idempotency, filesystem behavior, installer recovery, validator behavior, and reproducibility.
- Review Agent: checks safety policy, wording clarity, agent ambiguity, overwrite risks, public-contract impact, and temporary-tool positioning.

The same person or model may run both roles only if the notes are separated under distinct headings.
Neither role may directly move findings to `validated`; validation status changes must follow the approved artifact path.

## QA Agent Checklist

1. Run the commands listed in the implementation packet or record why they cannot run.
2. Confirm repeated commands are idempotent.
3. Confirm dry-run commands write nothing.
4. Confirm installer recovery fills missing kit files in a partial install.
5. Confirm existing project artifacts are not overwritten.
6. Confirm root `AGENTS.md`, existing docs, private files, cache files, findings, context packets, implementation packets, decisions, and reports are preserved.
7. Confirm `.gitignore` managed entries are not duplicated.
8. Confirm private workspace folders are created only when requested and are ignored.
9. Confirm validation output distinguishes errors from warnings.

## Review Agent Checklist

1. Confirm the change still treats `.optimization-kit/` as temporary workflow tooling.
2. Confirm root project instructions and docs remain the source of truth.
3. Confirm discovery and implementation write boundaries are clear.
4. Confirm Risk 4 and Risk 5 approval rules are preserved.
5. Confirm overwrite behavior is limited to known kit-owned files.
6. Confirm project-specific artifacts remain protected, including workspace maps, findings, reports, context packets, implementation packets, decisions, locks, private files, cache files, and raw files.
7. Confirm wording does not imply that findings are durable source of truth before acceptance and validation.
8. Confirm agent names do not create ambiguous authority.
9. Confirm durable knowledge promotion requires the promotion workflow.

## Partial Install Recovery Test

Create a project that already contains only part of `.optimization-kit/`, including at least one existing workspace artifact:

```text
project/
  AGENTS.md
  docs/existing.md
  .optimization-kit/
    START_HERE.md
    workspace/
      README.md
      findings/ARCH-001.md
      context-packets/CTX-001.md
```

Then rerun the installer. Expected result:

- Missing kit files are created.
- Existing `START_HERE.md` is skipped unless explicit overwrite is allowed.
- Existing workspace artifacts are not overwritten even when `--overwrite-kit-files` is later used.
- Root `AGENTS.md` and `docs/existing.md` are untouched.
- `.gitignore` contains one managed block with no duplicate entries.
- `scripts/validate.py` succeeds after recovery.

## v0.1 Concurrency Rule

Agents must not edit the same finding, context packet, implementation packet, decision, report, or lock file concurrently.

When active parallel work needs a visible marker, an agent may create:

```text
.optimization-kit/workspace/locks/<id>.lock
```

The lock file is advisory in v0.1. It should include owner, scope, started time, and expected cleanup condition. Full lock acquisition, stale-lock detection, and lock release automation are deferred to v0.2.

## Completion Criteria

Phase 5 review is complete enough when:

- QA notes cover commands, idempotency, filesystem behavior, and partial install recovery.
- Review notes cover safety policy, wording, agent ambiguity, and overwrite risk.
- Any failures are fixed or explicitly recorded as unresolved.
- Findings or implementation packets are updated only through the approved artifact path.
