# pdf-layout-extract

[![PyPI version](https://img.shields.io/pypi/v/trysac-pdf-layout-extract)](https://pypi.org/project/trysac-pdf-layout-extract/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-pdf-layout-extract)](LICENSE)
[![CI](https://github.com/Trysac/u110-pdf-layout-extract/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u110-pdf-layout-extract/actions/workflows/ci.yml)

Reading-order text from positioned PDF words: recursive XY-cut for columns, three-column-plus aligned regions as tables, hyphen joins, input shaped like pdfplumber words

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-pdf-layout-extract
# or
uv add trysac-pdf-layout-extract
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import pdf_layout_extract

# normalize() trims surrounding whitespace and lower-cases the text.
print(pdf_layout_extract.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    pdf_layout_extract.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
