import builtins
import importlib
import io
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from markitdown import DocumentConverter, DocumentConverterResult
from markitdown.converters import XlsxConverter, HtmlConverter, XlsConverter
from markitdown._exceptions import MissingDependencyException


class TestXLSXConverter:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        # Patch module-level _xlsx_dependency_exc_info to None before creating the converter
        import markitdown.converters._xlsx_converter as xlsx_module
        monkeypatch.setattr(xlsx_module, "_xlsx_dependency_exc_info", None)

        self.module = xlsx_module
        self.converter = xlsx_module.XlsxConverter()

    def test_xlsx_converter_constructor(self):
        assert hasattr(self.converter, "_html_converter")
        assert isinstance(self.converter._html_converter, HtmlConverter)
        assert isinstance(self.converter, DocumentConverter)

    @pytest.mark.parametrize(
        "extension, mimetype, expected_output",
        [
            (".jpg", "invalid", False),
            (".xlsx", "image/jpeg", True),
            (".docx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", True),
        ],
    )
    def test_accepts(self, extension, mimetype, expected_output):
        stream_info = MagicMock()
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    def test_convert_success(self):
        """Verify convert() builds proper markdown output."""

        with patch.object(self.module.pd, "read_excel") as mock_read_excel, \
             patch.object(HtmlConverter, "convert_string") as mock_convert_string:

            # Simulate pandas read_excel returning two sheets
            mock_read_excel.return_value = {
                "Sheet1": pd.DataFrame({"A": [1], "B": [2]}),
                "Sheet2": pd.DataFrame({"X": [9]}),
            }

            # Fake HTML conversion
            mock_convert_string.return_value = DocumentConverterResult(
                markdown="| A | B |\n|---|---|\n| 1 | 2 |"
            )

            stream_info = MagicMock()
            stream_info.extension = ".xlsx"
            stream_info.mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            result = self.converter.convert(io.BytesIO(), stream_info)

            assert isinstance(result, DocumentConverterResult)
            assert "## Sheet1" in result.markdown
            assert "| A | B |" in result.markdown
            assert "## Sheet2" in result.markdown

    def test_convert_missing_dependency(self, monkeypatch):
        """Verify MissingDependencyException raised if import failed earlier."""
        monkeypatch.setattr(self.module, "_xlsx_dependency_exc_info",
                            (ImportError, ImportError("fail"), None))

        converter = self.module.XlsxConverter()
        stream_info = MagicMock()
        stream_info.extension = ".xlsx"
        stream_info.mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        with pytest.raises(MissingDependencyException) as exc_info:
            converter.convert(io.BytesIO(), stream_info)

        assert "XlsxConverter" in str(exc_info.value)
        assert ".xlsx" in str(exc_info.value)


# ----------------------------
# Tests for XlsConverter
# ----------------------------
class TestXlsConverter:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        import markitdown.converters._xlsx_converter as xlsx_module
        # Patch _xls_dependency_exc_info to None to avoid missing dependency errors
        monkeypatch.setattr(xlsx_module, "_xls_dependency_exc_info", None)

        self.module = xlsx_module
        self.converter = xlsx_module.XlsConverter()

    @pytest.mark.parametrize(
        "extension, mimetype, expected",
        [
            (".xls", "application/excel", True),
            (".xls", "application/vnd.ms-excel", True),
            (".docx", "application/excel", True),
            (".xlsx", "application/excel", True),
            (".txt", "text/plain", False),
            (".docx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", False),
        ],
    )
    def test_accepts(self, extension, mimetype, expected):
        stream_info = MagicMock()
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        assert self.converter.accepts(io.BytesIO(), stream_info) is expected

    def test_convert_success(self):
        """Test convert() returns correct markdown for multiple sheets."""
        with patch.object(self.module.pd, "read_excel") as mock_read_excel, \
             patch.object(HtmlConverter, "convert_string") as mock_html_convert:

            mock_read_excel.return_value = {
                "Sheet1": pd.DataFrame({"A": [1], "B": [2]}),
                "Sheet2": pd.DataFrame({"X": [9]}),
            }

            mock_html_convert.return_value = DocumentConverterResult(
                markdown="| A | B |\n|---|---|\n| 1 | 2 |"
            )

            stream_info = MagicMock()
            stream_info.extension = ".xls"
            stream_info.mimetype = "application/vnd.ms-excel"

            result = self.converter.convert(io.BytesIO(), stream_info)

            assert isinstance(result, DocumentConverterResult)
            assert "## Sheet1" in result.markdown
            assert "| A | B |" in result.markdown
            assert "## Sheet2" in result.markdown

    def test_convert_missing_dependency(self, monkeypatch):
        """Test convert() raises MissingDependencyException if dependencies missing."""
        monkeypatch.setattr(self.module, "_xls_dependency_exc_info",
                            (ImportError, ImportError("missing"), None))

        stream_info = MagicMock()
        stream_info.extension = ".xls"
        stream_info.mimetype = "application/excel"

        with pytest.raises(MissingDependencyException) as exc_info:
            self.converter.convert(io.BytesIO(), stream_info)

        assert ".xls" in str(exc_info.value)
        assert "XlsConverter" in str(exc_info.value)