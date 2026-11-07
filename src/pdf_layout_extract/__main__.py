"""CLI entry point for pdf_layout_extract."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from pdf_layout_extract import LayoutError, PageLayout, extract_page, to_text, words_from_dicts

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MiB


def main(argv: list[str] | None = None) -> int:
    """Run the pdf-layout-extract CLI.

    Exit codes:
      0: Success
      1: Findings or domain failure (LayoutError)
      2: Usage, I/O, or JSON parse error
    """
    if argv is None:
        argv = sys.argv[1:]

    if not argv or len(argv) != 1 or argv[0] in ("-h", "--help"):
        sys.stderr.write("Usage: python -m pdf_layout_extract <pages.json>\n")
        return 2

    filepath = argv[0]
    try:
        size = os.path.getsize(filepath)
        if size > MAX_FILE_SIZE:
            sys.stderr.write(f"Error: file exceeds 50 MiB limit ({size} bytes)\n")
            return 2
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
            data: Any = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"Error reading/parsing JSON file: {exc}\n")
        return 2

    if not isinstance(data, list):
        sys.stderr.write("Error: root JSON must be a list of page objects\n")
        return 2

    layouts: list[PageLayout] = []
    for idx, page_data in enumerate(data):
        if not isinstance(page_data, dict):
            sys.stderr.write(f"Error: page at index {idx} is not a dictionary\n")
            return 2
        if "width" not in page_data or "words" not in page_data:
            sys.stderr.write(f"Error: page at index {idx} missing 'width' or 'words'\n")
            return 2
        try:
            width = float(page_data["width"])
            words_list = page_data["words"]
            if not isinstance(words_list, list):
                sys.stderr.write(f"Error: page at index {idx} words must be a list\n")
                return 2
            words = words_from_dicts(words_list)
            layout = extract_page(words, page_width=width)
            layouts.append(layout)
        except LayoutError as exc:
            sys.stderr.write(f"Layout domain failure: {exc}\n")
            return 1
        except (ValueError, TypeError) as exc:
            sys.stderr.write(f"Invalid page structure: {exc}\n")
            return 2

    text_output = to_text(layouts)
    print(text_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
