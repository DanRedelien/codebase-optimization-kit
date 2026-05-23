# Confidence Score

Confidence measures how strongly the evidence supports the finding. It does not measure impact or risk.

## Inputs

- Direct file references.
- Test or command results.
- Runtime traces, logs, or manual reproduction notes.
- Counterevidence and unresolved questions.
- Relevant language adapter caveats.

## Score

| Score | Meaning | Required support |
| --- | --- | --- |
| 1 | Speculative. | Naming, comments, or intuition only. |
| 2 | Plausible but weak. | Some static evidence, significant gaps remain. |
| 3 | Supported. | Direct code evidence and a credible validation path. |
| 4 | Strong. | Code evidence plus tests, runtime behavior, or maintainer confirmation. |
| 5 | Proven. | Reproduced issue or validated behavior with clear counterevidence addressed. |

## Rules

- Dead-code findings rarely exceed confidence 3 without dynamic usage checks.
- Dependency-removal findings require import, config, build, and runtime-loader evidence.
- Public contract findings require evidence from code and docs or tests.
- Lower confidence when generated code, reflection, macros, plugins, or framework conventions may hide usage.
- Another agent's agreement is not evidence by itself.

## Output Format

```text
Confidence: <1-5>
Reason:
Direct evidence:
Counterevidence:
Open questions:
```
