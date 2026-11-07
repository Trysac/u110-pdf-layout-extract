# Security notes

## Threat model

`pdf-layout-extract` operates as a pure library without I/O or external dependencies.

- **Defended**:
  - **Input Validation**: The library strictly validates input coordinates (NaN/infinite checks, geometric ordering) and object structures. All `LayoutError` exceptions explicitly sanitize messages to length 200 to prevent buffer-related risks.
  - **Execution**: The library does not use `eval`, `exec`, or unsafe deserialization.

- **Not defended**:
  - **Algorithmic Complexity**: Extremely pathological inputs (e.g., $10^6$ overlapping boxes) are limited by `max_words` and `max_depth` to prevent resource exhaustion.
  - **Data Privacy**: The library processes provided in-memory text; it assumes the caller has authorization to process the input strings.
