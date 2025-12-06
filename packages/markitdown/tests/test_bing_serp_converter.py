import io
import base64
import pytest
from markitdown.converters._bing_serp_converter import BingSerpConverter, DocumentConverterResult

class DummyStreamInfo:
    def __init__(self, extension, mimetype, url, charset=None):
        self.extension = extension
        self.mimetype = mimetype
        self.url = url
        self.charset = charset

class TestBingSerpConverter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = BingSerpConverter()

    @pytest.mark.parametrize(
        "extension, mimetype, url, expected_output",
        [
            (".html", "text/html", "https://www.bing.com/search?q=test", True),
            (".docx", "docx", "https://www.bing.com/search?q=test", False),
            (".docx", "docx", "https://example.com", False),
            (".docx", "application/xhtml", "https://www.bing.com/search?q=test", True),
        ]
    )
    def test_accepts(self, extension, mimetype, url, expected_output):
        stream_info = DummyStreamInfo(extension, mimetype, url)
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    def test_convert_full_coverage(self):
        # Create HTML covering all branches
        u_encoded = base64.b64encode(b"https://destination.com").decode("utf-8")
        fake_html = f"""
        <html>
            <head><title>Test Title</title></head>
            <body>
                <div class="tptt">Tip</div>
                <div class="algoSlug_icon">Slug</div>
                <div class="b_algo">
                    <a href="https://bing.com/?u={u_encoded}">Link</a>
                    <p>Result paragraph</p>
                </div>
                <div class="b_algo">
                    <p>Second result</p>
                </div>
            </body>
        </html>
        """.encode("utf-8")

        stream_info = DummyStreamInfo(
            extension=".html",
            mimetype="text/html",
            url="https://www.bing.com/search?q=unit+test",
            charset=None,  # Tests the default utf-8 path
        )

        result = self.converter.convert(io.BytesIO(fake_html), stream_info)

        # Check result is a DocumentConverterResult
        assert isinstance(result, DocumentConverterResult)
        # Check title is captured
        assert result.title == "Test Title"
        # Check markdown includes query and both results
        assert "unit+test" in result.markdown or "unit test" in result.markdown
        assert "Result paragraph" in result.markdown
        assert "Second result" in result.markdown
