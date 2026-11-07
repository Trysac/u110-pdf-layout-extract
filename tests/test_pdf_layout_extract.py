"""Tests for pdf_layout_extract covering all acceptance criteria, edge cases, and CLI."""

from __future__ import annotations

import json
import random
from typing import Any

import pytest

from pdf_layout_extract import (
    LayoutError,
    Word,
    extract_page,
    to_text,
    words_from_dicts,
)
from pdf_layout_extract.__main__ import main


def test_acceptance_1_simple_words_reading_order() -> None:
    """Acceptance item 1: to_text of extracted words gives reading order."""
    words = [Word("world", 50, 10, 80, 20), Word("Hello", 10, 10, 45, 20)]
    layout = extract_page(words, page_width=500)
    assert to_text(layout) == "Hello world"


def test_acceptance_2_heading_and_two_columns() -> None:
    """Acceptance item 2: A full-width heading 'Title' (x 10-400, top 0, bottom 10) above
    a left column 'A1', 'A2' (x 10-100, tops 22 and 34) and a right column 'B1', 'B2'
    (x 300-400, same tops, height 10) renders as 'Title\n\nA1\nA2\n\nB1\nB2'"""
    words = [
        Word("Title", 10, 0, 400, 10),
        Word("A1", 10, 22, 100, 32),
        Word("A2", 10, 34, 100, 44),
        Word("B1", 300, 22, 400, 32),
        Word("B2", 300, 34, 400, 44),
    ]
    layout = extract_page(words, page_width=500)
    rendered = to_text(layout)
    assert rendered == "Title\n\nA1\nA2\n\nB1\nB2"


def test_acceptance_3_hyphenation_joining() -> None:
    """Acceptance item 3: Lines 'infor-' and 'mation here' of one paragraph render as
    'information here', while 'well-' followed by 'Known' renders as 'well-\nKnown'"""
    words1 = [
        Word("infor-", 10, 10, 50, 20),
        Word("mation", 10, 25, 50, 35),
        Word("here", 55, 25, 80, 35),
    ]
    layout1 = extract_page(words1, page_width=300)
    assert to_text(layout1) == "information here"

    words2 = [
        Word("well-", 10, 10, 40, 20),
        Word("Known", 10, 25, 50, 35),
    ]
    layout2 = extract_page(words2, page_width=300)
    assert to_text(layout2) == "well-\nKnown"


def test_acceptance_4_table_detection() -> None:
    """Acceptance item 4: Three column regions x 10-50, 80-110 and 140-180 each with two lines
    at tops 10 and 22 ('Name', 'Pen' / 'Qty', '2' / 'Price', '1.50') produce one Block with kind
    'table' and rows [['Name', 'Qty', 'Price'], ['Pen', '2', '1.50']], rendered as
    'Name | Qty | Price\nPen | 2 | 1.50'"""
    words = [
        Word("Name", 10, 10, 50, 20),
        Word("Pen", 10, 22, 50, 32),
        Word("Qty", 80, 10, 110, 20),
        Word("2", 80, 22, 110, 32),
        Word("Price", 140, 10, 180, 20),
        Word("1.50", 140, 22, 180, 32),
    ]
    layout = extract_page(words, page_width=250)
    assert len(layout.blocks) == 1
    block = layout.blocks[0]
    assert block.kind == "table"
    assert block.rows == (("Name", "Qty", "Price"), ("Pen", "2", "1.50"))
    assert [list(r) for r in block.rows] == [["Name", "Qty", "Price"], ["Pen", "2", "1.50"]]
    assert to_text(layout) == "Name | Qty | Price\nPen | 2 | 1.50"


def test_acceptance_5_words_from_dicts_and_validation() -> None:
    """Acceptance item 5: words_from_dicts converts dictionaries and validates coordinates."""
    dict_item = {"text": "a", "x0": 1, "x1": 2, "top": 3, "bottom": 4, "fontname": "F1"}
    res = words_from_dicts([dict_item])
    assert res == [Word("a", 1.0, 3.0, 2.0, 4.0)]

    with pytest.raises(LayoutError) as exc_info1:
        words_from_dicts([{"text": "bad", "x0": 10, "x1": 5, "top": 1, "bottom": 2}])
    assert exc_info1.value.code == "invalid_word"
    assert "index 0" in str(exc_info1.value)

    with pytest.raises(LayoutError) as exc_info2:
        words_from_dicts(
            [
                {"text": "ok", "x0": 1, "x1": 2, "top": 3, "bottom": 4},
                {"text": "nan", "x0": float("nan"), "x1": 2, "top": 3, "bottom": 4},
            ]
        )
    assert exc_info2.value.code == "invalid_word"
    assert "index 1" in str(exc_info2.value)


def test_acceptance_6_limits_and_recursion_depth() -> None:
    """Acceptance item 6: word count limits and recursion depth cap."""
    dummy_words = [Word(f"w{i}", 10.0, 10.0, 20.0, 20.0) for i in range(10)]
    with pytest.raises(LayoutError) as exc_info:
        extract_page(dummy_words, page_width=500, max_words=5)
    assert exc_info.value.code == "too_many_words"

    staircase = [
        Word(f"w{i}", float(i * 30), float(i * 30), float(i * 30 + 10), float(i * 30 + 10))
        for i in range(100)
    ]
    layout = extract_page(staircase, page_width=5000, column_gap=15.0, row_gap=15.0, max_depth=32)
    assert len(layout.blocks) > 0


def test_acceptance_7_shuffling_determinism() -> None:
    """Acceptance item 7: Shuffling the input words with random.Random(7) gives an identical
    to_text result for every fixture page"""
    fixture = [
        Word("Title", 10, 0, 400, 10),
        Word("A1", 10, 22, 100, 32),
        Word("A2", 10, 34, 100, 44),
        Word("B1", 300, 22, 400, 32),
        Word("B2", 300, 34, 400, 44),
    ]
    base_text = to_text(extract_page(fixture, page_width=500))

    shuffled = list(fixture)
    rng = random.Random(7)  # noqa: S311
    rng.shuffle(shuffled)
    shuffled_text = to_text(extract_page(shuffled, page_width=500))
    assert shuffled_text == base_text


def test_acceptance_8_cli(tmp_path: Any, capsys: Any) -> None:
    """Acceptance item 8: main([path]) on a JSON file of two pages prints the pages joined
    by '\n\f\n' and returns 0; invalid JSON returns 2"""
    pages_data = [
        {
            "width": 500,
            "words": [{"text": "Page", "x0": 10, "x1": 40, "top": 10, "bottom": 20}],
        },
        {
            "width": 500,
            "words": [{"text": "Two", "x0": 10, "x1": 40, "top": 10, "bottom": 20}],
        },
    ]
    json_file = tmp_path / "pages.json"
    json_file.write_text(json.dumps(pages_data), encoding="utf-8")

    exit_code = main([str(json_file)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == "Page\n\x0c\nTwo"

    invalid_file = tmp_path / "bad.json"
    invalid_file.write_text("not valid json", encoding="utf-8")
    assert main([str(invalid_file)]) == 2


def test_edge_cases_empty_and_single_word() -> None:
    # Empty page
    empty_layout = extract_page([], page_width=500)
    assert to_text(empty_layout) == ""

    # Single word
    single_word = [Word("Lonely", 10, 10, 50, 20)]
    single_layout = extract_page(single_word, page_width=500)
    assert to_text(single_layout) == "Lonely"

    # Zero-height words (valid bottom >= top where bottom == top)
    zero_height = [Word("Zero", 10, 10, 50, 10)]
    zh_layout = extract_page(zero_height, page_width=500)
    assert to_text(zh_layout) == "Zero"

    # Overlapping words horizontally on the same line
    overlap = [
        Word("B", 15, 10, 30, 20),
        Word("A", 10, 10, 25, 20),
    ]
    assert to_text(extract_page(overlap, page_width=500)) == "A B"


def test_validation_errors() -> None:
    with pytest.raises(LayoutError) as exc:
        Word("", 0, 0, 10, 10)
    assert exc.value.code == "invalid_word"

    with pytest.raises(LayoutError) as exc:
        Word("Test", 0, 10, 10, 5)
    assert exc.value.code == "invalid_word"

    with pytest.raises(LayoutError) as exc:
        extract_page([], page_width=-10)
    assert exc.value.code == "invalid_input"

    with pytest.raises(LayoutError) as exc:
        extract_page([], page_width=500, column_gap=-1)
    assert exc.value.code == "invalid_input"

    with pytest.raises(LayoutError) as exc:
        extract_page([], page_width=500, row_gap=-1)
    assert exc.value.code == "invalid_input"

    with pytest.raises(LayoutError) as exc:
        words_from_dicts(["not-a-dict"])  # type: ignore[list-item]
    assert exc.value.code == "invalid_input"

    with pytest.raises(LayoutError) as exc:
        words_from_dicts([{"text": "missing_coords"}])
    assert exc.value.code == "invalid_word"


def test_cli_additional_paths(tmp_path: Any, capsys: Any) -> None:
    assert main([]) == 2
    assert main(["--help"]) == 2

    non_existent = tmp_path / "missing.json"
    assert main([str(non_existent)]) == 2

    root_not_list = tmp_path / "dict.json"
    root_not_list.write_text('{"key": 1}', encoding="utf-8")
    assert main([str(root_not_list)]) == 2

    page_not_dict = tmp_path / "page_not_dict.json"
    page_not_dict.write_text("[123]", encoding="utf-8")
    assert main([str(page_not_dict)]) == 2

    missing_keys = tmp_path / "missing_keys.json"
    missing_keys.write_text('[{"width": 100}]', encoding="utf-8")
    assert main([str(missing_keys)]) == 2

    words_not_list = tmp_path / "words_not_list.json"
    words_not_list.write_text('[{"width": 100, "words": 123}]', encoding="utf-8")
    assert main([str(words_not_list)]) == 2

    bad_page_width = tmp_path / "bad_width.json"
    bad_page_width.write_text('[{"width": "not_a_num", "words": []}]', encoding="utf-8")
    assert main([str(bad_page_width)]) == 2

    invalid_words_domain = tmp_path / "domain_fail.json"
    bad_payload = [{"width": 100, "words": [{"text": "", "x0": 0, "x1": 1, "top": 0, "bottom": 1}]}]
    invalid_words_domain.write_text(json.dumps(bad_payload), encoding="utf-8")
    assert main([str(invalid_words_domain)]) == 1
