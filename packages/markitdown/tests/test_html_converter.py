import io
import os
import pytest


from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._html_converter import (
    HtmlConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
HTML_TEST_FILE = os.path.join(TEST_FILES_DIR, "test.html")


class TestHtmlConverterAccepts:
    def test_accepts_html_extension(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(extension=".html")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_htm_extension(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(extension=".htm")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_html_extension_uppercase(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(extension=".HTML")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_text_html_mimetype(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(mimetype="text/html")
        assert converter.accepts(io.BytesIO(), stream_info) is True
    def test_accepts_text_xhtml_mimetype(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(mimetype="application/xhtml")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(mimetype="TEXT/HTML")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = HtmlConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestHtmlConverterConvert:

    TEST_HTML = b"""
    <html>
      <head><title>Test Page</title></head>
      <body>
        <h1>This is Lucian</h1>
      </body>
    </html>
    """

    def test_convert_html(self):
        converter = HtmlConverter()
        stream_info = StreamInfo(extension=".html")

        result = converter.convert(io.BytesIO(self.TEST_HTML), stream_info)
        
        assert isinstance(result, DocumentConverterResult)
        assert "This is Lucian" in result.markdown


class TestHtmlConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "text/html" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".html" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])