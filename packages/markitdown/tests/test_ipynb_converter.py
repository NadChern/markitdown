import io
import os
import pytest
import json


from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._ipynb_converter import (
    IpynbConverter,
    CANDIDATE_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")
IPYNB_TEST_FILE = os.path.join(TEST_FILES_DIR, "test_notebook.ipynb")


class TestIpynbConverterAccepts:
    def test_accepts_ipynb_extension(self):
        converter = IpynbConverter()
        stream_info = StreamInfo(extension=".ipynb")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_csv_extension_uppercase(self):
        converter = IpynbConverter()
        stream_info = StreamInfo(extension=".IPYNB")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_text_json_mimetype(self):
        converter = IpynbConverter()
        notebook_bytes = b'{"nbformat": 4, "nbformat_minor": 5, "cells": []}'
        stream_info = StreamInfo(mimetype="application/json")
        assert converter.accepts(io.BytesIO(notebook_bytes), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = IpynbConverter()
        notebook_bytes = b'{"nbformat": 4, "nbformat_minor": 5, "cells": []}'
        stream_info = StreamInfo(mimetype="APPLICATION/JSON")
        assert converter.accepts(io.BytesIO(notebook_bytes), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = IpynbConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = IpynbConverter()
        stream_info = StreamInfo(mimetype="image/png")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = IpynbConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestIpynbConverterConvert:
        
    def test_convert_ipynb(self):
        notebook = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": ["# Hello Notebook\n"],
                    "metadata": {},
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        data = json.dumps(notebook).encode("utf-8")

        converter = IpynbConverter()
        stream_info = StreamInfo(extension=".ipynb")

        result = converter.convert(io.BytesIO(data), stream_info)

        text = getattr(result, "markdown", None) 
        assert "# Hello Notebook" in text

    def test_convert_real_notebook_file(self):
        converter = IpynbConverter()
        stream_info = StreamInfo(extension=".ipynb", filename="test_notebook.ipynb")

        with open(IPYNB_TEST_FILE, "rb") as f:
            notebook_bytes = f.read()

        result = converter.convert(io.BytesIO(notebook_bytes), stream_info)

        assert isinstance(result, DocumentConverterResult)
        text = result.text_content
        assert isinstance(text, str)
        assert text.strip() != ""


class TestIpynbConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "application/json" in CANDIDATE_MIME_TYPE_PREFIXES
        assert len(CANDIDATE_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".ipynb" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])