# Workflow 03: Implementation

Use this workflow only after an implementation packet is approved. It covers packet requirements, allowed file scope, small-diff rules, implementation constraints, and review-agent checks.

## Inputs

- Approved implementation packet.
- Related findings and context packets.
- Relevant language adapter files.
- Root `AGENTS.md` and project docs.
- Rollback plan.
- Validation commands from the packet.
- Explicit human approval record for Risk 4 work, if applicable.

## Outputs

- Source changes limited to approved files.
- Test, build, or validation results.
- Updated kit artifacts only if those files are listed in the packet.
- Completion notes for the final summary.

## Allowed Writes

- Only files listed in the approved implementation packet.

If another file must change, stop and request packet reconciliation. Do not make the change first.

## Forbidden Actions

- Do not modify files outside the packet.
- Do not broaden formatting to unrelated files.
- Do not change public contracts unless the packet explicitly approves the contract change.
- Do not add, remove, or upgrade dependencies unless dependency files and validation are listed.
- Do not write to `docs/` by default.
- Do not implement Risk 4 work without recorded human approval.
- Do not implement Risk 5 work directly.

## Checklist

1. Confirm the implementation packet is approved and complete.
2. Confirm every intended file change is listed in the packet.
3. Confirm risk policy requirements are satisfied before editing.
4. Read the relevant source files and project instructions.
5. Make the smallest coherent change that satisfies the packet objective.
6. Run packet validation commands or record why they are not runnable.
7. Confirm public contracts, dependency files, and behavioral parity match the packet.
8. Confirm rollback steps still match the final diff.
9. Prepare completion notes for review and final summary.

## Implementation Packet Requirements

An implementation packet is actionable only when it includes:

- Status marked `approved`.
- Related finding IDs.
- Objective and explicit non-goals.
- Complete allowed file list with allowed change per file.
- Public contracts touched or a statement that none are touched.
- Dependency changes or a statement that none are changed.
- Risk level, approver requirements, and approval record.
- Behavioral parity requirements.
- Validation commands with expected results.
- Rollback reference.

If any item is missing, move the packet back to draft or request reconciliation.

## Small Diff Rules

- Implement one coherent finding or packet objective at a time.
- Prefer minimal edits that preserve existing style and local patterns.
- Avoid drive-by cleanup, renames, broad reformatting, and unrelated test rewrites.
- Keep mechanical changes separate from behavioral changes when possible.
- Do not delete code unless the packet includes dead-code evidence and rollback steps.
- Preserve public contract behavior unless the packet explicitly approves a change.

## Implementation Constraints

- Read the relevant code before editing.
- Confirm tests or validation commands can exercise the changed path.
- If validation is not runnable, record the reason and the risk.
- If the implementation contradicts the packet, stop and revise the packet.
- If evidence changes during implementation, update the finding status through the approved artifact path.

## Review Agent Checklist

Review agents should verify:

- Every modified file appears in the approved packet.
- The implemented behavior matches the objective and non-goals.
- Public contracts are preserved or approved changes are documented.
- Dependency changes match the dependency evaluation.
- Risk 4 work has human approval recorded before implementation.
- Risk 5 work was not directly implemented.
- Validation commands were run or clearly marked not runnable.
- Rollback steps still match the final diff.
- Findings were not promoted into durable docs without an approved promotion proposal.

## Validation Criteria

Implementation is complete enough when:

- The diff is limited to approved files.
- Validation evidence exists for the packet objective.
- Any skipped validation has a concrete reason.
- The rollback plan can restore the changed files or behavior.
- Completion notes are ready for the final summary.
