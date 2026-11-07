# pdf-layout-extract

Reading-order text from positioned PDF words: recursive XY-cut for columns, three-column-plus aligned regions as tables, hyphen joins, input shaped like pdfplumber words.

## Problem

Plain PDF text extraction interleaves the lines of two columns, flattens tables into word soup, and breaks hyphenated words, which ruins downstream text processing. This library calculates reading order deterministically from positioned words, separate from the PDF parsing itself.

## Installation

```bash
pip install pdf-layout-extract
```

## Usage

```python
from pdf_layout_extract import Word, extract_page, to_text

words = [Word("world", 50, 10, 80, 20), Word("Hello", 10, 10, 45, 20)]
layout = extract_page(words, page_width=500)
text = to_text(layout)
assert text == "Hello world"
print(text)
```

## API Summary

- **Core Objects**: `Word` (dataclass, top-left-origin), `PageLayout`, `Block`.
- **Main Functions**: 
  - `extract_page(words, *, page_width, column_gap=18.0, row_gap=None, max_words=200_000, max_depth=32)`: Returns `PageLayout`.
  - `to_text(layout)`: Formats layout as plain text.
  - `words_from_dicts(items)`: Converts dictionaries to `Word` list.
- **Errors**: `LayoutError` with `code` (`'invalid_word'`, `'too_many_words'`, `'invalid_input'`).
- **Limits**: No PDF parsing, OCR, or image support. Coordinates must be finite, $x_1 \ge x_0$, $\text{bottom} \ge \text{top}$. Page width/gaps must be $> 0$.

## Security

See [docs/SECURITY.md](docs/SECURITY.md).
