import io
from unittest.mock import patch

import markitdown.converters._bing_serp_converter
import pytest

class TestBingSerpConverter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = markitdown.converters._bing_serp_converter.BingSerpConverter()

    @pytest.mark.parametrize("extension, mimetype, url, expected_output", [
        pytest.param(".html", "text/html", "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D", True, id=".html_extension_case"),
        pytest.param(".docx", "docx", "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D", False, id=".docx_extension_case"),
        pytest.param(".docx", "docx", "https://example.com", False, id="not_SERP_case"),
        pytest.param(".docx", "application/xhtml", "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D", True, id="true_mime_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts(self, stream_info, extension, mimetype, url, expected_output):
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        stream_info.url = url
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    @pytest.mark.parametrize("extension, mimetype, url, expected_output", [
        pytest.param(".html", "text/html",
                     "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D",
                     True, id=".html_extension_case"),
        pytest.param(".docx", "docx",
                     "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D",
                     False, id=".docx_extension_case"),
        pytest.param(".docx", "docx", "https://example.com", False, id="not_SERP_case"),
        pytest.param(".docx", "application/xhtml",
                     "https://www.bing.com/search?q=test&form=QBLH&sp=-1&ghc=1&lq=0&pq=test&sc=12-4&qs=n&sk=&cvid=954C3072AE4C491EB1598CCC8834CD7D",
                     True, id="true_mime_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert(self, stream_info, extension, mimetype, url, expected_output):
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        stream_info.url = url
        assert self.converter.convert(io.BytesIO(), stream_info) == expected_output
