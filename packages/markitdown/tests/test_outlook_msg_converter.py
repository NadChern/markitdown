import io
import os
import pytest


from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._outlook_msg_converter import (
    OutlookMsgConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
CSV_TEST_FILE = os.path.join(TEST_FILES_DIR, "test.msg")


class TestOutlookMsgConverterAccepts:
    def test_accepts_msg_extension(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(extension=".msg")
        assert converter.accepts(io.BytesIO(), stream_info) is True


    def test_accepts_msg_extension_uppercase(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(extension=".MSG")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_text_outlook_mimetype(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(mimetype="application/vnd.ms-outlook")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(mimetype="APPLICATION/VND.MS-OUTLOOK")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = OutlookMsgConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False






class TestOutlookMsgConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "application/vnd.ms-outlook" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".msg" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])