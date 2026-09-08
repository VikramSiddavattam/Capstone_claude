from bs4 import BeautifulSoup

from app.models import DiscoveredElement, PageSource
from app.pipeline.report import (build_element_report, build_metadata,
                                 render_error, render_form, render_report)


def _element(attrs=None, text="Click me") -> DiscoveredElement:
    attrs = attrs or {"id": "x", "data-ll-idx": "3", "data-testid": "y"}
    return DiscoveredElement(
        tag="a", attrs=attrs, text=text, node_key="3", element_type="link", soup_node=None
    )


def test_build_element_report_strips_synthetic_marker_attribute():
    row = build_element_report(
        _element(),
        xpath="//a",
        fragile=False,
        font_family="Arial",
        font_size="14px",
        font_color="#000000",
    )
    assert "data-ll-idx" not in row.attributes
    assert row.attributes["id"] == "x"
    assert row.attributes["data-testid"] == "y"


def test_build_element_report_uses_id_when_no_text():
    row = build_element_report(
        _element(text=""),
        xpath="//a",
        fragile=False,
        font_family="Not Available",
        font_size="Not Available",
        font_color="Not Available",
    )
    assert row.name == "x"


def test_build_metadata_counts_by_type():
    soup = BeautifulSoup("<html><head><title>Demo</title></head></html>", "lxml")
    page_source = PageSource(
        html="<html></html>", mode="raw_html", source_label="Raw HTML", rendered=False
    )
    elements = [_element(), _element()]
    metadata = build_metadata(soup, page_source, elements)
    assert metadata.total_elements == 2
    assert metadata.counts_by_type == {"link": 2}
    assert metadata.app_name == "Demo"
    assert metadata.page_source_label == "Raw HTML"


def test_render_report_produces_html_with_escaped_content():
    soup = BeautifulSoup("<html><head></head></html>", "lxml")
    page_source = PageSource(
        html="<html></html>", mode="raw_html", source_label="Raw HTML", rendered=False
    )
    metadata = build_metadata(soup, page_source, [])
    xss_element = _element(attrs={"id": "x"}, text="<script>alert(1)</script>")
    row = build_element_report(
        xss_element,
        xpath="//a",
        fragile=False,
        font_family="Not Available",
        font_size="Not Available",
        font_color="Not Available",
    )
    html = render_report(metadata, [row])
    assert "<script>alert(1)</script>" not in html  # must be escaped
    assert "&lt;script&gt;" in html


def test_render_error_and_render_form_produce_html():
    error_html = render_error("Something failed.", 400)
    assert "Something failed." in error_html
    form_html = render_form()
    assert "<form" in form_html
