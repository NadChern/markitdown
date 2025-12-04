import io
import os
from markitdown.converters._docx_converter import DocxConverter
from markitdown._stream_info import StreamInfo

TEST_DOCX_PATH = os.path.join(
    os.path.dirname(__file__),
    "test_files",
    "test.docx",
)

def test_docx_integration():
    converter = DocxConverter()

    with open(TEST_DOCX_PATH, "rb") as f:
        file_bytes = f.read()

    stream_info = StreamInfo(
        extension=".docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        url=None,
    )
    assert converter.accepts(io.BytesIO(file_bytes), stream_info)
    result = converter.convert(io.BytesIO(file_bytes), stream_info)
    # Verify integration properties
    assert result is not None
    assert hasattr(result, "markdown")
    assert isinstance(result.markdown, str)
    assert len(result.markdown) > 0
