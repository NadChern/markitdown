import io
from unittest.mock import patch

import pytest

import markitdown.converters._audio_converter
from markitdown import StreamInfo, DocumentConverter, MissingDependencyException


class TestAudioConverter:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.converter = markitdown.converters._audio_converter.AudioConverter()


    @pytest.mark.parametrize("input_value, expected_output", [
        pytest.param(".mp3", True, id=".mp3_extension_case"),
        pytest.param(".docx", False, id=".docx_extension_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts_valid_extension(self, stream_info, input_value, expected_output):
        stream_info.extension = input_value
        stream_info.mimetype = "invalid"
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output

    @pytest.mark.parametrize("input_value, expected_output", [
        pytest.param("audio/mpeg", True, id="audio/mpeg_mimetype_case"),
        pytest.param("video/mp4", True, id="video/mp4_mimetype_case"),
        pytest.param("audio/x-wav", True, id="audio/x-wav_mimetype_case"),
        pytest.param("x-wav", False, id="x-wav_mimetype_case")
    ])
    @patch("markitdown._stream_info.StreamInfo")
    def test_accepts_valid_mimetype(self, stream_info, input_value, expected_output):
        stream_info.mimetype = input_value
        assert self.converter.accepts(io.BytesIO(), stream_info) == expected_output


    @pytest.mark.parametrize("mimetype, extension, expected_output", [
        pytest.param("audio/x-wav", ".wav", True, id=".wav_format_case"),
        pytest.param("audio/mpeg", ".mp3", True, id=".mp3_format_case"),
        pytest.param("video/mp4", ".mp4", True, id=".mp4_format_case"),
        pytest.param("test", ".test", True, id="no_format_case")
    ])
    @patch("markitdown.converters._audio_converter.exiftool_metadata")
    @patch("markitdown.converters._audio_converter.transcribe_audio")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert(self, stream_info, mock_transcribe, mock_exif, mimetype, extension, expected_output):
        mock_exif.return_value = {
            "Title": "Song",
            "Artist": "Alice",
            "SampleRate": 48000,
        }

        mock_transcribe.return_value = "hello world"

        stream_info.mimetype = mimetype
        stream_info.extension = extension
        result = self.converter.convert(io.BytesIO(), stream_info)

        assert "Title: Song" in result.markdown
        assert "Artist: Alice" in result.markdown
        assert "SampleRate: 48000" in result.markdown

    @patch("markitdown.converters._audio_converter.transcribe_audio")
    @patch("markitdown._stream_info.StreamInfo")
    def test_convert_raises_exception(self, stream_info, mock_transcribe):
        mock_transcribe.side_effect = MissingDependencyException("dependency not installed")
        stream_info.mimetype = "audio/mpeg"
        stream_info.extension =".mp3"
        file_stream = io.BytesIO(b"dummy audio data")


        mock_transcribe.side_effect = MissingDependencyException("missing dependency")

        # ACT
        result = self.converter.convert(file_stream, stream_info)

        # ASSERT
        assert "Audio Transcript" not in result.markdown
        assert result.markdown == ""  # no metadata, no transcript
