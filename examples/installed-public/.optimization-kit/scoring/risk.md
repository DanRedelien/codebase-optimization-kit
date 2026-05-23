# Risk Score

Risk measures how dangerous the proposed change is. It controls approval requirements through `risk-policy.md`.

## Inputs

- Proposed implementation scope.
- Files and public contracts touched.
- Dependency, schema, build, deployment, and runtime effects.
- Test coverage and rollback confidence.
- Language adapter dynamic usage risks.

## Score

| Score | Meaning | Typical change |
| --- | --- | --- |
| 1 | Very low risk. | Comment, local test, or isolated internal cleanup with direct validation. |
| 2 | Low risk. | Small internal change with clear tests and no public contract impact. |
| 3 | Moderate risk. | Multi-file internal change, removal, refactor, or behavior-sensitive fix requiring an implementation packet. |
| 4 | High risk. | Public contract, dependency, migration, generated code, build, release, or security-sensitive change requiring explicit human approval. |
| 5 | Critical risk. | Architecture, data model, compatibility, security posture, or cross-system change requiring RFC/ADR and no direct implementation. |

## Risk Raisers

- Public contract changes.
- Dependency additions, removals, upgrades, or lockfile churn.
- Database migrations or serialized data format changes.
- Authentication, authorization, payments, privacy, security, or compliance code.
- Generated code, native bindings, reflection, macros, plugin registries, or dynamic loading.
- Broad formatting mixed with behavior changes.
- Weak test coverage or unclear rollback.

## Rules

- Score risk for the actual proposed change, not just the finding.
- When uncertain between two scores, choose the higher score.
- Risk can be high even when impact is low.
- Lower risk only when evidence and validation reduce implementation danger.
- Apply `risk-policy.md` after scoring.

## Output Format

```text
Risk: <1-5>
Reason:
Risk raisers:
Risk reducers:
Required policy path:
```
