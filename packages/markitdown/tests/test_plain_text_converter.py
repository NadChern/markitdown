import io
import os
import pytest


from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._plain_text_converter import (
    PlainTextConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
TEXT_TEST_FILE = os.path.join(TEST_FILES_DIR, "test.txt")


class TestPlainTextConverterAccepts:
    def test_accepts_txt_extension(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(extension=".txt")
        assert converter.accepts(io.BytesIO(), stream_info) is True


    def test_accepts_txt_extension_uppercase(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(extension=".TXT")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_text_mimetype(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(mimetype="text/plain")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(mimetype="TEXT/PLAIN")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestPlainTextConverterConvert:
    def test_convert_from_bytes_stream(self):
        converter = PlainTextConverter()
        stream = io.BytesIO(b"Hello its Lucian\nStill Lucian")
        stream_info = StreamInfo(extension=".txt", filename="exampleTest.txt")
        result = converter.convert(stream, stream_info)
        assert isinstance(result, DocumentConverterResult)
        assert "Hello its Lucian" in result.text_content
        assert "Still Lucian" in result.text_content

    def test_convert_real_text_file(self):
        converter = PlainTextConverter()
        stream_info = StreamInfo(extension=".txt", filename="test.txt")

        with open(TEXT_TEST_FILE, "rb") as f:
            stream = io.BytesIO(f.read())

        result = converter.convert(stream, stream_info)
        assert isinstance(result, DocumentConverterResult)
        assert isinstance(result.text_content, str)



class TestPlainTextConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "application/json" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".txt" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])