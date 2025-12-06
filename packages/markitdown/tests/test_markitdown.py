import io
import os
import sys
import pytest
import tempfile
import codecs
import magika
from unittest.mock import Mock, MagicMock, patch, call, mock_open
from pathlib import Path

from markitdown import MarkItDown, DocumentConverterResult, StreamInfo
from markitdown._base_converter import DocumentConverter
from markitdown._exceptions import (
    FileConversionException,
    UnsupportedFormatException,
    FailedConversionAttempt,
)
from markitdown._markitdown import PRIORITY_SPECIFIC_FILE_FORMAT


class MockConverter(DocumentConverter):
    """A simple mock converter for testing"""

    def __init__(self, accept_value=True, convert_result="# Test"):
        self.accept_value = accept_value
        self.convert_result = convert_result
        self.accepts_calls = []
        self.convert_calls = []

    def accepts(self, file_stream, stream_info, **kwargs):
        self.accepts_calls.append((file_stream, stream_info, kwargs))
        return self.accept_value

    def convert(self, file_stream, stream_info, **kwargs):
        self.convert_calls.append((file_stream, stream_info, kwargs))
        return DocumentConverterResult(markdown=self.convert_result)


class TestPluginLoading:
    @patch('markitdown._markitdown.entry_points')
    def test_load_plugins_success(self, mock_entry_points):
        # Reset global state
        import markitdown._markitdown
        markitdown._markitdown._plugins = None

        # Setup mock plugin
        mock_plugin = Mock()
        mock_ep = Mock()
        mock_ep.name = "test_plugin"
        mock_ep.load.return_value = mock_plugin
        mock_entry_points.return_value = [mock_ep]

        from markitdown._markitdown import _load_plugins
        plugins = _load_plugins()

        assert plugins == [mock_plugin]
        mock_ep.load.assert_called_once()

    @patch('markitdown._markitdown.entry_points')
    @patch('markitdown._markitdown.warn')
    def test_load_plugins_failure(self, mock_warn, mock_entry_points):
        # Reset global state
        import markitdown._markitdown
        markitdown._markitdown._plugins = None

        # Setup failing plugin
        mock_ep = Mock()
        mock_ep.name = "bad_plugin"
        mock_ep.load.side_effect = Exception("Failed to load")
        mock_entry_points.return_value = [mock_ep]

        from markitdown._markitdown import _load_plugins
        plugins = _load_plugins()

        assert plugins == []
        mock_warn.assert_called_once()
        assert "bad_plugin" in str(mock_warn.call_args)

    @patch('markitdown._markitdown.entry_points')
    def test_load_plugins_already_loaded(self, mock_entry_points):
        # Set plugins as already loaded
        import markitdown._markitdown
        markitdown._markitdown._plugins = ["existing_plugin"]

        from markitdown._markitdown import _load_plugins
        plugins = _load_plugins()

        assert plugins == ["existing_plugin"]
        # Should not call entry_points again
        mock_entry_points.assert_not_called()


class TestMarkItDownInit:
    def test_init_default(self):
        md = MarkItDown()
        assert md._builtins_enabled is True
        assert md._plugins_enabled is False
        assert md._requests_session is not None
        assert md._magika is not None
        assert len(md._converters) > 0

    def test_init_disable_builtins(self):
        md = MarkItDown(enable_builtins=False)
        assert md._builtins_enabled is False
        assert len(md._converters) == 0

    @patch('markitdown._markitdown._load_plugins')
    def test_init_enable_plugins(self, mock_load_plugins):
        mock_load_plugins.return_value = []
        md = MarkItDown(enable_plugins=True)
        assert md._plugins_enabled is True

    def test_init_custom_requests_session(self):
        custom_session = Mock()
        md = MarkItDown(requests_session=custom_session)
        assert md._requests_session is custom_session


class TestEnableBuiltins:
    def test_enable_builtins_basic(self):
        md = MarkItDown(enable_builtins=False)
        assert md._builtins_enabled is False

        md.enable_builtins()
        assert md._builtins_enabled is True
        assert len(md._converters) > 0

    def test_enable_builtins_with_llm_kwargs(self):
        md = MarkItDown(enable_builtins=False)
        mock_client = Mock()

        md.enable_builtins(
            llm_client=mock_client,
            llm_model="gpt-4",
            llm_prompt="Test prompt"
        )

        assert md._llm_client is mock_client
        assert md._llm_model == "gpt-4"
        assert md._llm_prompt == "Test prompt"

    @patch.dict(os.environ, {"EXIFTOOL_PATH": "/custom/path/exiftool"})
    def test_enable_builtins_exiftool_from_env(self):
        md = MarkItDown(enable_builtins=False)
        md.enable_builtins()
        assert md._exiftool_path == "/custom/path/exiftool"

    @patch('shutil.which')
    def test_enable_builtins_exiftool_from_which(self, mock_which):
        mock_which.return_value = "/usr/bin/exiftool"

        md = MarkItDown(enable_builtins=False)
        md.enable_builtins()

        assert md._exiftool_path == "/usr/bin/exiftool"

    @patch('shutil.which')
    def test_enable_builtins_exiftool_not_in_known_paths(self, mock_which):
        mock_which.return_value = "/unknown/path/exiftool"

        md = MarkItDown(enable_builtins=False)
        md.enable_builtins()

        # Should not use the path from unknown location
        assert md._exiftool_path is None

    @patch('markitdown._markitdown.DocumentIntelligenceConverter')
    def test_enable_builtins_with_docintel(self, mock_docintel):
        md = MarkItDown(enable_builtins=False)
        md.enable_builtins(
            docintel_endpoint="https://example.com",
            docintel_credential="key123",
            docintel_file_types=["pdf"],
            docintel_api_version="2023-01-01"
        )

        assert md._builtins_enabled is True
        # Document Intelligence converter should be instantiated with the right args
        mock_docintel.assert_called_once_with(
            endpoint="https://example.com",
            credential="key123",
            file_types=["pdf"],
            api_version="2023-01-01"
        )

    @patch('markitdown._markitdown.DocumentIntelligenceConverter')
    def test_enable_builtins_with_docintel_minimal(self, mock_docintel):
        # Test with only endpoint (no optional params) - covers branches 206->209, 210->213, 214->217
        md = MarkItDown(enable_builtins=False)
        md.enable_builtins(
            docintel_endpoint="https://example.com"
        )

        assert md._builtins_enabled is True
        # Should be called with only endpoint
        mock_docintel.assert_called_once_with(
            endpoint="https://example.com"
        )

    def test_enable_builtins_with_exiftool_kwarg(self):
        # Test when exiftool_path is provided via kwarg - covers branch 147->151
        md = MarkItDown(enable_builtins=False)
        md.enable_builtins(exiftool_path="/custom/exiftool")

        assert md._exiftool_path == "/custom/exiftool"

    @patch('markitdown._markitdown.warn')
    def test_enable_builtins_already_enabled_warning(self, mock_warn):
        md = MarkItDown()  # Builtins enabled by default
        md.enable_builtins()

        mock_warn.assert_called_once()
        assert "already enabled" in str(mock_warn.call_args)


class TestEnablePlugins:
    @patch('markitdown._markitdown._load_plugins')
    def test_enable_plugins_success(self, mock_load_plugins):
        mock_plugin = Mock()
        mock_load_plugins.return_value = [mock_plugin]

        md = MarkItDown(enable_plugins=False)
        md.enable_plugins()

        assert md._plugins_enabled is True
        mock_plugin.register_converters.assert_called_once()

    @patch('markitdown._markitdown._load_plugins')
    @patch('markitdown._markitdown.warn')
    def test_enable_plugins_registration_failure(self, mock_warn, mock_load_plugins):
        mock_plugin = Mock()
        mock_plugin.register_converters.side_effect = Exception("Registration failed")
        mock_load_plugins.return_value = [mock_plugin]

        md = MarkItDown(enable_plugins=False)
        md.enable_plugins()

        assert md._plugins_enabled is True
        mock_warn.assert_called_once()

    @patch('markitdown._markitdown._load_plugins')
    @patch('markitdown._markitdown.warn')
    def test_enable_plugins_already_enabled_warning(self, mock_warn, mock_load_plugins):
        mock_load_plugins.return_value = []
        md = MarkItDown(enable_plugins=True)
        md.enable_plugins()

        # Should warn on second call
        assert any("already enabled" in str(call) for call in mock_warn.call_args_list)


class TestConvertEntryPoint:
    def test_convert_http_url(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            md.convert("https://example.com/test.html")
            mock_convert_uri.assert_called_once()

    def test_convert_https_url(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            md.convert("https://example.com/test.html")
            mock_convert_uri.assert_called_once()

    def test_convert_file_uri(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            md.convert("file:///path/to/file.txt")
            mock_convert_uri.assert_called_once()

    def test_convert_data_uri(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            md.convert("data:text/plain;base64,SGVsbG8=")
            mock_convert_uri.assert_called_once()

    def test_convert_local_path_string(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_local') as mock_convert_local:
            md.convert("/path/to/file.txt")
            mock_convert_local.assert_called_once()

    def test_convert_path_object(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_local') as mock_convert_local:
            md.convert(Path("/path/to/file.txt"))
            mock_convert_local.assert_called_once()

    def test_convert_requests_response(self):
        md = MarkItDown(enable_builtins=False)
        # Use requests.Response to get the proper spec
        import requests
        mock_response = Mock(spec=requests.Response)
        with patch.object(md, 'convert_response') as mock_convert_response:
            md.convert(mock_response)
            mock_convert_response.assert_called_once()

    def test_convert_binary_stream(self):
        md = MarkItDown(enable_builtins=False)
        stream = io.BytesIO(b"test")
        with patch.object(md, 'convert_stream') as mock_convert_stream:
            md.convert(stream)
            mock_convert_stream.assert_called_once()

    def test_convert_invalid_type(self):
        md = MarkItDown(enable_builtins=False)
        with pytest.raises(TypeError, match="Invalid source type"):
            md.convert(12345)

    def test_convert_text_io_rejected(self):
        md = MarkItDown(enable_builtins=False)
        text_stream = io.StringIO("test")
        with pytest.raises(TypeError):
            md.convert(text_stream)

    def test_convert_url_kwarg_rename(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            md.convert("https://example.com", url="https://mock.com")
            # url kwarg should be renamed to mock_url
            assert 'mock_url' in mock_convert_uri.call_args[1]
            assert 'url' not in mock_convert_uri.call_args[1]


class TestConvertLocal:
    def test_convert_local_with_path_object(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            md = MarkItDown(enable_builtins=False)
            converter = MockConverter()
            md.register_converter(converter)

            result = md.convert_local(Path(temp_path))
            assert result.markdown == "# Test"
        finally:
            os.unlink(temp_path)

    def test_convert_local_with_stream_info(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            md = MarkItDown(enable_builtins=False)
            converter = MockConverter()
            md.register_converter(converter)

            stream_info = StreamInfo(mimetype="text/plain")
            result = md.convert_local(temp_path, stream_info=stream_info)
            assert result.markdown == "# Test"
        finally:
            os.unlink(temp_path)

    def test_convert_local_with_deprecated_kwargs(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            md = MarkItDown(enable_builtins=False)
            converter = MockConverter()
            md.register_converter(converter)

            result = md.convert_local(
                temp_path,
                file_extension=".md",
                url="https://example.com"
            )
            assert result.markdown == "# Test"
        finally:
            os.unlink(temp_path)


class TestConvertStream:
    def test_convert_stream_seekable(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test content")
        result = md.convert_stream(stream)

        assert result.markdown == "# Test"

    def test_convert_stream_non_seekable(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        # Create a non-seekable stream
        class NonSeekableStream:
            def __init__(self, data):
                self.data = io.BytesIO(data)

            def read(self, size=-1):
                return self.data.read(size)

            def seekable(self):
                return False

        stream = NonSeekableStream(b"test content")
        result = md.convert_stream(stream)

        assert result.markdown == "# Test"

    def test_convert_stream_with_stream_info(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        stream_info = StreamInfo(extension=".txt")
        result = md.convert_stream(stream, stream_info=stream_info)

        assert result.markdown == "# Test"

    def test_convert_stream_with_deprecated_kwargs(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        result = md.convert_stream(
            stream,
            file_extension=".md",
            url="https://example.com"
        )

        assert result.markdown == "# Test"


class TestConvertUri:
    @patch('markitdown._markitdown.file_uri_to_path')
    def test_convert_file_uri_localhost(self, mock_file_uri):
        mock_file_uri.return_value = ("localhost", "/path/to/file.txt")

        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_local') as mock_convert_local:
            mock_convert_local.return_value = DocumentConverterResult(markdown="# Test")
            md.convert_uri("file://localhost/path/to/file.txt")
            mock_convert_local.assert_called_once()

    @patch('markitdown._markitdown.file_uri_to_path')
    def test_convert_file_uri_empty_netloc(self, mock_file_uri):
        mock_file_uri.return_value = ("", "/path/to/file.txt")

        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_local') as mock_convert_local:
            mock_convert_local.return_value = DocumentConverterResult(markdown="# Test")
            md.convert_uri("file:///path/to/file.txt")
            mock_convert_local.assert_called_once()

    @patch('markitdown._markitdown.file_uri_to_path')
    def test_convert_file_uri_invalid_netloc(self, mock_file_uri):
        mock_file_uri.return_value = ("remote-host", "/path/to/file.txt")

        md = MarkItDown(enable_builtins=False)
        with pytest.raises(ValueError, match="Unsupported file URI"):
            md.convert_uri("file://remote-host/path/to/file.txt")

    @patch('markitdown._markitdown.parse_data_uri')
    def test_convert_data_uri(self, mock_parse_data):
        mock_parse_data.return_value = ("text/plain", {"charset": "utf-8"}, b"Hello")

        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        result = md.convert_uri("data:text/plain;charset=utf-8;base64,SGVsbG8=")
        assert result.markdown == "# Test"

    @patch('markitdown._markitdown.parse_data_uri')
    def test_convert_data_uri_with_stream_info(self, mock_parse_data):
        mock_parse_data.return_value = ("text/plain", {"charset": "utf-8"}, b"Hello")

        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        # Test with additional stream_info parameter (line 434)
        stream_info = StreamInfo(filename="test.txt")
        result = md.convert_uri(
            "data:text/plain;charset=utf-8;base64,SGVsbG8=",
            stream_info=stream_info
        )
        assert result.markdown == "# Test"

    def test_convert_http_uri(self):
        md = MarkItDown(enable_builtins=False)
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        with patch.object(md._requests_session, 'get') as mock_get:
            mock_get.return_value = mock_response
            converter = MockConverter()
            md.register_converter(converter)

            result = md.convert_uri("http://example.com/test.txt")
            assert result.markdown == "# Test"

    def test_convert_https_uri(self):
        md = MarkItDown(enable_builtins=False)
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "https://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        with patch.object(md._requests_session, 'get') as mock_get:
            mock_get.return_value = mock_response
            converter = MockConverter()
            md.register_converter(converter)

            result = md.convert_uri("https://example.com/test.txt")
            assert result.markdown == "# Test"

    def test_convert_unsupported_uri_scheme(self):
        md = MarkItDown(enable_builtins=False)
        with pytest.raises(ValueError, match="Unsupported URI scheme"):
            md.convert_uri("ftp://example.com/file.txt")

    def test_convert_uri_whitespace_stripped(self):
        md = MarkItDown(enable_builtins=False)
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        with patch.object(md._requests_session, 'get') as mock_get:
            mock_get.return_value = mock_response
            converter = MockConverter()
            md.register_converter(converter)

            result = md.convert_uri("  https://example.com/test.txt  ")
            assert result.markdown == "# Test"


class TestConvertUrl:
    def test_convert_url_is_alias(self):
        md = MarkItDown(enable_builtins=False)
        with patch.object(md, 'convert_uri') as mock_convert_uri:
            mock_convert_uri.return_value = DocumentConverterResult(markdown="# Test")
            md.convert_url("https://example.com")
            mock_convert_uri.assert_called_once()


class TestConvertResponse:
    def test_convert_response_with_content_type(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain; charset=utf-8"}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_with_content_disposition(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {
            "content-disposition": 'attachment; filename="test.txt"'
        }
        mock_response.url = "http://example.com/"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_filename_from_url(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "http://example.com/path/file.txt"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_with_stream_info(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "http://example.com/test"
        mock_response.iter_content.return_value = [b"test"]

        stream_info = StreamInfo(extension=".md")
        result = md.convert_response(mock_response, stream_info=stream_info)
        assert result.markdown == "# Test"

    def test_convert_response_with_deprecated_kwargs(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {}
        mock_response.url = "http://example.com/test"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(
            mock_response,
            file_extension=".txt",
            url="https://mock.com"
        )
        assert result.markdown == "# Test"

    def test_convert_response_content_type_no_charset(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_content_disposition_single_quotes(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {
            "content-disposition": "attachment; filename='test.txt'"
        }
        mock_response.url = "http://example.com/"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_empty_charset(self):
        # Test line 478: when charset is extracted but is empty string
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain; charset="}
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_content_disposition_no_match(self):
        # Test line 486: when content-disposition has no filename
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {
            "content-disposition": "attachment"  # No filename
        }
        mock_response.url = "http://example.com/test.txt"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"

    def test_convert_response_filename_no_extension(self):
        # Test line 489: when filename has no extension
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        mock_response = Mock()
        mock_response.headers = {
            "content-disposition": 'attachment; filename="README"'  # No extension
        }
        mock_response.url = "http://example.com/"
        mock_response.iter_content.return_value = [b"test"]

        result = md.convert_response(mock_response)
        assert result.markdown == "# Test"


class Test_Convert:
    def test_convert_with_single_converter(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter(accept_value=True, convert_result="# Success")
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        assert result.markdown == "# Success"
        assert len(converter.accepts_calls) == 1
        assert len(converter.convert_calls) == 1

    def test_convert_with_multiple_converters(self):
        md = MarkItDown(enable_builtins=False)

        # Register converters - most recent registration is tried first
        # So we register the rejecting one second
        converter_accepts = MockConverter(accept_value=True, convert_result="# Accepts")
        md.register_converter(converter_accepts)

        converter_rejects = MockConverter(accept_value=False)
        md.register_converter(converter_rejects)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # The rejecting converter is tried first (registered last), then the accepting one
        assert result.markdown == "# Accepts"
        assert len(converter_rejects.accepts_calls) == 1
        assert len(converter_rejects.convert_calls) == 0
        assert len(converter_accepts.accepts_calls) == 1
        assert len(converter_accepts.convert_calls) == 1

    def test_convert_with_priority_ordering(self):
        md = MarkItDown(enable_builtins=False)

        # Register in reverse priority order
        converter_low = MockConverter(accept_value=True, convert_result="# Low")
        md.register_converter(converter_low, priority=10.0)

        converter_high = MockConverter(accept_value=True, convert_result="# High")
        md.register_converter(converter_high, priority=0.0)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # High priority (0.0) should be tried first
        assert result.markdown == "# High"

    def test_convert_normalizes_line_endings(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter(accept_value=True, convert_result="Line1\r\nLine2\nLine3\n")
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # \r\n and \n line endings should be normalized to \n
        assert result.markdown == "Line1\nLine2\nLine3\n"

    def test_convert_removes_excessive_newlines(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter(accept_value=True, convert_result="Line1\n\n\n\nLine2")
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # Excessive newlines should be reduced to double newlines
        assert result.markdown == "Line1\n\nLine2"

    def test_convert_strips_trailing_whitespace(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter(accept_value=True, convert_result="Line1   \nLine2\t\n")
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # Trailing whitespace on lines should be stripped
        assert result.markdown == "Line1\nLine2\n"

    def test_convert_raises_unsupported_format(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter(accept_value=False)
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        with pytest.raises(UnsupportedFormatException):
            md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

    def test_convert_raises_file_conversion_exception(self):
        md = MarkItDown(enable_builtins=False)

        # Converter that accepts but throws an exception
        class FailingConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                raise ValueError("Conversion failed")

        md.register_converter(FailingConverter())

        stream = io.BytesIO(b"test")
        with pytest.raises(FileConversionException) as exc_info:
            md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # Check that the exception contains failed attempts
        # It tries with the provided StreamInfo and then with the empty StreamInfo() fallback
        assert len(exc_info.value.attempts) >= 1

    def test_convert_tries_all_stream_info_guesses(self):
        md = MarkItDown(enable_builtins=False)

        # Converter that only accepts .txt files
        class TxtConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                return stream_info.extension == ".txt"

            def convert(self, file_stream, stream_info, **kwargs):
                return DocumentConverterResult(markdown="# TXT")

        md.register_converter(TxtConverter())

        stream = io.BytesIO(b"test")
        guesses = [
            StreamInfo(extension=".md"),
            StreamInfo(extension=".txt"),  # This one should match
        ]
        result = md._convert(file_stream=stream, stream_info_guesses=guesses)

        assert result.markdown == "# TXT"

    def test_convert_passes_global_llm_options(self):
        md = MarkItDown(enable_builtins=False)
        md._llm_client = "test_client"
        md._llm_model = "test_model"
        md._llm_prompt = "test_prompt"

        class CapturingConverter(DocumentConverter):
            captured_kwargs = {}

            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                self.captured_kwargs = kwargs
                return DocumentConverterResult(markdown="# Test")

        converter = CapturingConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        assert converter.captured_kwargs["llm_client"] == "test_client"
        assert converter.captured_kwargs["llm_model"] == "test_model"
        assert converter.captured_kwargs["llm_prompt"] == "test_prompt"

    def test_convert_passes_exiftool_path(self):
        md = MarkItDown(enable_builtins=False)
        md._exiftool_path = "/usr/bin/exiftool"

        class CapturingConverter(DocumentConverter):
            captured_kwargs = {}

            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                self.captured_kwargs = kwargs
                return DocumentConverterResult(markdown="# Test")

        converter = CapturingConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        assert converter.captured_kwargs["exiftool_path"] == "/usr/bin/exiftool"

    def test_convert_passes_style_map(self):
        md = MarkItDown(enable_builtins=False)
        md._style_map = "test_style_map"

        class CapturingConverter(DocumentConverter):
            captured_kwargs = {}

            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                self.captured_kwargs = kwargs
                return DocumentConverterResult(markdown="# Test")

        converter = CapturingConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        assert converter.captured_kwargs["style_map"] == "test_style_map"

    def test_convert_passes_parent_converters(self):
        md = MarkItDown(enable_builtins=False)

        class CapturingConverter(DocumentConverter):
            captured_kwargs = {}

            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                self.captured_kwargs = kwargs
                return DocumentConverterResult(markdown="# Test")

        converter = CapturingConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        assert "_parent_converters" in converter.captured_kwargs
        assert len(converter.captured_kwargs["_parent_converters"]) == 1

    def test_convert_passes_legacy_kwargs(self):
        md = MarkItDown(enable_builtins=False)

        class CapturingConverter(DocumentConverter):
            captured_kwargs = {}

            def accepts(self, file_stream, stream_info, **kwargs):
                return True

            def convert(self, file_stream, stream_info, **kwargs):
                self.captured_kwargs = kwargs
                return DocumentConverterResult(markdown="# Test")

        converter = CapturingConverter()
        md.register_converter(converter)

        stream = io.BytesIO(b"test")
        stream_info = StreamInfo(extension=".txt", url="https://example.com")
        md._convert(file_stream=stream, stream_info_guesses=[stream_info])

        assert converter.captured_kwargs["file_extension"] == ".txt"
        assert converter.captured_kwargs["url"] == "https://example.com"

    def test_convert_accepts_not_implemented_skipped(self):
        md = MarkItDown(enable_builtins=False)

        # Converter that raises NotImplementedError in accepts
        class NotImplementedConverter(DocumentConverter):
            def accepts(self, file_stream, stream_info, **kwargs):
                raise NotImplementedError()

            def convert(self, file_stream, stream_info, **kwargs):
                return DocumentConverterResult(markdown="# Should not reach")

        md.register_converter(NotImplementedConverter())

        # Add a working converter
        working_converter = MockConverter()
        md.register_converter(working_converter)

        stream = io.BytesIO(b"test")
        result = md._convert(file_stream=stream, stream_info_guesses=[StreamInfo()])

        # Should use the working converter
        assert result.markdown == "# Test"


class TestRegisterConverter:
    def test_register_converter_basic(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        assert len(md._converters) == 1
        assert md._converters[0].converter is converter

    def test_register_converter_with_priority(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter, priority=5.0)

        assert len(md._converters) == 1
        assert md._converters[0].priority == 5.0

    def test_register_converter_default_priority(self):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()
        md.register_converter(converter)

        assert md._converters[0].priority == PRIORITY_SPECIFIC_FILE_FORMAT

    def test_register_multiple_converters(self):
        md = MarkItDown(enable_builtins=False)
        converter1 = MockConverter()
        converter2 = MockConverter()

        md.register_converter(converter1)
        md.register_converter(converter2)

        assert len(md._converters) == 2
        # Most recent registration should be first (at index 0)
        assert md._converters[0].converter is converter2
        assert md._converters[1].converter is converter1


class TestRegisterPageConverter:
    @patch('markitdown._markitdown.warn')
    def test_register_page_converter_deprecated(self, mock_warn):
        md = MarkItDown(enable_builtins=False)
        converter = MockConverter()

        md.register_page_converter(converter)

        # Should warn about deprecation
        mock_warn.assert_called_once()
        assert "deprecated" in str(mock_warn.call_args).lower()

        # Should still register the converter
        assert len(md._converters) == 1
        assert md._converters[0].converter is converter


class TestGetStreamInfoGuesses:
    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_basic(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "txt"
        mock_result.prediction.output.mime_type = "text/plain"
        mock_result.prediction.output.extensions = ["txt"]
        mock_result.prediction.output.is_text = True
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo()

        guesses = md._get_stream_info_guesses(stream, base_guess)

        assert len(guesses) > 0
        assert guesses[0].mimetype == "text/plain"

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_compatible(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "txt"
        mock_result.prediction.output.mime_type = "text/plain"
        mock_result.prediction.output.extensions = ["txt"]
        mock_result.prediction.output.is_text = True
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(mimetype="text/plain", extension=".txt")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should have compatible guess
        assert len(guesses) == 1
        assert guesses[0].mimetype == "text/plain"
        assert guesses[0].extension == ".txt"

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_incompatible(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "pdf"
        mock_result.prediction.output.mime_type = "application/pdf"
        mock_result.prediction.output.extensions = ["pdf"]
        mock_result.prediction.output.is_text = False
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(mimetype="text/plain", extension=".txt")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should have both guesses (base and magika)
        assert len(guesses) == 2

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_unknown_label(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result with unknown label
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "unknown"
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(extension=".txt")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should return enhanced base guess
        assert len(guesses) > 0

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_failed_status(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result with failed status
        mock_result = Mock()
        mock_result.status = "error"
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(extension=".txt")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should return enhanced base guess
        assert len(guesses) > 0

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_extension_to_mimetype(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika to fail
        mock_result = Mock()
        mock_result.status = "error"
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(extension=".txt")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should have guessed mimetype from extension
        assert len(guesses) > 0
        assert guesses[0].mimetype is not None

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_mimetype_to_extension(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika to fail
        mock_result = Mock()
        mock_result.status = "error"
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(mimetype="text/plain")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should have guessed extension from mimetype
        assert len(guesses) > 0
        assert guesses[0].extension is not None

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_charset_detection(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result for text file
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "txt"
        mock_result.prediction.output.mime_type = "text/plain"
        mock_result.prediction.output.extensions = ["txt"]
        mock_result.prediction.output.is_text = True
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo()

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should have detected charset
        assert len(guesses) > 0
        # Charset may or may not be detected depending on content

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_incompatible_charset(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "txt"
        mock_result.prediction.output.mime_type = "text/plain"
        mock_result.prediction.output.extensions = ["txt"]
        mock_result.prediction.output.is_text = True
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(charset="ISO-8859-1")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # May have incompatible guesses if charset doesn't match
        assert len(guesses) > 0

    @patch.object(magika.Magika, 'identify_stream')
    def test_get_stream_info_guesses_preserves_filename(self, mock_identify):
        md = MarkItDown(enable_builtins=False)

        # Mock magika result
        mock_result = Mock()
        mock_result.status = "ok"
        mock_result.prediction.output.label = "txt"
        mock_result.prediction.output.mime_type = "text/plain"
        mock_result.prediction.output.extensions = ["txt"]
        mock_result.prediction.output.is_text = True
        mock_identify.return_value = mock_result

        stream = io.BytesIO(b"test content")
        base_guess = StreamInfo(filename="test.txt", url="https://example.com")

        guesses = md._get_stream_info_guesses(stream, base_guess)

        # Should preserve filename and url
        assert len(guesses) > 0
        assert guesses[0].filename == "test.txt"
        assert guesses[0].url == "https://example.com"


class TestNormalizeCharset:
    def test_normalize_charset_none(self):
        md = MarkItDown(enable_builtins=False)
        result = md._normalize_charset(None)
        assert result is None

    def test_normalize_charset_utf8(self):
        md = MarkItDown(enable_builtins=False)
        result = md._normalize_charset("utf-8")
        assert result == "utf-8"

    def test_normalize_charset_utf8_variations(self):
        md = MarkItDown(enable_builtins=False)

        # All of these should normalize to the same value
        result1 = md._normalize_charset("UTF-8")
        result2 = md._normalize_charset("utf8")
        result3 = md._normalize_charset("UTF8")

        # All should be the same canonical form
        assert result1 == result2 == result3

    def test_normalize_charset_iso_8859_1(self):
        md = MarkItDown(enable_builtins=False)
        result = md._normalize_charset("ISO-8859-1")
        assert result is not None

    def test_normalize_charset_unknown(self):
        md = MarkItDown(enable_builtins=False)
        result = md._normalize_charset("unknown-charset-xyz")
        # Should return the original if lookup fails
        assert result == "unknown-charset-xyz"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
