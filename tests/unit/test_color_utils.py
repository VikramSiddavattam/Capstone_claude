import pytest

from app.color_utils import to_hex


@pytest.mark.parametrize(
    "value,expected",
    [
        ("#112233", "#112233"),
        ("#ABCDEF", "#abcdef"),
        ("#fff", "#ffffff"),
        ("#000", "#000000"),
        ("rgb(255, 0, 0)", "#ff0000"),
        ("rgba(0, 128, 0, 0.5)", "#008000"),
        ("black", "#000000"),
        ("white", "#ffffff"),
        ("  red  ", "#ff0000"),
    ],
)
def test_to_hex_resolves_known_formats(value, expected):
    assert to_hex(value) == expected


@pytest.mark.parametrize(
    "value",
    [None, "", "not-a-color", "var(--brand-color)", "transparent", "rgb(300, 0, 0)"],
)
def test_to_hex_returns_none_for_unresolvable_values(value):
    assert to_hex(value) is None
