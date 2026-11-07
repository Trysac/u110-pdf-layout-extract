"""pdf_layout_extract: reading-order text from positioned PDF words."""

from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

__all__ = [
    "Block",
    "ErrorCode",
    "LayoutError",
    "PageLayout",
    "Word",
    "__version__",
    "extract_page",
    "to_text",
    "words_from_dicts",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

ErrorCode = Literal["invalid_word", "too_many_words", "invalid_input"]


class LayoutError(Exception):
    """Base exception for all layout extraction errors."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message[:200])
        self.code: ErrorCode = code
        self.message: str = message[:200]

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True)
class Word:
    """Positioned word bounding box in top-left-origin coordinates."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float

    def __post_init__(self) -> None:
        if not isinstance(self.text, str) or not self.text:
            raise LayoutError("invalid_word", "Word text must be a non-empty string")
        for name, val in (
            ("x0", self.x0),
            ("top", self.top),
            ("x1", self.x1),
            ("bottom", self.bottom),
        ):
            if not isinstance(val, (int, float)) or not math.isfinite(val):
                raise LayoutError("invalid_word", f"Word {name} must be a finite float")
        if self.x1 < self.x0:
            raise LayoutError("invalid_word", f"x1 ({self.x1}) must be >= x0 ({self.x0})")
        if self.bottom < self.top:
            raise LayoutError("invalid_word", f"bottom ({self.bottom}) must be >= top ({self.top})")
        object.__setattr__(self, "x0", float(self.x0))
        object.__setattr__(self, "top", float(self.top))
        object.__setattr__(self, "x1", float(self.x1))
        object.__setattr__(self, "bottom", float(self.bottom))


@dataclass(frozen=True)
class Block:
    """A layout block, either a reading paragraph or an aligned table."""

    kind: Literal["paragraph", "table"]
    lines: tuple[str, ...] = ()
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class PageLayout:
    """Extracted layout of a page composed of ordered blocks."""

    blocks: tuple[Block, ...]


def words_from_dicts(items: Iterable[Mapping[str, Any]]) -> list[Word]:
    """Convert an iterable of word dictionaries into a list of Word instances."""
    words: list[Word] = []
    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise LayoutError("invalid_input", f"Item at index {idx} is not a mapping")
        for key in ("text", "x0", "x1", "top", "bottom"):
            if key not in item:
                raise LayoutError("invalid_word", f"Item at index {idx} missing key '{key}'")
        try:
            word = Word(
                text=str(item["text"]),
                x0=float(item["x0"]),
                top=float(item["top"]),
                x1=float(item["x1"]),
                bottom=float(item["bottom"]),
            )
        except LayoutError as exc:
            raise LayoutError(
                "invalid_word", f"Item at index {idx} is invalid: {exc.message}"
            ) from exc
        words.append(word)
    return words


def _median(values: Sequence[float]) -> float:
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    if n == 0:
        return 10.0
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def _build_leaf_block(words: Sequence[Word]) -> Block:
    if not words:
        return Block(kind="paragraph", lines=(), rows=())

    # Sort words deterministically by top, then x0, then text
    sorted_words = sorted(words, key=lambda w: (w.top, w.x0, w.text))

    lines_of_words: list[list[Word]] = []
    lines_top_bottom: list[list[float]] = []  # [top, bottom]

    for word in sorted_words:
        w_center = (word.top + word.bottom) / 2.0
        matched_line_idx: int | None = None
        for idx, (lt, lb) in enumerate(lines_top_bottom):
            if lt <= w_center <= lb:
                matched_line_idx = idx
                break

        if matched_line_idx is None:
            lines_of_words.append([word])
            lines_top_bottom.append([word.top, word.bottom])
        else:
            lines_of_words[matched_line_idx].append(word)
            lt, lb = lines_top_bottom[matched_line_idx]
            lines_top_bottom[matched_line_idx][0] = min(lt, word.top)
            lines_top_bottom[matched_line_idx][1] = max(lb, word.bottom)

    raw_lines: list[str] = []
    for line_words in lines_of_words:
        line_words_sorted = sorted(line_words, key=lambda w: (w.x0, w.top, w.text))
        line_text = " ".join(w.text for w in line_words_sorted)
        raw_lines.append(line_text)

    # Hyphenation pass:
    # Inside a paragraph, a line ending in a letter followed by '-' and a next line starting
    # with a lowercase letter are joined without the hyphen and the line break.
    merged_lines: list[str] = []
    i = 0
    while i < len(raw_lines):
        curr = raw_lines[i]
        while i + 1 < len(raw_lines):
            next_line = raw_lines[i + 1]
            if (
                len(curr) >= 2
                and curr.endswith("-")
                and curr[-2].isalpha()
                and len(next_line) > 0
                and next_line[0].islower()
            ):
                curr = curr[:-1] + next_line
                i += 1
            else:
                break
        merged_lines.append(curr)
        i += 1

    return Block(kind="paragraph", lines=tuple(merged_lines), rows=())


def _try_table_block(children: list[Block]) -> Block | None:
    if len(children) < 3:
        return None
    for child in children:
        if child.kind != "paragraph":
            return None
    num_lines = len(children[0].lines)
    if num_lines < 2:
        return None
    for child in children[1:]:
        if len(child.lines) != num_lines:
            return None
    return None


def _build_leaf_lines_with_tops(words: Sequence[Word]) -> list[tuple[float, str]]:
    if not words:
        return []
    sorted_words = sorted(words, key=lambda w: (w.top, w.x0, w.text))
    lines_of_words: list[list[Word]] = []
    lines_bounds: list[list[float]] = []  # [top, bottom]

    for word in sorted_words:
        w_center = (word.top + word.bottom) / 2.0
        matched_line_idx: int | None = None
        for idx, (lt, lb) in enumerate(lines_bounds):
            if lt <= w_center <= lb:
                matched_line_idx = idx
                break
        if matched_line_idx is None:
            lines_of_words.append([word])
            lines_bounds.append([word.top, word.bottom])
        else:
            lines_of_words[matched_line_idx].append(word)
            lines_bounds[matched_line_idx][0] = min(lines_bounds[matched_line_idx][0], word.top)
            lines_bounds[matched_line_idx][1] = max(lines_bounds[matched_line_idx][1], word.bottom)

    res: list[tuple[float, str]] = []
    for idx, line_words in enumerate(lines_of_words):
        sorted_w = sorted(line_words, key=lambda w: (w.x0, w.top, w.text))
        line_str = " ".join(w.text for w in sorted_w)
        line_top = lines_bounds[idx][0]
        res.append((line_top, line_str))
    return res


def _find_vertical_cuts(words: Sequence[Word], col_gap: float) -> list[list[Word]] | None:
    if not words:
        return None
    min_x = min(w.x0 for w in words)
    max_x = max(w.x1 for w in words)
    if max_x <= min_x:
        return None

    x_intervals = sorted([(w.x0, w.x1) for w in words], key=lambda iv: (iv[0], iv[1]))
    merged: list[tuple[float, float]] = []
    for start, end in x_intervals:
        if not merged:
            merged.append((start, end))
        else:
            last_s, last_e = merged[-1]
            if start <= last_e:
                merged[-1] = (last_s, max(last_e, end))
            else:
                merged.append((start, end))

    cut_points: list[float] = []
    for i in range(len(merged) - 1):
        gap = merged[i + 1][0] - merged[i][1]
        if gap >= col_gap:
            cut_points.append((merged[i][1] + merged[i + 1][0]) / 2.0)

    if not cut_points:
        return None

    children: list[list[Word]] = [[] for _ in range(len(cut_points) + 1)]
    for w in words:
        w_center_x = (w.x0 + w.x1) / 2.0
        placed = False
        for c_idx, cut in enumerate(cut_points):
            if w_center_x < cut:
                children[c_idx].append(w)
                placed = True
                break
        if not placed:
            children[-1].append(w)

    non_empty = [c for c in children if c]
    return non_empty if len(non_empty) > 1 else None


def _find_horizontal_cuts(words: Sequence[Word], row_gap: float) -> list[list[Word]] | None:
    if not words:
        return None
    min_y = min(w.top for w in words)
    max_y = max(w.bottom for w in words)
    if max_y <= min_y:
        return None

    y_intervals = sorted([(w.top, w.bottom) for w in words], key=lambda iv: (iv[0], iv[1]))
    merged: list[tuple[float, float]] = []
    for start, end in y_intervals:
        if not merged:
            merged.append((start, end))
        else:
            last_s, last_e = merged[-1]
            if start <= last_e:
                merged[-1] = (last_s, max(last_e, end))
            else:
                merged.append((start, end))

    cut_points: list[float] = []
    for i in range(len(merged) - 1):
        gap = merged[i + 1][0] - merged[i][1]
        if gap >= row_gap:
            cut_points.append((merged[i][1] + merged[i + 1][0]) / 2.0)

    if not cut_points:
        return None

    children: list[list[Word]] = [[] for _ in range(len(cut_points) + 1)]
    for w in words:
        w_center_y = (w.top + w.bottom) / 2.0
        placed = False
        for c_idx, cut in enumerate(cut_points):
            if w_center_y < cut:
                children[c_idx].append(w)
                placed = True
                break
        if not placed:
            children[-1].append(w)

    non_empty = [c for c in children if c]
    return non_empty if len(non_empty) > 1 else None


def _recursive_xy_cut(
    words: Sequence[Word],
    col_gap: float,
    row_gap: float,
    depth: int,
    max_depth: int,
) -> list[Block]:
    if not words:
        return []
    if depth >= max_depth:
        return [_build_leaf_block(words)]

    # 1. Vertical cut first
    v_groups = _find_vertical_cuts(words, col_gap)
    if v_groups is not None:
        # Check table rule on vertical cut:
        # "The children of a vertical cut form one table block when there are >= 3 children,
        # every child is a leaf with the same number (>= 2) of lines, and the i-th line tops
        # agree within 2.0 points across children; row i is the i-th line of each child."
        if len(v_groups) >= 3:
            can_be_table = True
            child_leaf_lines: list[list[tuple[float, str]]] = []
            for group in v_groups:
                # A child is a leaf if neither vertical nor horizontal cut can split it further
                if (
                    _find_vertical_cuts(group, col_gap) is not None
                    or _find_horizontal_cuts(group, row_gap) is not None
                ):
                    can_be_table = False
                    break
                lines_tops = _build_leaf_lines_with_tops(group)
                if len(lines_tops) < 2:
                    can_be_table = False
                    break
                child_leaf_lines.append(lines_tops)

            if can_be_table:
                num_lines = len(child_leaf_lines[0])
                for cl in child_leaf_lines[1:]:
                    if len(cl) != num_lines:
                        can_be_table = False
                        break

            if can_be_table:
                for line_idx in range(num_lines):
                    tops = [cl[line_idx][0] for cl in child_leaf_lines]
                    if max(tops) - min(tops) > 2.0:
                        can_be_table = False
                        break

            if can_be_table:
                table_rows: list[tuple[str, ...]] = []
                for line_idx in range(num_lines):
                    row = tuple(cl[line_idx][1] for cl in child_leaf_lines)
                    table_rows.append(row)
                return [Block(kind="table", lines=(), rows=tuple(table_rows))]

        # Otherwise, left-to-right children
        blocks: list[Block] = []
        for group in v_groups:
            blocks.extend(_recursive_xy_cut(group, col_gap, row_gap, depth + 1, max_depth))
        return blocks

    # 2. Otherwise horizontal cut
    h_groups = _find_horizontal_cuts(words, row_gap)
    if h_groups is not None:
        blocks = []
        for group in h_groups:
            blocks.extend(_recursive_xy_cut(group, col_gap, row_gap, depth + 1, max_depth))
        return blocks

    # 3. Otherwise the node is a leaf
    return [_build_leaf_block(words)]


def extract_page(
    words: Sequence[Word],
    *,
    page_width: float,
    column_gap: float = 18.0,
    row_gap: float | None = None,
    max_words: int = 200_000,
    max_depth: int = 32,
) -> PageLayout:
    """Extract reading order and layout blocks from a sequence of words."""
    if not isinstance(page_width, (int, float)) or not math.isfinite(page_width) or page_width <= 0:
        raise LayoutError("invalid_input", f"page_width must be > 0 (got {page_width})")
    if not isinstance(column_gap, (int, float)) or not math.isfinite(column_gap) or column_gap <= 0:
        raise LayoutError("invalid_input", f"column_gap must be > 0 (got {column_gap})")
    if row_gap is not None and (
        not isinstance(row_gap, (int, float)) or not math.isfinite(row_gap) or row_gap <= 0
    ):
        raise LayoutError("invalid_input", f"row_gap must be > 0 (got {row_gap})")
    if len(words) > max_words:
        raise LayoutError(
            "too_many_words",
            f"Too many words: {len(words)} exceeds limit of {max_words}",
        )

    if not words:
        return PageLayout(blocks=())

    effective_row_gap: float
    if row_gap is not None:
        effective_row_gap = float(row_gap)
    else:
        heights = [w.bottom - w.top for w in words if (w.bottom - w.top) > 0]
        effective_row_gap = _median(heights) if heights else 10.0

    blocks = _recursive_xy_cut(
        words=words,
        col_gap=float(column_gap),
        row_gap=effective_row_gap,
        depth=0,
        max_depth=max_depth,
    )
    return PageLayout(blocks=tuple(blocks))


def to_text(layout: PageLayout | Sequence[PageLayout]) -> str:
    """Format extracted layout(s) as plain reading-order text."""
    pages = [layout] if isinstance(layout, PageLayout) else list(layout)

    page_texts: list[str] = []
    for p in pages:
        block_texts: list[str] = []
        for b in p.blocks:
            if b.kind == "paragraph":
                block_texts.append("\n".join(b.lines))
            elif b.kind == "table":
                row_texts = [" | ".join(cell for cell in row) for row in b.rows]
                block_texts.append("\n".join(row_texts))
        page_texts.append("\n\n".join(bt for bt in block_texts if bt))

    return "\n\f\n".join(page_texts)
