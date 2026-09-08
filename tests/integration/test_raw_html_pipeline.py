"""End-to-end raw-HTML analysis using fixture pages (no live network)."""

import pytest

from app.exceptions import (NoElementsFoundError, PageTooLargeError,
                            UnparseableContentError)
from app.pipeline.input_acquisition import MAX_BYTES
from app.pipeline.pipeline import analyze_raw_html
from tests.conftest import read_fixture


def test_analyze_raw_html_end_to_end_report_contains_all_columns():
    html = read_fixture("basic_elements.html").encode("utf-8")
    report_html = analyze_raw_html(html, "basic_elements.html")

    assert "Analysis Report" in report_html
    assert "Welcome to the Fixture Page" in report_html
    assert "XPath" in report_html
    assert "Font Family" in report_html
    assert "Font Color" in report_html
    # style resolved from the fixture's <style> block for #main-title
    assert "#112233" in report_html
    # hidden/iframe content must never reach the report
    assert "Hidden Link" not in report_html
    assert "Should Never Appear" not in report_html


def test_analyze_raw_html_raises_on_zero_elements():
    html = read_fixture("no_elements.html").encode("utf-8")
    with pytest.raises(NoElementsFoundError):
        analyze_raw_html(html)


def test_analyze_raw_html_tolerates_malformed_markup():
    html = read_fixture("malformed.html").encode("utf-8")
    report_html = analyze_raw_html(html)
    assert "Analysis Report" in report_html


def test_analyze_raw_html_rejects_oversized_input():
    with pytest.raises(PageTooLargeError):
        analyze_raw_html(b"a" * (MAX_BYTES + 1))


def test_analyze_raw_html_rejects_binary_content():
    with pytest.raises(UnparseableContentError):
        analyze_raw_html(b"\xff\xfe\x00\x01\x80\x81")


def test_analyze_raw_html_marks_duplicate_link_text_as_fragile():
    report_html = analyze_raw_html(read_fixture("basic_elements.html").encode("utf-8"))
    assert "** Fragile **" in report_html
