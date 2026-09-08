from bs4 import BeautifulSoup

from app.models import NOT_AVAILABLE
from app.pipeline.tech_detect import (detect_app_name,
                                      detect_frontend_technology)


def test_detect_app_name_from_title():
    soup = BeautifulSoup("<html><head><title>My App</title></head></html>", "lxml")
    assert detect_app_name(soup, "https://example.com", "url") == "My App"


def test_detect_app_name_falls_back_to_url_host():
    soup = BeautifulSoup("<html><head></head></html>", "lxml")
    assert detect_app_name(soup, "https://example.com/page", "url") == "example.com"


def test_detect_app_name_not_available_for_raw_html_without_title():
    soup = BeautifulSoup("<html><head></head></html>", "lxml")
    assert detect_app_name(soup, "Raw HTML", "raw_html") == NOT_AVAILABLE


def test_detect_frontend_technology_from_meta_generator():
    html = '<html><head><meta name="generator" content="Hugo 0.1"></head></html>'
    soup = BeautifulSoup(html, "lxml")
    assert detect_frontend_technology(soup, html) == "Hugo 0.1"


def test_detect_frontend_technology_from_framework_signature():
    html = '<html><body><div id="app" ng-version="15.0"></div></body></html>'
    soup = BeautifulSoup(html, "lxml")
    assert detect_frontend_technology(soup, html) == "Angular"


def test_detect_frontend_technology_from_script_src():
    html = '<html><body><script src="/static/react.production.min.js"></script></body></html>'
    soup = BeautifulSoup(html, "lxml")
    assert detect_frontend_technology(soup, html) == "React"


def test_detect_frontend_technology_not_available_when_undetectable():
    html = "<html><body><p>Plain page</p></body></html>"
    soup = BeautifulSoup(html, "lxml")
    assert detect_frontend_technology(soup, html) == NOT_AVAILABLE
