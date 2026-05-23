# Workflow 04: Validation, Rollback, And Archive

Use this workflow after implementation or when closing an optimization pass. It covers validation, rollback, final summary export, durable knowledge promotion, and archive/delete rules for `.optimization-kit/`.

## Inputs

- Approved implementation packets.
- Related findings and context packets.
- Rollback plans.
- Validation command outputs.
- Final summary draft.
- Durable-knowledge promotion proposals.
- Root project docs and project source-of-truth files.

## Outputs

Write outputs under `.optimization-kit/workspace/` unless an approved packet or approved promotion proposal allows another path:

- Validation reports.
- Rollback execution notes.
- Final summary.
- Durable-knowledge promotion proposals.
- Archive manifest, if archiving.

## Allowed Writes

- `.optimization-kit/workspace/**`
- Files listed in an approved rollback plan when executing rollback.
- Files listed in an approved durable-knowledge promotion proposal.

## Forbidden Actions

- Do not delete `.optimization-kit/` before the final summary is exported and accepted.
- Do not archive raw private or sensitive data into durable project docs.
- Do not promote temporary findings directly into `docs/`.
- Do not execute rollback outside the approved rollback scope.
- Do not mark findings `validated` without validation evidence.
- Do not treat validation skipped for convenience as success.

## Checklist

1. Match each implemented finding to its validation commands.
2. Run validation commands or record why each command is not runnable.
3. Compare behavior against the packet's behavioral parity requirements.
4. Update finding statuses to `validated`, `rolled-back`, `needs-evidence`, or another accurate status.
5. Confirm rollback plans still match the final diff.
6. Export a final summary using `.optimization-kit/templates/final-summary.template.md`.
7. Review durable-knowledge promotion proposals for human approval.
8. Decide whether to delete or archive `.optimization-kit/`.

## Validation

Validation evidence must include:

- Command or manual check performed.
- Expected result.
- Actual result.
- Files, routes, entrypoints, or contracts exercised.
- Known gaps and residual risk.

A finding can be marked `validated` only when the validation evidence covers the claim and the implemented change.

## Rollback

Rollback is allowed when:

- The rollback plan identifies exact files and behavior to restore.
- The rollback scope does not exceed the implementation packet.
- Public contracts and data migrations are accounted for.
- Validation after rollback is defined.

Rollback notes must record:

- Trigger for rollback.
- Files changed.
- Commands run.
- Result after rollback.
- Findings moved to `rolled-back` or `needs-evidence`.

## Final Summary Export

The final summary must include:

- Accepted, rejected, superseded, implemented, validated, and rolled-back findings.
- Files changed by implementation packets.
- Validation commands and results.
- Remaining risks and skipped validation.
- Durable-knowledge promotion decisions.
- Cleanup decision for `.optimization-kit/`.

The summary is the portable output of the temporary workspace. It does not replace project docs.

## Durable Knowledge Promotion

Promote only knowledge that is durable after the optimization pass:

- New or changed public contracts.
- Architecture decisions accepted by project owners.
- Operational procedures that future maintainers need.
- Test or validation knowledge that belongs in project docs.

Promotion requires an approved proposal that states:

- Source finding or implementation packet.
- Exact target file.
- Exact content or summary to add.
- Human approver.
- Reason the knowledge is durable.

The kit never writes to `docs/` by default. Project docs may be changed only when an approved promotion proposal or implementation packet lists the target file.

## Archive Or Delete

It is safe to delete `.optimization-kit/` when:

- The final summary is exported.
- Accepted changes are merged or otherwise captured by the project.
- Durable promotion proposals are completed, rejected, or intentionally deferred.
- No open rollback plan depends on temporary workspace-only information.
- The cleanup decision says deletion is allowed.

Archive instead of delete when the project needs an audit trail. A minimal archive should include:

- Manifest.
- Final summary.
- Approved implementation packets.
- Validation reports.
- Rollback plans.
- Approved durable-knowledge promotion proposals.

Do not archive cache files, raw sensitive logs, private notes, or generated noise unless project policy explicitly requires it.

## Validation Criteria

Closure is complete enough when:

- Every implemented finding has a final lifecycle status.
- Validation and rollback evidence is recorded.
- Durable knowledge was promoted only through approval.
- The final summary clearly states whether `.optimization-kit/` can be deleted or should be archived.
