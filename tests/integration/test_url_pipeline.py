"""End-to-end URL-mode analysis against a local fixture HTTP server
(never a live public website), driving real Playwright/Chromium rendering."""

from app.pipeline.pipeline import analyze_url


def test_analyze_url_end_to_end_renders_report(fixture_server):
    report_html = analyze_url(f"{fixture_server}/basic_elements.html")

    assert "Analysis Report" in report_html
    assert "Welcome to the Fixture Page" in report_html
    assert "Fixture: Basic Elements" in report_html  # <title> -> app name
    # marker-injection attribute must never leak into the rendered report
    assert "data-ll-idx" not in report_html
    assert "Hidden Link" not in report_html
    assert "Should Never Appear" not in report_html


def test_analyze_url_reports_computed_style_from_rendered_page(fixture_server):
    report_html = analyze_url(f"{fixture_server}/basic_elements.html")
    # rendered mode resolves color via getComputedStyle, not stylesheet text;
    # the fixture sets #main-title { color: #112233 }.
    assert "#112233" in report_html.lower()


def test_analyze_url_no_elements_page_raises(fixture_server):
    import pytest

    from app.exceptions import NoElementsFoundError

    with pytest.raises(NoElementsFoundError):
        analyze_url(f"{fixture_server}/no_elements.html")
