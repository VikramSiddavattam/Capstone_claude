import pytest

from app.exceptions import NoElementsFoundError
from app.models import PageSource
from app.pipeline.discovery import classify_element, discover_elements
from tests.conftest import read_fixture


@pytest.mark.parametrize(
    "tag,attrs,expected",
    [
        ("h1", {}, "heading"),
        ("h2", {}, "subheading"),
        ("h6", {}, "subheading"),
        ("a", {"href": "/x"}, "link"),
        ("button", {}, "button"),
        ("input", {"type": "button"}, "button"),
        ("input", {"type": "text"}, "input"),
        ("input", {"type": "checkbox"}, "input"),
        ("select", {}, "dropdown"),
        ("textarea", {}, "textarea"),
        ("div", {"role": "button"}, "clickable_role"),
        ("span", {"role": "tab"}, "clickable_role"),
        ("div", {}, None),
        ("p", {"role": "presentation"}, None),
    ],
)
def test_classify_element(tag, attrs, expected):
    assert classify_element(tag, attrs) == expected


def _raw_source(html: str) -> PageSource:
    return PageSource(html=html, mode="raw_html", source_label="test", rendered=False)


def test_discover_elements_finds_all_visible_types():
    soup, elements = discover_elements(_raw_source(read_fixture("basic_elements.html")))
    types_found = {e.element_type for e in elements}
    assert types_found == {
        "heading",
        "subheading",
        "link",
        "button",
        "input",
        "dropdown",
        "textarea",
        "clickable_role",
    }


def test_discover_elements_excludes_hidden_and_iframe_content():
    _, elements = discover_elements(_raw_source(read_fixture("basic_elements.html")))
    texts = [e.text for e in elements]
    assert not any("Hidden Link" in t for t in texts)
    assert not any("Hidden Button" in t for t in texts)
    assert not any("Should Never Appear" in t for t in texts)


def test_discover_elements_node_key_is_positional_index_for_raw_html():
    _, elements = discover_elements(_raw_source(read_fixture("basic_elements.html")))
    # raw-HTML mode: node_key must be a plain, distinct pre-order index
    keys = [e.node_key for e in elements]
    assert len(keys) == len(set(keys))
    assert all(key.isdigit() for key in keys)


def test_discover_elements_raises_when_nothing_found():
    with pytest.raises(NoElementsFoundError):
        discover_elements(_raw_source(read_fixture("no_elements.html")))


def test_discover_elements_tolerates_malformed_html():
    # Should not raise UnparseableContentError; lxml recovers from malformed markup.
    soup, elements = discover_elements(_raw_source(read_fixture("malformed.html")))
    assert any(e.element_type == "heading" for e in elements)
    assert any(e.element_type == "link" for e in elements)
