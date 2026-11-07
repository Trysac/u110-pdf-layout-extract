# Testing

Tests cover acceptance criteria, edge cases, input validation, and the CLI.

## File structure

- `tests/test_pdf_layout_extract.py`: Contains test cases mapping to the specification requirements:
  - `test_acceptance_1_simple_words_reading_order`: Validates simple paragraph ordering.
  - `test_acceptance_2_heading_and_two_columns`: Validates recursive XY-cut column splitting.
  - `test_acceptance_3_hyphenation_joining`: Validates the hyphenation join rule.
  - `test_acceptance_4_table_detection`: Validates the table detection rule for aligned columns.
  - `test_acceptance_5_words_from_dicts_and_validation`: Validates input dictionary conversion and `LayoutError` trigger conditions (NaNs, geometric constraint violations).
  - `test_cli`: Validates `main()` entry point with valid and invalid JSON inputs.

Tests are deterministic, relying on `random.Random(7)` for shuffling tests to confirm that input word order never affects the output.
