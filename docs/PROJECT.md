# Project record

## Objective

To provide an explainable, deterministic reading-order text extraction library that reconstructs columns and tables from positioned word bounding boxes.

## Scope

- **In scope**:
  - Implementation of the recursive XY-cut algorithm (Nagy & Seth 1984).
  - Table recognition for aligned $3+$ column regions.
  - Hyphenation joining across paragraphs.
  - Python public API (`Word`, `extract_page`, `to_text`, `words_from_dicts`).
  - CLI entry point (`python -m pdf_layout_extract`).

- **Out of scope**:
  - PDF decoding, font processing, OCR, or image handling.
  - Ruling-line based table detection.
  - Markdown output generation.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created. |

## Effort metrics

| Metric | Value |
|---|---|
| Tokens (input / output) | 1255791 / 17749 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.2895 |

## Factory run u110 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4413 | 12684 | 0 | 0 | 0.0254 |
| fix-1 | gemini-3.8-flash | no | 84032 | 1751 | 0 | 569455 | 0.1123 |
| fix-2 | gemini-3.8-flash | no | 60381 | 1550 | 0 | 233985 | 0.0686 |
| fix-3 | gemini-3.8-flash | no | 34727 | 302 | 0 | 47865 | 0.0308 |
| audit | gemini-3.1-flash-lite | no | 35235 | 147 | 0 | 22368 | 0.0096 |
| docs | gemini-3.1-flash-lite | no | 163330 | 1315 | 0 | 0 | 0.0428 |

Total: $0.2895. Prices: Anthropic list prices.
