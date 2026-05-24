# Project Dead Code Policy

Fill this file with project-specific dead-code rules before approving removals.

Required checks before deletion:

- Static references checked: `<command, query, or method>`
- Runtime entrypoints checked: `<entrypoints and routing paths>`
- Config, registry, plugin, or reflection usage checked: `<files and result>`
- Tests or runtime exercise checked: `<commands or manual evidence>`
- Public exports/contracts checked: `<contracts and result>`
- Generated/vendor status checked: `<result>`
- Counterevidence and gaps recorded: `<known uncertainty>`

If any field is incomplete, the finding status must be `needs-evidence` and the packet must not be approved for deletion.
