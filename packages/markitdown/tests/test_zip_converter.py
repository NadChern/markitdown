import io
import os
import pytest

from markitdown import MarkItDown, StreamInfo
from markitdown.converters._zip_converter import (
    ZipConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
ZIP_TEST_FILE = os.path.join(TEST_FILES_DIR, "test_files.zip")



class TestZipConverterAccepts:
    def test_accepts_zip_extension(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(extension=".zip")
        assert converter.accepts(io.BytesIO(), stream_info) is True
    def test_accepts_zip_extension_uppercase(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(extension=".ZIP")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_application_zip_mimetype(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(mimetype="application/zip")
        assert converter.accepts(io.BytesIO(), stream_info) is True


    def test_accepts_mimetype_case_insensitive(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(mimetype="APPLICATION/ZIP")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo(mimetype="text/plain")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        self.md = MarkItDown()
        converter = ZipConverter(markitdown = self.md)
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False



class TestZipConverterConvert:
    def test_convert_zip_via_markitdown(self):
        assert os.path.exists(ZIP_TEST_FILE), f"Missing test file: {ZIP_TEST_FILE}"

        md = MarkItDown()
        result = md.convert(ZIP_TEST_FILE)

 
        assert hasattr(result, "markdown")
        assert isinstance(result.markdown, str)
        assert result.markdown.strip() != ""



class TestZipConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "application/zip" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".zip" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])