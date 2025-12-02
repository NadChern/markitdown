import io
import os
import pytest


from markitdown import StreamInfo
from markitdown.converters._csv_converter import (
    CsvConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
CSV_TEST_FILE = os.path.join(TEST_FILES_DIR, "test.csv")


class TestCsvConverterAccepts:
    def test_accepts_csv_extension(self):
        converter = CsvConverter()
        stream_info = StreamInfo(extension=".csv")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_csv_extension_uppercase(self):
        converter = CsvConverter()
        stream_info = StreamInfo(extension=".CSV")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_text_csv_mimetype(self):
        converter = CsvConverter()
        stream_info = StreamInfo(mimetype="text/csv")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = CsvConverter()
        stream_info = StreamInfo(mimetype="TEXT/CSV")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = CsvConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = CsvConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = CsvConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestCsvConverterConvert:
    def test_convert_empty_csv(self):
        converter = CsvConverter()
        data = b""
        stream_info = StreamInfo(
            filename="empty.csv",
            extension=".csv",
            mimetype="text/csv",
            charset="utf-8",
        )
        result = converter.convert(io.BytesIO(data), stream_info)
        assert result.markdown == ""

    def test_convert_to_padded_rows(self):
        converter = CsvConverter()
        csv_text = "a,b,c\nd,e\ng,h,i\n"
        data = csv_text.encode("utf-8")
        stream_info = StreamInfo(
            filename="padded.csv",
            extension=".csv",
            mimetype="text/csv",
            charset="utf-8",
        )

        result = converter.convert(io.BytesIO(data), stream_info)
        out = result.markdown.replace("\r\n", "\n")

        assert "| a | b | c |" in out
        assert "|---" in out or "| ---" in out
        assert "| d | e |  |" in out 
        assert "| g | h | i |" in out


class TestCsvConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert any(p.lower().startswith("text/") for p in ACCEPTED_MIME_TYPE_PREFIXES)
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".csv" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])