import pytest

from app.exceptions import (InvalidUrlError, PageTooLargeError,
                            UnparseableContentError)
from app.pipeline.input_acquisition import (MAX_BYTES, acquire_raw_html,
                                            decode_raw_html, validate_url)


@pytest.mark.parametrize(
    "url",
    ["https://example.com", "http://example.com/path?x=1", "https://sub.example.com:8080/"],
)
def test_validate_url_accepts_http_https(url):
    validate_url(url)  # should not raise


@pytest.mark.parametrize(
    "url",
    ["", "   ", "ftp://example.com", "file:///etc/passwd", "javascript:alert(1)", "example.com"],
)
def test_validate_url_rejects_invalid_schemes_and_formats(url):
    with pytest.raises(InvalidUrlError):
        validate_url(url)


def test_validate_url_rejects_missing_host():
    with pytest.raises(InvalidUrlError):
        validate_url("https://")


def test_decode_raw_html_accepts_utf8():
    assert decode_raw_html("<h1>café</h1>".encode("utf-8")) == "<h1>café</h1>"


def test_decode_raw_html_rejects_binary_content():
    with pytest.raises(UnparseableContentError):
        decode_raw_html(b"\xff\xfe\x00\x01binarydata\x80\x81")


def test_acquire_raw_html_rejects_oversized_payload():
    oversized = b"a" * (MAX_BYTES + 1)
    with pytest.raises(PageTooLargeError):
        acquire_raw_html(oversized)


def test_acquire_raw_html_returns_page_source_for_valid_input():
    page_source = acquire_raw_html(b"<h1>Hi</h1>", source_label="upload.html")
    assert page_source.mode == "raw_html"
    assert page_source.rendered is False
    assert page_source.degraded is False
    assert page_source.source_label == "upload.html"
    assert "<h1>Hi</h1>" in page_source.html
