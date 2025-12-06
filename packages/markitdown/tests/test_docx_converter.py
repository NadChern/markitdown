import importlib
import io
from unittest.mock import patch, MagicMock

import pytest
import sys
import markitdown.converters._docx_converter as docx_converter
from markitdown import StreamInfo, MissingDependencyException


class TestDocxConverter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = docx_converter.DocxConverter()

    def test_mammoth_files_open(self=None):
        with pytest.warns(UserWarning, match="DOCX: processing of r:link resources"):
            result = docx_converter.mammoth_files_open(self, "dummy_uri")
        assert isinstance(result, io.BytesIO)
        assert result.getvalue() == b""

    @pytest.mark.parametrize("input_value, mime_type, expected_output", [
        pytest.param(".mp3", None, False, id=".mp3_extension_case"),
        pytest.param(".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", True, id=".docx_extension_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts_valid_extension(self, stream_info, input_value, mime_type, expected_output):
        stream_info.extension = input_value
        stream_info.mimetype = mime_type

        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    @pytest.mark.parametrize("input_value, expected_output", [
        pytest.param("application/vnd.openxmlformats-officedocument.wordprocessingml.document", True, id="accepted_mimetype_case"),
        pytest.param("video/mp4", False, id="invalid_mimetype_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts_valid_mimetype(self, stream_info, input_value, expected_output):
        stream_info.mimetype = input_value
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    def test_convert_raises_missing_dependency(self):
        # Patch the _dependency_exc_info to simulate missing dependency
        exc_info = (None, Exception("dep error"), None)
        with patch("markitdown.converters._docx_converter._dependency_exc_info", exc_info):
            with pytest.raises(MissingDependencyException) as exc:
                self.converter.convert(io.BytesIO(b"dummy"), None)
            assert ".docx" in str(exc.value)

    @patch("markitdown.converters._docx_converter.pre_process_docx")
    @patch("markitdown.converters._docx_converter.mammoth.convert_to_html")
    def test_convert_successful_with_style_map(self, mock_convert_to_html, mock_pre_process_docx):
        mock_pre_process_docx.return_value = io.BytesIO(b"processed")
        mock_convert_to_html.return_value = MagicMock(value="<html>converted</html>")
        self.converter._html_converter.convert_string = MagicMock(return_value="final_result")

        result = self.converter.convert(io.BytesIO(b"test content"), None, style_map="mystyle")

        mock_pre_process_docx.assert_called_once()
        mock_convert_to_html.assert_called_once()
        self.converter._html_converter.convert_string.assert_called_once_with(
            "<html>converted</html>", style_map="mystyle"
        )
        assert result == "final_result"

    @patch("markitdown.converters._docx_converter.pre_process_docx")
    @patch("markitdown.converters._docx_converter.mammoth.convert_to_html")
    def test_convert_successful_without_style_map(self, mock_convert_to_html, mock_pre_process_docx):
        mock_pre_process_docx.return_value = io.BytesIO(b"processed")
        mock_convert_to_html.return_value = MagicMock(value="<html>converted</html>")
        self.converter._html_converter.convert_string = MagicMock(return_value="final_result")

        result = self.converter.convert(io.BytesIO(b"test content"), None)

        mock_pre_process_docx.assert_called_once()
        mock_convert_to_html.assert_called_once()
        self.converter._html_converter.convert_string.assert_called_once_with(
            "<html>converted</html>"
        )
        assert result == "final_result"

    @patch("markitdown._stream_info.StreamInfo")
    def test_excepts_import_error(self, stream_info):
        sys.modules.pop("mammoth", None)

        # Patch mammoth to raise ImportError
        with patch.dict("sys.modules", {"mammoth": None}):
            # Reload the module to trigger the except ImportError block
            from markitdown.converters import _docx_converter
            importlib.reload(_docx_converter)

            stream_info.mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            stream_info.extension = ".docx"

            with pytest.raises(_docx_converter.MissingDependencyException) as exc:
                self.converter.convert(io.BytesIO(b"dummy"), stream_info)

        # Restore the module to its original state by reloading with mammoth available
        importlib.reload(_docx_converter)

