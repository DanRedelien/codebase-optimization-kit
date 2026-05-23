# Impact Score

Impact measures how much the project benefits if the finding is true and fixed. It does not measure implementation danger; use `risk.md` for that.

## Inputs

- Finding claim and evidence.
- Affected users, maintainers, systems, or workflows.
- Public contracts touched.
- Test, performance, reliability, or security evidence.

## Score

| Score | Meaning | Typical evidence |
| --- | --- | --- |
| 1 | Cosmetic or local maintainability issue. | Small cleanup, clearer naming, isolated duplicate code. |
| 2 | Minor reliability, test, or maintainability gain. | Local flake, narrow dead branch, small confusion for one module. |
| 3 | Meaningful project maintenance or behavior improvement. | Repeated bug source, confusing module boundary, slow common test path. |
| 4 | Broad user, operational, performance, or developer impact. | Public workflow affected, frequent failure mode, major build or runtime cost. |
| 5 | Critical correctness, availability, data, security, or release impact. | Data loss risk, security exposure, release blocker, widespread breakage. |

## Rules

- Score the impact of the problem, not the size of the proposed fix.
- Use the lowest score supported by evidence.
- Raise impact only when evidence shows real reach or severity.
- If impact depends on an assumption, lower confidence instead of inflating impact.
- Public contract breakage can raise impact even when the code change is small.

## Output Format

```text
Impact: <1-5>
Reason:
Evidence:
Affected users or maintainers:
```
