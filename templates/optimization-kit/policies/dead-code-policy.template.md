# Dead Code Policy Template

Use this file to strengthen project-specific dead-code rules before approving removals.

## Required Classification

Choose one: `truly_unreachable`, `unused_internal_export`, `unused_public_export`, `legacy_branch`, `duplicate_implementation`, `dormant_planned_code`, `external_contract_code`, `dynamic_usage_unknown`, `generated_or_vendor_code`.

## Required Checks Before Deletion

- Static references checked: `<command, query, or method>`
- Runtime entrypoints checked: `<entrypoints and routing paths>`
- Config, registry, plugin, or reflection usage checked: `<files and result>`
- Tests or runtime exercise checked: `<commands or manual evidence>`
- Public exports/contracts checked: `<contracts and result>`
- Generated/vendor status checked: `<result>`
- Counterevidence and gaps recorded: `<known uncertainty>`

If any field is incomplete, the finding status must be `needs-evidence` and the packet must not be approved for deletion.
