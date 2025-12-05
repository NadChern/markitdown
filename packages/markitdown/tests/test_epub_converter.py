import io
import unittest
from unittest.mock import patch, MagicMock

import pytest
from xlsxwriter import url

from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters import EpubConverter, HtmlConverter


class TestEpubConverter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = EpubConverter()

    def test_EpubConverter_constructor(self):
        assert hasattr(self.converter, "_html_converter")
        assert isinstance(self.converter._html_converter, HtmlConverter)
        assert isinstance(self.converter, HtmlConverter)

    @pytest.mark.parametrize("extension, mimetype, expected_output", [
        pytest.param(".epub", "application/epub", True, id=".epub_extension_case"),
        pytest.param(".html", "application/epub+zip", True, id="epub_mimetype_case"),
        pytest.param(".html", "html", False, id="invalid_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts(self, stream_info, extension, mimetype, expected_output):
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    @patch("markitdown.converters._epub_converter.zipfile.ZipFile")
    @patch("markitdown.converters._epub_converter.minidom.parse")
    def test_convert(self, mock_parse, mock_zipfile):
        # --- Mock container.xml ---
        container_dom = MagicMock()
        container_dom.getElementsByTagName.return_value = [
            MagicMock(getAttribute=MagicMock(return_value="OEBPS/content.opf"))
        ]

        # --- Mock content.opf ---
        opf_dom = MagicMock()

        # Metadata nodes
        title_node = MagicMock(firstChild=MagicMock(nodeValue="Test Title"))
        author_node1 = MagicMock(firstChild=MagicMock(nodeValue="Author1"))
        author_node2 = MagicMock(firstChild=MagicMock(nodeValue="Author2"))
        language_node = MagicMock(firstChild=MagicMock(nodeValue="en"))

        # getElementsByTagName returns nodes for different tags
        def get_elements(tag):
            return {
                "dc:title": [title_node],
                "dc:creator": [author_node1, author_node2],
                "dc:language": [language_node],
                "dc:publisher": [],
                "dc:date": [],
                "dc:description": [],
                "dc:identifier": [],
                "item": [MagicMock(
                    getAttribute=MagicMock(side_effect=lambda k: {"id": "item1", "href": "chapter1.html"}[k]))],
                "itemref": [MagicMock(getAttribute=MagicMock(return_value="item1"))],
            }.get(tag, [])

        opf_dom.getElementsByTagName.side_effect = get_elements

        # Patch minidom.parse to return container_dom first, then opf_dom
        mock_parse.side_effect = [container_dom, opf_dom]

        # --- Mock ZipFile context ---
        mock_zip = MagicMock()
        mock_zip.namelist.return_value = ["OEBPS/chapter1.html"]
        mock_zip.open.return_value = io.BytesIO(b"<h1>Chapter 1</h1>")
        mock_zipfile.return_value.__enter__.return_value = mock_zip

        # --- Mock HTML conversion ---
        mock_html_converter = MagicMock()
        mock_html_converter.convert.return_value = DocumentConverterResult(
            markdown="Converted Chapter",
            title="Chapter 1"
        )
        self.converter._html_converter = mock_html_converter

        # --- Call convert ---
        stream_info = StreamInfo(
            url="dummy",
            extension=".epub",
            mimetype="application/epub+zip",
            filename="book.epub"
        )
        result = self.converter.convert(io.BytesIO(b"fake epub bytes"), stream_info)

        # --- Assertions ---
        assert isinstance(result, DocumentConverterResult)
        assert "Test Title" in result.markdown
        assert "Author1, Author2" in result.markdown
        assert "Converted Chapter" in result.markdown
        assert result.title == "Test Title"

        # HTML converter should be called once
        mock_html_converter.convert.assert_called_once()
