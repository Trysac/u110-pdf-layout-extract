"""Behavior tests for the public API of pdf_layout_extract."""

from __future__ import annotations

import pytest

import pdf_layout_extract


def test_normalize_trims_and_lowercases() -> None:
    assert pdf_layout_extract.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        pdf_layout_extract.normalize(value)


def test_version_is_semver() -> None:
    parts = pdf_layout_extract.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
