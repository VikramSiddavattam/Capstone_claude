from bs4 import BeautifulSoup

from app.models import DiscoveredElement
from app.pipeline.xpath_gen import generate_xpath


def _element(soup, css_selector, element_type="link") -> DiscoveredElement:
    tag = soup.select_one(css_selector)
    return DiscoveredElement(
        tag=tag.name,
        attrs=dict(tag.attrs),
        text=tag.get_text(strip=True),
        node_key="0",
        element_type=element_type,
        soup_node=tag,
    )


def test_priority1_unique_id_wins():
    soup = BeautifulSoup('<div><a id="submit" name="submit">Go</a></div>', "lxml")
    result = generate_xpath(_element(soup, "#submit"), soup)
    assert result.strategy == "id"
    assert result.xpath == "//*[@id='submit']"
    assert result.fragile is False


def test_priority1_skipped_when_id_not_unique():
    html = '<div><a id="dup" data-testid="t1">A</a><span id="dup">B</span></div>'
    soup = BeautifulSoup(html, "lxml")
    result = generate_xpath(_element(soup, "a#dup"), soup)
    assert result.strategy != "id"


def test_priority2_unique_data_testid():
    soup = BeautifulSoup('<button data-testid="submit-btn">Go</button>', "lxml")
    result = generate_xpath(_element(soup, "button"), soup)
    assert result.strategy == "unique-attribute"
    assert "data-testid" in result.xpath
    assert result.fragile is False


def test_priority3_text_based_when_unique_text():
    html = "<div><a>Click Here</a><a>Other Link</a></div>"
    soup = BeautifulSoup(html, "lxml")
    element = _element(soup, "a")
    result = generate_xpath(element, soup)
    assert result.strategy == "text-based"
    assert result.fragile is False
    assert "Click Here" in result.xpath


def test_priority3_fragile_position_fallback_when_no_identifiers():
    html = "<div><a>Same</a><a>Same</a></div>"
    soup = BeautifulSoup(html, "lxml")
    element = _element(soup, "a")
    result = generate_xpath(element, soup)
    assert result.strategy == "position-fallback"
    assert result.fragile is True


def test_generated_xpath_handles_single_quote_in_id():
    # only one quote style present -> wrapped in the other quote character
    soup = BeautifulSoup("""<a id="o'brien">Link</a>""", "lxml")
    result = generate_xpath(_element(soup, "a"), soup)
    assert result.strategy == "id"
    assert result.xpath == '//*[@id="o\'brien"]'


def test_generated_xpath_uses_concat_when_both_quote_styles_present():
    soup = BeautifulSoup("""<a id="o'brien&quot;s"></a>""", "lxml")
    result = generate_xpath(_element(soup, "a"), soup)
    assert result.strategy == "id"
    assert "concat(" in result.xpath
