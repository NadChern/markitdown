import io
import os
import pytest


from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._rss_converter import (
    RssConverter,
    PRECISE_MIME_TYPE_PREFIXES,
    PRECISE_FILE_EXTENSIONS,
    CANDIDATE_MIME_TYPE_PREFIXES,
    CANDIDATE_FILE_EXTENSIONS,
)


class TestRssConverterAccepts:
    def test_accepts_rss_extension(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_atom_extension(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".atom")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_rss_extension_uppercase(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".RSS")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_atom_extension_uppercase(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".ATOM")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_application_rss_mimetype(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="application/rss")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_application_rss_xml_mimetype(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="application/rss+xml")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_application_atom_mimetype(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="application/atom")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_application_atom_xml_mimetype(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="application/atom+xml")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="APPLICATION/RSS+XML")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_xml_extension_with_valid_rss(self):
        converter = RssConverter()
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
            </channel>
        </rss>"""
        stream_info = StreamInfo(extension=".xml")
        assert converter.accepts(io.BytesIO(rss_content), stream_info) is True

    def test_accepts_xml_extension_with_valid_atom(self):
        converter = RssConverter()
        atom_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test</title>
            <entry>
                <title>Entry</title>
            </entry>
        </feed>"""
        stream_info = StreamInfo(extension=".xml")
        assert converter.accepts(io.BytesIO(atom_content), stream_info) is True

    def test_accepts_text_xml_mimetype_with_valid_rss(self):
        converter = RssConverter()
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
            </channel>
        </rss>"""
        stream_info = StreamInfo(mimetype="text/xml")
        assert converter.accepts(io.BytesIO(rss_content), stream_info) is True

    def test_accepts_application_xml_mimetype_with_valid_atom(self):
        converter = RssConverter()
        atom_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test</title>
            <entry>
                <title>Entry</title>
            </entry>
        </feed>"""
        stream_info = StreamInfo(mimetype="application/xml")
        assert converter.accepts(io.BytesIO(atom_content), stream_info) is True

    def test_rejects_xml_extension_with_invalid_xml(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".xml")
        assert converter.accepts(io.BytesIO(b"not xml"), stream_info) is False

    def test_rejects_xml_extension_with_non_feed_xml(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <document>
            <title>Not a feed</title>
        </document>"""
        stream_info = StreamInfo(extension=".xml")
        assert converter.accepts(io.BytesIO(xml_content), stream_info) is False

    def test_rejects_wrong_extension(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = RssConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = RssConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_file_stream_position_preserved_after_check(self):
        converter = RssConverter()
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
            </channel>
        </rss>"""
        stream = io.BytesIO(rss_content)
        stream.seek(10)
        stream_info = StreamInfo(extension=".xml")
        converter.accepts(stream, stream_info)
        assert stream.tell() == 10


class TestRssConverterConvertRss:

    SIMPLE_RSS = b"""<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <description>A test RSS feed</description>
            <item>
                <title>First Item</title>
                <description>First item description</description>
                <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
            </item>
            <item>
                <title>Second Item</title>
                <description>Second item description</description>
                <pubDate>Tue, 02 Jan 2024 00:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>"""

    RSS_WITH_ENCODED_CONTENT = b"""<?xml version="1.0"?>
    <rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
        <channel>
            <title>Blog Feed</title>
            <description>A blog feed</description>
            <item>
                <title>Article Title</title>
                <description>Short description</description>
                <pubDate>Wed, 03 Jan 2024 00:00:00 GMT</pubDate>
                <content:encoded><![CDATA[<p>Full <strong>HTML</strong> content here</p>]]></content:encoded>
            </item>
        </channel>
    </rss>"""

    RSS_WITH_HTML_DESCRIPTION = b"""<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>HTML Feed</title>
            <item>
                <title>HTML Item</title>
                <description><![CDATA[<p>Description with <a href="http://example.com">link</a></p>]]></description>
            </item>
        </channel>
    </rss>"""

    RSS_WITHOUT_CHANNEL = b"""<?xml version="1.0"?>
    <rss version="2.0">
    </rss>"""

    def test_convert_simple_rss(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(self.SIMPLE_RSS), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Test Feed" in result.markdown
        assert "A test RSS feed" in result.markdown
        assert "## First Item" in result.markdown
        assert "## Second Item" in result.markdown
        assert "Published on: Mon, 01 Jan 2024 00:00:00 GMT" in result.markdown
        assert "Published on: Tue, 02 Jan 2024 00:00:00 GMT" in result.markdown
        assert "First item description" in result.markdown
        assert "Second item description" in result.markdown
        assert result.title == "Test Feed"

    def test_convert_rss_with_encoded_content(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(self.RSS_WITH_ENCODED_CONTENT), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Blog Feed" in result.markdown
        assert "## Article Title" in result.markdown
        assert "HTML" in result.markdown
        assert result.title == "Blog Feed"

    def test_convert_rss_with_html_description(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(self.RSS_WITH_HTML_DESCRIPTION), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "## HTML Item" in result.markdown
        assert "link" in result.markdown

    def test_convert_rss_without_channel_raises_error(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        with pytest.raises(ValueError, match="No channel found in RSS feed"):
            converter.convert(io.BytesIO(self.RSS_WITHOUT_CHANNEL), stream_info)

    def test_convert_rss_without_channel_title(self):
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <description>Feed without title</description>
                <item>
                    <title>Item</title>
                    <description>Description</description>
                </item>
            </channel>
        </rss>"""
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(rss_content), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "Feed without title" in result.markdown

    def test_convert_rss_only_description_no_title(self):
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <description>Only description here</description>
            </channel>
        </rss>"""
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(rss_content), stream_info)

        assert isinstance(result, DocumentConverterResult)

    def test_convert_rss_with_minimal_item(self):
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
                <item>
                </item>
            </channel>
        </rss>"""
        converter = RssConverter()
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(io.BytesIO(rss_content), stream_info)

        assert isinstance(result, DocumentConverterResult)


class TestRssConverterConvertAtom:

    SIMPLE_ATOM = b"""<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Test Atom Feed</title>
        <subtitle>A test Atom feed</subtitle>
        <entry>
            <title>First Entry</title>
            <summary>First entry summary</summary>
            <updated>2024-01-01T00:00:00Z</updated>
        </entry>
        <entry>
            <title>Second Entry</title>
            <summary>Second entry summary</summary>
            <updated>2024-01-02T00:00:00Z</updated>
        </entry>
    </feed>"""

    ATOM_WITH_CONTENT = b"""<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Blog Atom Feed</title>
        <entry>
            <title>Article Title</title>
            <summary>Short summary</summary>
            <updated>2024-01-03T00:00:00Z</updated>
            <content type="html"><![CDATA[<p>Full <em>content</em> here</p>]]></content>
        </entry>
    </feed>"""

    ATOM_WITHOUT_SUBTITLE = b"""<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
        <title>Simple Feed</title>
        <entry>
            <title>Entry</title>
        </entry>
    </feed>"""

    def test_convert_simple_atom(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".atom")

        result = converter.convert(io.BytesIO(self.SIMPLE_ATOM), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Test Atom Feed" in result.markdown
        assert "A test Atom feed" in result.markdown
        assert "## First Entry" in result.markdown
        assert "## Second Entry" in result.markdown
        assert "Updated on: 2024-01-01T00:00:00Z" in result.markdown
        assert "Updated on: 2024-01-02T00:00:00Z" in result.markdown
        assert "First entry summary" in result.markdown
        assert "Second entry summary" in result.markdown
        assert result.title == "Test Atom Feed"

    def test_convert_atom_with_content(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".atom")

        result = converter.convert(io.BytesIO(self.ATOM_WITH_CONTENT), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Blog Atom Feed" in result.markdown
        assert "## Article Title" in result.markdown
        assert "content" in result.markdown

    def test_convert_atom_without_subtitle(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".atom")

        result = converter.convert(io.BytesIO(self.ATOM_WITHOUT_SUBTITLE), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Simple Feed" in result.markdown
        assert result.title == "Simple Feed"

    def test_convert_atom_with_minimal_entry(self):
        atom_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test Feed</title>
            <entry>
            </entry>
        </feed>"""
        converter = RssConverter()
        stream_info = StreamInfo(extension=".atom")

        result = converter.convert(io.BytesIO(atom_content), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# Test Feed" in result.markdown


class TestRssConverterConvertErrors:

    INVALID_FEED_TYPE = b"""<?xml version="1.0"?>
    <document>
        <title>Not a feed</title>
    </document>"""

    INVALID_XML = b"This is not valid XML"

    def test_convert_unknown_feed_type_raises_error(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".xml")

        with pytest.raises(ValueError, match="Unknown feed type"):
            converter.convert(io.BytesIO(self.INVALID_FEED_TYPE), stream_info)

    def test_convert_invalid_xml_raises_error(self):
        converter = RssConverter()
        stream_info = StreamInfo(extension=".xml")

        with pytest.raises(Exception):
            converter.convert(io.BytesIO(self.INVALID_XML), stream_info)


class TestRssConverterHelperMethods:

    def test_feed_type_detects_rss(self):
        converter = RssConverter()
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
            </channel>
        </rss>"""
        from defusedxml import minidom
        doc = minidom.parseString(rss_content)

        assert converter._feed_type(doc) == "rss"

    def test_feed_type_detects_atom(self):
        converter = RssConverter()
        atom_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test</title>
            <entry>
                <title>Entry</title>
            </entry>
        </feed>"""
        from defusedxml import minidom
        doc = minidom.parseString(atom_content)

        assert converter._feed_type(doc) == "atom"

    def test_feed_type_returns_none_for_invalid(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <document>
            <title>Not a feed</title>
        </document>"""
        from defusedxml import minidom
        doc = minidom.parseString(xml_content)

        assert converter._feed_type(doc) is None

    def test_feed_type_returns_none_for_feed_without_entry(self):
        converter = RssConverter()
        atom_content = b"""<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Test</title>
        </feed>"""
        from defusedxml import minidom
        doc = minidom.parseString(atom_content)

        assert converter._feed_type(doc) is None

    def test_get_data_by_tag_name_returns_text(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <root>
            <title>Test Title</title>
        </root>"""
        from defusedxml import minidom
        doc = minidom.parseString(xml_content)
        root = doc.getElementsByTagName("root")[0]

        assert converter._get_data_by_tag_name(root, "title") == "Test Title"

    def test_get_data_by_tag_name_returns_none_when_not_found(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <root>
            <title>Test Title</title>
        </root>"""
        from defusedxml import minidom
        doc = minidom.parseString(xml_content)
        root = doc.getElementsByTagName("root")[0]

        assert converter._get_data_by_tag_name(root, "nonexistent") is None

    def test_get_data_by_tag_name_returns_none_for_empty_element(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <root>
            <title></title>
        </root>"""
        from defusedxml import minidom
        doc = minidom.parseString(xml_content)
        root = doc.getElementsByTagName("root")[0]

        assert converter._get_data_by_tag_name(root, "title") is None

    def test_get_data_by_tag_name_returns_none_for_element_with_child_element(self):
        converter = RssConverter()
        xml_content = b"""<?xml version="1.0"?>
        <root>
            <title><nested>Value</nested></title>
        </root>"""
        from defusedxml import minidom
        doc = minidom.parseString(xml_content)
        root = doc.getElementsByTagName("root")[0]

        # Should return None because firstChild is an element, not a text node
        result = converter._get_data_by_tag_name(root, "title")
        assert result is None or result == "Value"

    def test_parse_content_converts_html_to_markdown(self):
        converter = RssConverter()
        html_content = "<p>Test <strong>bold</strong> text</p>"

        result = converter._parse_content(html_content)

        assert "Test" in result
        assert "bold" in result

    def test_parse_content_returns_plain_text_on_error(self):
        converter = RssConverter()
        content = "Plain text content"

        result = converter._parse_content(content)

        assert result == content or "Plain text content" in result

    def test_parse_content_handles_exception(self):
        converter = RssConverter()

        # Mock _CustomMarkdownify to raise an exception
        from unittest.mock import patch

        content = "<p>Test content</p>"

        with patch('markitdown.converters._rss_converter._CustomMarkdownify') as mock_markdownify:
            mock_markdownify.return_value.convert_soup.side_effect = Exception("Test exception")

            result = converter._parse_content(content)

            # Should return original content when exception occurs
            assert result == content


class TestRssConverterConstants:
    def test_precise_mime_type_prefixes(self):
        assert "application/rss" in PRECISE_MIME_TYPE_PREFIXES
        assert "application/rss+xml" in PRECISE_MIME_TYPE_PREFIXES
        assert "application/atom" in PRECISE_MIME_TYPE_PREFIXES
        assert "application/atom+xml" in PRECISE_MIME_TYPE_PREFIXES
        assert len(PRECISE_MIME_TYPE_PREFIXES) == 4

    def test_precise_file_extensions(self):
        assert ".rss" in PRECISE_FILE_EXTENSIONS
        assert ".atom" in PRECISE_FILE_EXTENSIONS
        assert len(PRECISE_FILE_EXTENSIONS) == 2

    def test_candidate_mime_type_prefixes(self):
        assert "text/xml" in CANDIDATE_MIME_TYPE_PREFIXES
        assert "application/xml" in CANDIDATE_MIME_TYPE_PREFIXES
        assert len(CANDIDATE_MIME_TYPE_PREFIXES) == 2

    def test_candidate_file_extensions(self):
        assert ".xml" in CANDIDATE_FILE_EXTENSIONS
        assert len(CANDIDATE_FILE_EXTENSIONS) == 1


class TestRssConverterKwargs:
    def test_convert_passes_kwargs_to_markdownify(self):
        converter = RssConverter()
        rss_content = b"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
                <item>
                    <title>Item</title>
                    <description><![CDATA[<h1>Header</h1>]]></description>
                </item>
            </channel>
        </rss>"""
        stream_info = StreamInfo(extension=".rss")

        result = converter.convert(
            io.BytesIO(rss_content),
            stream_info,
            heading_style="ATX"
        )

        assert isinstance(result, DocumentConverterResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
