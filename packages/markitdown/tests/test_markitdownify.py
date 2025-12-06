from types import SimpleNamespace

from bs4 import BeautifulSoup
from markdownify import ATX

from markitdown.converters._markdownify import _CustomMarkdownify


def test_heading_style_atx():
    conv = _CustomMarkdownify()
    assert conv.options["heading_style"] is ATX


def test_block_heading_adds_single_leading_newline():
    conv = _CustomMarkdownify()
    text = conv.convert_hN(1, SimpleNamespace(), "Heading", parent_tags=[])
    assert text.startswith("\n")
    assert not text.startswith("\n\n")


def test_block_heading_does_not_double_preexisting_newline():
    conv = _CustomMarkdownify()
    text = conv.convert_hN(1, SimpleNamespace(), "\nHeading", parent_tags=[])
    assert not text.startswith("\n\n")


def test_inline_heading_has_no_leading_newline():
    conv = _CustomMarkdownify()
    text = conv.convert_hN(1, SimpleNamespace(), "Heading", parent_tags=['p'])
    assert not text.startswith("\n")


def test_empty_link_text_is_empty():
    soup = BeautifulSoup("<a href='https://example.com'></a>", "html.parser")
    a = soup.find("a")
    conv = _CustomMarkdownify()
    assert conv.convert_a(a, "") == ""


def test_link_inside_pre_is_left_as_plain_text():
    soup = BeautifulSoup(
        "<pre><a href='https://example.com'>code()</a></pre>",
        "html.parser",
    )
    a = soup.find("a")
    conv = _CustomMarkdownify()
    out = conv.convert_a(a, "code()")
    assert out == "code()"


def test_http_link_gets_percent_encoded_path():
    conv = _CustomMarkdownify()
    html = "<a href='https://example.com/a b'>Link</a>"
    md = conv.convert(html)
    assert md.strip() == "[Link](https://example.com/a%20b)"


def test_non_http_link_uses_text_only():
    conv = _CustomMarkdownify()
    html = "<a href='mailto:me@example.com'>Email me</a>"
    md = conv.convert(html)
    assert "mailto:" not in md
    assert md.strip() == "Email me"


def test_autolink_format_when_enabled():
    url = "https://example.com/path"
    conv = _CustomMarkdownify(autolinks=True, default_title=False)
    html = f"<a href='{url}'>{url}</a>"
    md = conv.convert(html)
    assert md.strip() == f"<{url}>"


def test_default_title_included_when_enabled():
    conv = _CustomMarkdownify(default_title=True)
    html = "<a href='https://example.com/path'>Link</a>"
    md = conv.convert(html)
    assert '[Link](https://example.com/path "https://example.com/path")' in md


def test_invalid_url_falls_back_to_plain_text(monkeypatch):
    soup = BeautifulSoup("<a href='bad://url'>Link</a>", "html.parser")
    a = soup.find("a")

    def bad_parse(url):
        raise ValueError("bad")

    monkeypatch.setattr(
        "markitdown.converters._markdownify.urlparse",
        bad_parse,
    )

    conv = _CustomMarkdownify()
    out = conv.convert_a(a, "Link")
    assert out == "Link"


def test_basic_image_markdown():
    conv = _CustomMarkdownify()
    html = "<img src='image.png' alt='alt text' title='Title'>"
    md = conv.convert(html)
    assert md.strip() == '![alt text](image.png "Title")'


def test_inline_image_returns_alt_if_not_allowed_parent():
    soup = BeautifulSoup(
        "<p><img src='image.png' alt='alt text'></p>",
        "html.parser",
    )
    img = soup.find("img")
    conv = _CustomMarkdownify(keep_inline_images_in=[])
    out = conv.convert_img(img, "", convert_as_inline=True)
    assert out == "alt text"


def test_data_uri_image_is_truncated():
    soup = BeautifulSoup(
        "<img src='data:image/png;base64,AAAAAA' alt='pic'>",
        "html.parser",
    )
    img = soup.find("img")
    conv = _CustomMarkdownify()
    out = conv.convert_img(img, "")
    assert out == "![pic](data:image/png;base64...)"


def test_convert_handles_simple_html_snippet():
    html = "<h1>Title</h1><p>body</p>"
    conv = _CustomMarkdownify()
    md = conv.convert(html)
    assert "# Title" in md
    assert "body" in md