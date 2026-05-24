# Removal And Archive

The kit is temporary. Remove or archive it after the final report is exported and accepted changes are merged or abandoned.

## Before Removal

- Generate `reports/final-report.md`.
- Confirm accepted changes are merged.
- Confirm rollback notes are no longer needed or are archived.
- Promote durable knowledge through the project's normal approval process if needed.

## Remove

Delete the installed runtime directory:

```text
.codebase-optimization-kit/
```

Then remove the managed `.git/info/exclude` or `.gitignore` marker block if no future kit work is planned.

## Archive

If an audit trail is needed, archive only the final report, approved packets, validation records, rollback records, and approved decisions. Do not archive raw private data by default.
