# Priority Score

Priority ranks which approved findings should be addressed first. Priority does not bypass risk policy, implementation packets, or human approval.

## Inputs

- Impact score.
- Confidence score.
- Risk score.
- Urgency, owner availability, release timing, and validation cost.
- Dependencies between findings.

## Priority Bands

| Band | Meaning | Use when |
| --- | --- | --- |
| P0 | Immediate blocker. | Critical production, release, security, or data issue with strong evidence. |
| P1 | High priority. | High impact and strong confidence, or important risk reduction before planned work. |
| P2 | Normal priority. | Meaningful impact with adequate confidence and manageable risk. |
| P3 | Opportunistic. | Useful but low impact, low confidence, or blocked by other work. |
| P4 | Do not pursue now. | Weak evidence, poor cost/benefit, rejected, superseded, or not aligned with goals. |

## Suggested Mapping

- P0: Impact 5, confidence 4-5, urgent, and owner agrees.
- P1: Impact 4-5 with confidence 3-5.
- P2: Impact 3 with confidence 3-5 and risk 1-3.
- P3: Impact 1-2 or confidence 2, unless bundled with approved work.
- P4: Confidence 1, rejected, superseded, or no validation path.

Raise or lower priority only with a written reason.

## Rules

- High priority does not lower risk.
- Low risk does not raise priority unless impact and confidence justify it.
- Risk 4 still needs explicit human approval.
- Risk 5 still requires RFC/ADR and no direct implementation.
- Dependencies between findings should be listed before ranking.

## Output Format

```text
Priority: <P0-P4>
Reason:
Depends on:
Blocked by:
```
