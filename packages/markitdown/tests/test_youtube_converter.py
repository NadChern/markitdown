import io
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, call

from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._youtube_converter import (
    YouTubeConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)


class TestYouTubeConverterAccepts:
    def test_accepts_youtube_url_with_html_extension(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_youtube_url_with_htm_extension(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            extension=".htm"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_youtube_url_with_html_mimetype(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            mimetype="text/html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_youtube_url_with_xhtml_mimetype(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            mimetype="application/xhtml+xml"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_case_insensitive_mimetype(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            mimetype="TEXT/HTML"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_case_insensitive_extension(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".HTML"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_url_with_encoded_characters(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch%3Fv%3Dtest",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_url_with_escaped_query_params(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url=r"https://www.youtube.com/watch\?v\=test123",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_non_youtube_url(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://example.com/video.html",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_youtube_url_without_watch(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/channel/test",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_youtube_url_without_html_content(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".mp4"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_url(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="",
            extension=".html"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_none_url(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(extension=".html")
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestYouTubeConverterConvert:
    SIMPLE_HTML = b"""
    <html>
        <head>
            <title>Test Video - YouTube</title>
            <meta property="og:title" content="Test Video">
            <meta property="og:description" content="This is a test video">
            <meta itemprop="interactionCount" content="1000000">
            <meta itemprop="duration" content="PT5M30S">
            <meta name="keywords" content="test,video,youtube">
        </head>
        <body></body>
    </html>
    """

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_basic_video_without_transcript(self, ):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(self.SIMPLE_HTML), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "# YouTube" in result.markdown
        assert "## Test Video" in result.markdown
        assert "### Video Metadata" in result.markdown
        assert "**Views:** 1000000" in result.markdown
        assert "**Keywords:** test,video,youtube" in result.markdown
        assert "**Runtime:** PT5M30S" in result.markdown
        assert "### Description" in result.markdown
        assert "This is a test video" in result.markdown
        assert result.title == "Test Video - YouTube"

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_video_with_custom_charset(self):
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html",
            charset="utf-16"
        )

        html = self.SIMPLE_HTML.decode('utf-8').encode('utf-16')
        result = converter.convert(io.BytesIO(html), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "Test Video" in result.markdown

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_video_without_metadata(self):
        html = b"""
        <html>
            <head><title>Simple Video</title></head>
            <body></body>
        </html>
        """
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)

        assert "# YouTube" in result.markdown
        assert "## Simple Video" in result.markdown
        # Should not have metadata section
        assert "### Video Metadata" not in result.markdown

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_extracts_description_from_ytInitialData(self):
        yt_data = {
            "contents": {
                "attributedDescriptionBodyText": {
                    "content": "Description from ytInitialData"
                }
            }
        }

        html = f"""
        <html>
            <head><title>Test</title></head>
            <body>
                <script>
                    var ytInitialData = {json.dumps(yt_data)};
                </script>
            </body>
        </html>
        """.encode('utf-8')

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)

        assert "Description from ytInitialData" in result.markdown

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_handles_invalid_ytInitialData_json(self):
        html = b"""
        <html>
            <head><title>Test</title></head>
            <body>
                <script>
                    var ytInitialData = {invalid json};
                </script>
            </body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        # Should not raise exception, just skip the description
        result = converter.convert(io.BytesIO(html), stream_info)
        assert isinstance(result, DocumentConverterResult)

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_handles_empty_meta_content(self):
        html = b"""
        <html>
            <head>
                <title>Test</title>
                <meta property="og:title" content="">
                <meta name="description" content="">
            </head>
            <body></body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        assert isinstance(result, DocumentConverterResult)

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_without_title_falls_back_to_soup_title(self):
        html = b"""
        <html>
            <head><title>Fallback Title</title></head>
            <body></body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        assert result.title == "Fallback Title"


class TestYouTubeConverterTranscript:
    SIMPLE_HTML = b"""
    <html>
        <head><title>Test Video</title></head>
        <body></body>
    </html>
    """

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_with_transcript(self, mock_yt_api_class):
        # Setup mocks
        mock_api = Mock()
        mock_yt_api_class.return_value = mock_api

        mock_transcript_obj = Mock()
        mock_transcript_obj.language_code = "en"

        mock_list = Mock()
        mock_list.__iter__ = Mock(return_value=iter([mock_transcript_obj]))
        mock_api.list.return_value = mock_list

        mock_transcript_part1 = Mock()
        mock_transcript_part1.text = "Hello"
        mock_transcript_part2 = Mock()
        mock_transcript_part2.text = "World"

        mock_api.fetch.return_value = [mock_transcript_part1, mock_transcript_part2]

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(self.SIMPLE_HTML), stream_info)

        assert "### Transcript" in result.markdown
        assert "Hello World" in result.markdown
        mock_api.list.assert_called_once_with("test123")
        mock_api.fetch.assert_called_once()

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_with_custom_transcript_languages(self, mock_yt_api_class):
        # Setup mocks
        mock_api = Mock()
        mock_yt_api_class.return_value = mock_api

        mock_transcript_obj = Mock()
        mock_transcript_obj.language_code = "fr"

        mock_list = Mock()
        mock_list.__iter__ = Mock(return_value=iter([mock_transcript_obj]))
        mock_api.list.return_value = mock_list

        mock_transcript_part = Mock()
        mock_transcript_part.text = "Bonjour"
        mock_api.fetch.return_value = [mock_transcript_part]

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        result = converter.convert(
            io.BytesIO(self.SIMPLE_HTML),
            stream_info,
            youtube_transcript_languages=["fr", "en"]
        )

        assert "Bonjour" in result.markdown
        # Should use custom languages
        call_args = mock_api.fetch.call_args
        assert call_args[1]['languages'] == ["fr", "en"]

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_transcript_fetch_fails_then_translates(self, mock_yt_api_class):
        # Setup mocks
        mock_api = Mock()
        mock_yt_api_class.return_value = mock_api

        mock_transcript_obj = Mock()
        mock_transcript_obj.language_code = "es"

        mock_list = Mock()
        mock_list.__iter__ = Mock(return_value=iter([mock_transcript_obj]))
        mock_api.list.return_value = mock_list

        # First fetch fails
        mock_api.fetch.side_effect = Exception("Transcript not available")

        # Translation succeeds
        mock_found_transcript = Mock()
        mock_translated = Mock()
        mock_part = Mock()
        mock_part.text = "Translated text"
        mock_translated.fetch.return_value = [mock_part]
        mock_found_transcript.translate.return_value = mock_translated
        mock_list.find_transcript.return_value = mock_found_transcript

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        result = converter.convert(
            io.BytesIO(self.SIMPLE_HTML),
            stream_info,
            youtube_transcript_languages=["en"]
        )

        assert "Translated text" in result.markdown

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_no_video_id_in_url(self, mock_yt_api_class):
        # URL without 'v' parameter
        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?other=param",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(self.SIMPLE_HTML), stream_info)

        # Should not try to fetch transcript
        mock_yt_api_class.return_value.list.assert_not_called()

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_transcript_with_retries(self, mock_yt_api_class):
        # Setup mocks
        mock_api = Mock()
        mock_yt_api_class.return_value = mock_api

        mock_transcript_obj = Mock()
        mock_transcript_obj.language_code = "en"

        mock_list = Mock()
        mock_list.__iter__ = Mock(return_value=iter([mock_transcript_obj]))
        mock_api.list.return_value = mock_list

        # Fail twice, then succeed
        mock_part = Mock()
        mock_part.text = "Success"
        mock_api.fetch.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            [mock_part]
        ]

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(self.SIMPLE_HTML), stream_info)

        assert "Success" in result.markdown
        assert mock_api.fetch.call_count == 3


class TestYouTubeConverterHelpers:
    def test_get_returns_first_matching_key(self):
        converter = YouTubeConverter()
        metadata = {
            "title": "First Title",
            "og:title": "Second Title",
            "name": "Third Title"
        }

        result = converter._get(metadata, ["missing", "og:title", "name"])
        assert result == "Second Title"

    def test_get_returns_default_when_no_match(self):
        converter = YouTubeConverter()
        metadata = {"other": "value"}

        result = converter._get(metadata, ["missing1", "missing2"], default="default")
        assert result == "default"

    def test_get_returns_none_when_no_match_and_no_default(self):
        converter = YouTubeConverter()
        metadata = {"other": "value"}

        result = converter._get(metadata, ["missing"])
        assert result is None

    def test_findKey_in_dict(self):
        converter = YouTubeConverter()
        data = {
            "level1": {
                "level2": {
                    "target": "found it"
                }
            }
        }

        result = converter._findKey(data, "target")
        assert result == "found it"

    def test_findKey_in_list(self):
        converter = YouTubeConverter()
        data = [
            {"not_here": "no"},
            {"target": "found it"},
            {"also_not": "no"}
        ]

        result = converter._findKey(data, "target")
        assert result == "found it"

    def test_findKey_in_nested_structure(self):
        converter = YouTubeConverter()
        data = {
            "items": [
                {
                    "nested": {
                        "target": "deep value"
                    }
                }
            ]
        }

        result = converter._findKey(data, "target")
        assert result == "deep value"

    def test_findKey_returns_none_when_not_found(self):
        converter = YouTubeConverter()
        data = {"other": "value"}

        result = converter._findKey(data, "missing")
        assert result is None

    def test_findKey_with_walrus_operator(self):
        converter = YouTubeConverter()
        data = {
            "a": {
                "b": {
                    "c": "value"
                }
            }
        }

        result = converter._findKey(data, "c")
        assert result == "value"

    @patch('markitdown.converters._youtube_converter.time.sleep')
    def test_retry_operation_succeeds_first_try(self, mock_sleep):
        converter = YouTubeConverter()
        operation = Mock(return_value="success")

        result = converter._retry_operation(operation, retries=3, delay=1)

        assert result == "success"
        operation.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('markitdown.converters._youtube_converter.time.sleep')
    def test_retry_operation_succeeds_after_retries(self, mock_sleep):
        converter = YouTubeConverter()
        operation = Mock(side_effect=[
            Exception("Fail 1"),
            Exception("Fail 2"),
            "success"
        ])

        result = converter._retry_operation(operation, retries=3, delay=1)

        assert result == "success"
        assert operation.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(1)

    @patch('markitdown.converters._youtube_converter.time.sleep')
    def test_retry_operation_fails_all_attempts(self, mock_sleep):
        converter = YouTubeConverter()
        operation = Mock(side_effect=Exception("Always fails"))

        with pytest.raises(Exception, match="Operation failed after 3 attempts"):
            converter._retry_operation(operation, retries=3, delay=1)

        assert operation.call_count == 3
        assert mock_sleep.call_count == 2


class TestYouTubeConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "text/html" in ACCEPTED_MIME_TYPE_PREFIXES
        assert "application/xhtml" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 2

    def test_accepted_file_extensions(self):
        assert ".html" in ACCEPTED_FILE_EXTENSIONS
        assert ".htm" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 2


class TestYouTubeConverterTranscriptEdgeCases:
    SIMPLE_HTML = b"""
    <html>
        <head><title>Test Video</title></head>
        <body></body>
    </html>
    """

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', True)
    @patch('markitdown.converters._youtube_converter.YouTubeTranscriptApi')
    def test_convert_transcript_fails_with_single_language(self, mock_yt_api_class):
        # Test when transcript fetch fails with only default language
        mock_api = Mock()
        mock_yt_api_class.return_value = mock_api

        # Empty language list from API (only default "en" will be used)
        mock_list = Mock()
        mock_list.__iter__ = Mock(return_value=iter([]))
        mock_api.list.return_value = mock_list

        # Fetch fails
        mock_api.fetch.side_effect = Exception("No transcript")

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test123",
            extension=".html"
        )

        # Should handle gracefully without crashing
        result = converter.convert(io.BytesIO(self.SIMPLE_HTML), stream_info)
        assert isinstance(result, DocumentConverterResult)
        # No transcript section should be added
        assert "### Transcript" not in result.markdown


class TestYouTubeConverterEdgeCases:
    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_with_no_title_tag(self):
        html = b"""
        <html>
            <head>
                <meta property="og:title" content="Meta Title Only">
            </head>
            <body></body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        # Should use og:title when no <title> tag exists
        assert "Meta Title Only" in result.markdown
        assert result.title == "Meta Title Only"

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_with_non_tag_meta_elements(self):
        # bs4 might return non-Tag elements in some cases
        html = b"""
        <html>
            <head>
                <title>Test</title>
                <!-- Comment that's not a Tag -->
                <meta property="og:description" content="Real Meta Description">
            </head>
            <body></body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        # Should handle non-Tag elements gracefully and still extract the meta description
        assert "Real Meta Description" in result.markdown

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_with_non_tag_script_elements(self):
        html = b"""
        <html>
            <head><title>Test</title></head>
            <body>
                <!-- Comment -->
                <script>var test = "value";</script>
            </body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        assert isinstance(result, DocumentConverterResult)

    @patch('markitdown.converters._youtube_converter.IS_YOUTUBE_TRANSCRIPT_CAPABLE', False)
    def test_convert_with_empty_script_tag(self):
        html = b"""
        <html>
            <head><title>Test</title></head>
            <body>
                <script></script>
                <script>var ytInitialData = {};</script>
            </body>
        </html>
        """

        converter = YouTubeConverter()
        stream_info = StreamInfo(
            url="https://www.youtube.com/watch?v=test",
            extension=".html"
        )

        result = converter.convert(io.BytesIO(html), stream_info)
        assert isinstance(result, DocumentConverterResult)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
