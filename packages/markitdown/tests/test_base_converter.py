import io
import pytest

from markitdown._base_converter import DocumentConverter, DocumentConverterResult
from markitdown._stream_info import StreamInfo


class TestDocumentConverterResult:
    """Test the DocumentConverterResult class."""

    def test_constructor_with_markdown_only(self):
        """Test creating DocumentConverterResult with only markdown parameter."""
        result = DocumentConverterResult("# Test Markdown")
        assert result.markdown == "# Test Markdown"
        assert result.title is None

    def test_constructor_with_markdown_and_title(self):
        """Test creating DocumentConverterResult with both markdown and title."""
        result = DocumentConverterResult("# Test Markdown", title="Test Title")
        assert result.markdown == "# Test Markdown"
        assert result.title == "Test Title"

    def test_constructor_markdown_is_required(self):
        """Test that markdown parameter is required."""
        with pytest.raises(TypeError):
            DocumentConverterResult()  # type: ignore

    def test_constructor_title_is_keyword_only(self):
        """Test that title must be passed as keyword argument."""
        with pytest.raises(TypeError):
            # Should fail because title is keyword-only
            DocumentConverterResult("# Markdown", "Title")  # type: ignore

    def test_markdown_attribute_access(self):
        """Test direct access to markdown attribute."""
        result = DocumentConverterResult("Original markdown")
        assert result.markdown == "Original markdown"

    def test_markdown_attribute_modification(self):
        """Test that markdown attribute can be modified."""
        result = DocumentConverterResult("Original markdown")
        result.markdown = "Modified markdown"
        assert result.markdown == "Modified markdown"

    def test_title_attribute_access(self):
        """Test direct access to title attribute."""
        result = DocumentConverterResult("# Markdown", title="My Title")
        assert result.title == "My Title"

    def test_title_attribute_modification(self):
        """Test that title attribute can be modified."""
        result = DocumentConverterResult("# Markdown", title="Original Title")
        result.title = "Modified Title"
        assert result.title == "Modified Title"

    def test_title_can_be_set_to_none(self):
        """Test that title can be set to None."""
        result = DocumentConverterResult("# Markdown", title="Some Title")
        result.title = None
        assert result.title is None

    def test_text_content_property_getter(self):
        """Test that text_content property returns markdown (soft-deprecated alias)."""
        result = DocumentConverterResult("# Test Content")
        assert result.text_content == "# Test Content"
        assert result.text_content == result.markdown

    def test_text_content_property_setter(self):
        """Test that text_content property setter updates markdown (soft-deprecated alias)."""
        result = DocumentConverterResult("Original content")
        result.text_content = "Updated content"
        assert result.text_content == "Updated content"
        assert result.markdown == "Updated content"

    def test_text_content_and_markdown_are_synchronized(self):
        """Test that text_content and markdown stay synchronized."""
        result = DocumentConverterResult("Initial content")

        # Set via markdown
        result.markdown = "Via markdown"
        assert result.text_content == "Via markdown"

        # Set via text_content
        result.text_content = "Via text_content"
        assert result.markdown == "Via text_content"

    def test_str_method_returns_markdown(self):
        """Test that __str__() returns the markdown content."""
        result = DocumentConverterResult("# Markdown Content")
        assert str(result) == "# Markdown Content"

    def test_str_method_reflects_changes(self):
        """Test that __str__() reflects changes to markdown."""
        result = DocumentConverterResult("Original")
        result.markdown = "Updated"
        assert str(result) == "Updated"

    def test_empty_markdown_is_allowed(self):
        """Test that empty string is a valid markdown value."""
        result = DocumentConverterResult("")
        assert result.markdown == ""
        assert str(result) == ""

    def test_multiline_markdown(self):
        """Test that multiline markdown is handled correctly."""
        markdown = "# Title\n\nParagraph 1\n\nParagraph 2"
        result = DocumentConverterResult(markdown)
        assert result.markdown == markdown
        assert str(result) == markdown

    def test_markdown_with_special_characters(self):
        """Test markdown with special characters."""
        markdown = "# Title with **bold** and *italic* and `code`"
        result = DocumentConverterResult(markdown, title="Special Chars")
        assert result.markdown == markdown
        assert result.title == "Special Chars"


class TestDocumentConverter:
    """Test the DocumentConverter abstract base class."""

    def test_accepts_raises_not_implemented_error(self):
        """Test that calling accepts() on base class raises NotImplementedError."""
        converter = DocumentConverter()
        stream = io.BytesIO(b"test content")
        stream_info = StreamInfo()

        with pytest.raises(NotImplementedError) as exc_info:
            converter.accepts(stream, stream_info)

        # Check the error message includes the class name
        assert "DocumentConverter" in str(exc_info.value)
        assert "accepts()" in str(exc_info.value)

    def test_convert_raises_not_implemented_error(self):
        """Test that calling convert() on base class raises NotImplementedError."""
        converter = DocumentConverter()
        stream = io.BytesIO(b"test content")
        stream_info = StreamInfo()

        with pytest.raises(NotImplementedError) as exc_info:
            converter.convert(stream, stream_info)

        assert "Subclasses must implement this method" in str(exc_info.value)

    def test_can_instantiate_base_class(self):
        """Test that DocumentConverter can be instantiated (not enforced as abstract)."""
        converter = DocumentConverter()
        assert isinstance(converter, DocumentConverter)

    def test_accepts_with_kwargs(self):
        """Test that accepts() signature supports **kwargs."""
        converter = DocumentConverter()
        stream = io.BytesIO(b"test content")
        stream_info = StreamInfo()

        with pytest.raises(NotImplementedError):
            converter.accepts(stream, stream_info, custom_option=True, another_option="value")

    def test_convert_with_kwargs(self):
        """Test that convert() signature supports **kwargs."""
        converter = DocumentConverter()
        stream = io.BytesIO(b"test content")
        stream_info = StreamInfo()

        with pytest.raises(NotImplementedError):
            converter.convert(stream, stream_info, custom_option=True, another_option="value")


class TestConcreteConverterImplementation:
    """Test concrete implementations of DocumentConverter."""

    def test_concrete_converter_can_override_accepts(self):
        """Test that a concrete converter can override accepts() method."""

        class TestConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return stream_info.extension == ".test"

            def convert(self, file_stream, stream_info, **kwargs):
                return DocumentConverterResult("Converted content")

        converter = TestConverter()
        stream = io.BytesIO(b"content")

        # Should accept .test extension
        assert converter.accepts(stream, StreamInfo(extension=".test")) is True

        # Should reject other extensions
        assert converter.accepts(stream, StreamInfo(extension=".txt")) is False

    def test_concrete_converter_can_override_convert(self):
        """Test that a concrete converter can override convert() method."""

        class TestConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                content = file_stream.read().decode("utf-8")
                return DocumentConverterResult(f"# {content}")

        converter = TestConverter()
        stream = io.BytesIO(b"Test Content")

        result = converter.convert(stream, StreamInfo())
        assert isinstance(result, DocumentConverterResult)
        assert result.markdown == "# Test Content"

    def test_concrete_converter_accepts_with_mimetype(self):
        """Test concrete converter that checks mimetype."""

        class PdfConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return stream_info.mimetype == "application/pdf"

            def convert(self, file_stream, stream_info, **kwargs):
                return DocumentConverterResult("PDF content")

        converter = PdfConverter()
        stream = io.BytesIO(b"pdf content")

        assert converter.accepts(stream, StreamInfo(mimetype="application/pdf")) is True
        assert converter.accepts(stream, StreamInfo(mimetype="text/plain")) is False

    def test_concrete_converter_convert_with_title(self):
        """Test concrete converter that sets a title in the result."""

        class TitleConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                return DocumentConverterResult(
                    "# Document\n\nContent here",
                    title="Document Title"
                )

        converter = TitleConverter()
        result = converter.convert(io.BytesIO(b"content"), StreamInfo())

        assert result.markdown == "# Document\n\nContent here"
        assert result.title == "Document Title"

    def test_concrete_converter_uses_kwargs(self):
        """Test concrete converter that uses kwargs."""

        class ConfigurableConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return kwargs.get("force_accept", False)

            def convert(self, file_stream, stream_info, **kwargs):
                prefix = kwargs.get("prefix", "")
                content = file_stream.read().decode("utf-8")
                return DocumentConverterResult(f"{prefix}{content}")

        converter = ConfigurableConverter()
        stream1 = io.BytesIO(b"content")
        stream2 = io.BytesIO(b"content")

        # Should reject without force_accept
        assert converter.accepts(stream1, StreamInfo()) is False

        # Should accept with force_accept
        assert converter.accepts(stream1, StreamInfo(), force_accept=True) is True

        # Should use prefix from kwargs
        result = converter.convert(stream2, StreamInfo(), prefix="PREFIX: ")
        assert result.markdown == "PREFIX: content"

    def test_concrete_converter_reads_stream(self):
        """Test that concrete converter can read from file stream."""

        class CountingConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                content = file_stream.read()
                return DocumentConverterResult(f"Length: {len(content)}")

        converter = CountingConverter()
        stream = io.BytesIO(b"12345678")
        result = converter.convert(stream, StreamInfo())

        assert result.markdown == "Length: 8"

    def test_concrete_converter_error_message_includes_subclass_name(self):
        """Test that NotImplementedError includes the subclass name, not base class."""

        class PartialConverter(DocumentConverter):
            # Only implements accepts, not convert
            def accepts(self, file_stream, stream_info, **kwargs):
                return True

        converter = PartialConverter()
        stream = io.BytesIO(b"content")

        with pytest.raises(NotImplementedError) as exc_info:
            converter.convert(stream, StreamInfo())

        # Should still show the generic message since convert wasn't overridden
        assert "Subclasses must implement this method" in str(exc_info.value)

    def test_concrete_converter_accepts_can_peek_stream(self):
        """Test that accepts() can peek at stream and reset position."""

        class PeekingConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                # Save position
                cur_pos = file_stream.tell()

                # Peek at first 4 bytes
                magic = file_stream.read(4)

                # Reset position
                file_stream.seek(cur_pos)

                return magic == b"PEEK"

            def convert(self, file_stream, stream_info, **kwargs):
                content = file_stream.read()
                return DocumentConverterResult(f"Converted: {content.decode()}")

        converter = PeekingConverter()
        stream = io.BytesIO(b"PEEK rest of content")

        # accepts() should return True and reset stream position
        assert converter.accepts(stream, StreamInfo()) is True

        # Stream position should be back at 0
        assert stream.tell() == 0

        # convert() should be able to read from the beginning
        result = converter.convert(stream, StreamInfo())
        assert result.markdown == "Converted: PEEK rest of content"


class TestDocumentConverterParametrized:
    """Parametrized tests for DocumentConverter and DocumentConverterResult."""

    @pytest.mark.parametrize("markdown,expected", [
        ("# Title", "# Title"),
        ("", ""),
        ("Line 1\nLine 2", "Line 1\nLine 2"),
        ("Special: <>[]()!@#$%", "Special: <>[]()!@#$%"),
    ])
    def test_result_str_returns_markdown(self, markdown, expected):
        """Test that __str__() returns the markdown content for various inputs."""
        result = DocumentConverterResult(markdown)
        assert str(result) == expected

    @pytest.mark.parametrize("title", [
        "Simple Title",
        "Title with Special Chars: !@#$%",
        "",
        None,
    ])
    def test_result_title_values(self, title):
        """Test DocumentConverterResult with various title values."""
        if title is None:
            result = DocumentConverterResult("# Markdown")
        else:
            result = DocumentConverterResult("# Markdown", title=title)
        assert result.title == title


if __name__ == "__main__":
    """Runs this file's tests from the command line."""
    pytest.main([__file__, "-v"])
