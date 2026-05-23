# Scoring

Scoring helps rank findings and choose the required approval path. It does not authorize implementation by itself.

Read only the files needed for the current decision:

| File | Purpose |
| --- | --- |
| `impact.md` | How much the issue matters if the claim is true. |
| `confidence.md` | How strong the evidence is. |
| `risk.md` | How dangerous the proposed change is. |
| `priority.md` | How to rank work after impact, confidence, and risk are known. |
| `risk-policy.md` | Required approval and implementation path by risk level. |

The scoring rubric is split across these files to keep context small. Risk policy is the controlling contract.
