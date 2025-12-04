import io
from unittest.mock import patch, MagicMock

import pytest

from markitdown import DocumentConverterResult
from markitdown.converters import ImageConverter


class TestImageConverter():
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = ImageConverter()

    @pytest.mark.parametrize("extension, mimetype, expected_output", [
        pytest.param(".jpg", "invalid", True, id=".jpg_extension_case"),
        pytest.param(".docx", "image/jpeg", True, id=".jpeg_extension_case"),
        pytest.param(".docx", "docx", False, id=".docx_extension_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts(self, stream_info, extension, mimetype, expected_output):
        stream_info.extension = extension
        stream_info.mimetype = mimetype
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    @pytest.mark.parametrize("extension, mimetype", [
        pytest.param(".jpg", "invalid", id=".jpg_extension_case"),
        pytest.param(".docx", "image/jpeg", id=".jpeg_extension_case"),
        pytest.param(".docx", "docx", id=".docx_extension_case")
    ])
    @patch("markitdown.converters._image_converter.exiftool_metadata")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert(self, stream_info, mock_exif, extension, mimetype):
        mock_exif.return_value = {
            "Title": "Test Image",
            "Artist": "John Doe",
            "DateTimeOriginal": "2025:12:03 12:00:00",
        }
        file_stream = io.BytesIO(b"fake image bytes")
        stream_info.mimetype = mimetype
        stream_info.extension = extension

        result = self.converter.convert(file_stream, stream_info)
        assert isinstance(result, DocumentConverterResult)
        assert "Title: Test Image" in result.markdown
        assert "Artist: John Doe" in result.markdown
        assert "DateTimeOriginal: 2025:12:03 12:00:00" in result.markdown


    @patch("markitdown.converters._image_converter.exiftool_metadata")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert_no_metadata(self, stream_info, mock_exif):
        """Test convert when no metadata is returned"""
        mock_exif.return_value = {}

        file_stream = io.BytesIO(b"fake image bytes")
        stream_info.mimetype = "image/jpeg"
        stream_info.extension = ".jpg"
        stream_info.filename = "test.jpg"

        result = self.converter.convert(file_stream, stream_info)
        assert isinstance(result, DocumentConverterResult)
        # Should be empty markdown
        assert result.markdown == ""

    @patch("markitdown.converters._image_converter.ImageConverter._get_llm_description")
    @patch("markitdown.converters._image_converter.exiftool_metadata")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert_with_llm_description(self, stream_info, mock_exif, mock_llm):
        """Test convert when LLM description is used"""
        mock_exif.return_value = {
            "Title": "Test Image",
        }
        mock_llm.return_value = "This is an AI description."

        file_stream = io.BytesIO(b"fake image bytes")

        stream_info.mimetype = "image/jpeg"
        stream_info.extension = ".jpg"
        stream_info.filename = "test.jpg"

        result = self.converter.convert(
            file_stream, stream_info, llm_client=MagicMock(), llm_model="gpt-4"
        )
        assert isinstance(result, DocumentConverterResult)
        assert "Title: Test Image" in result.markdown
        assert "This is an AI description." in result.markdown

    @patch("markitdown.converters._image_converter.ImageConverter._get_llm_description")
    @patch("markitdown.converters._image_converter.exiftool_metadata")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert_llm_returns_none(self, stream_info, mock_exif, mock_llm):
        """Test convert when LLM description returns None"""
        mock_exif.return_value = {
            "Title": "Test Image",
        }
        mock_llm.return_value = None
        file_stream = io.BytesIO(b"fake image bytes")
        stream_info.mimetype = "image/jpeg"
        stream_info.extension = ".jpg"
        stream_info.filename = "test.jpg"

        result = self.converter.convert(
            file_stream, stream_info, llm_client=MagicMock(), llm_model="gpt-4"
        )
        assert isinstance(result, DocumentConverterResult)
        # Only metadata should appear
        assert result.markdown.strip() == "Title: Test Image"