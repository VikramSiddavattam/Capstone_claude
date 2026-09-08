from bs4 import BeautifulSoup

from app.models import NOT_AVAILABLE, DiscoveredElement, PageSource
from app.pipeline.style_extract import extract_style, parse_css_rules


def _raw_page(html: str) -> tuple:
    soup = BeautifulSoup(html, "lxml")
    page_source = PageSource(html=html, mode="raw_html", source_label="t", rendered=False)
    return soup, page_source


def _element(soup, css_selector) -> DiscoveredElement:
    tag = soup.select_one(css_selector)
    return DiscoveredElement(
        tag=tag.name,
        attrs=dict(tag.attrs),
        text=tag.get_text(strip=True),
        node_key="0",
        element_type="heading",
        soup_node=tag,
    )


def test_extract_style_resolves_id_selector_from_style_block():
    html = (
        "<html><head><style>#title{color:#ff0000;font-size:20px;"
        "font-family:Arial;}</style></head>"
        '<body><h1 id="title">Hello</h1></body></html>'
    )
    soup, page_source = _raw_page(html)
    rules = parse_css_rules(soup)
    result = extract_style(_element(soup, "h1"), page_source, rules)
    assert result.font_color == "#ff0000"
    assert result.font_size == "20px"
    assert result.font_family == "Arial"
    assert result.visible_text == "Hello"


def test_extract_style_inline_style_overrides_stylesheet():
    html = (
        "<html><head><style>#title{color:#ff0000;}</style></head>"
        '<body><h1 id="title" style="color:#00ff00">Hello</h1></body></html>'
    )
    soup, page_source = _raw_page(html)
    rules = parse_css_rules(soup)
    result = extract_style(_element(soup, "h1"), page_source, rules)
    assert result.font_color == "#00ff00"


def test_extract_style_returns_not_available_when_unresolvable():
    html = "<html><body><h1>Hello</h1></body></html>"
    soup, page_source = _raw_page(html)
    rules = parse_css_rules(soup)
    result = extract_style(_element(soup, "h1"), page_source, rules)
    assert result.font_color == NOT_AVAILABLE
    assert result.font_size == NOT_AVAILABLE
    assert result.font_family == NOT_AVAILABLE


def test_extract_style_skips_elements_without_visible_text():
    html = '<html><body><h1 id="title"></h1></body></html>'
    soup, page_source = _raw_page(html)
    result = extract_style(_element(soup, "h1"), page_source, [])
    assert result.visible_text == ""
    assert result.font_color == NOT_AVAILABLE


def test_extract_style_class_selector_and_compound_selectors_ignored():
    html = (
        "<html><head><style>.headline{color:#123456;} "
        "div > h1{color:#654321;}</style></head>"
        '<body><h1 class="headline">Hello</h1></body></html>'
    )
    soup, page_source = _raw_page(html)
    rules = parse_css_rules(soup)
    # combinator selector ("div > h1") must be skipped as unsupported;
    # only the simple class selector should apply.
    result = extract_style(_element(soup, "h1"), page_source, rules)
    assert result.font_color == "#123456"
