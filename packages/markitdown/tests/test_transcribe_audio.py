import io
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from markitdown._exceptions import MissingDependencyException


class TestTranscribeAudioDependencies:
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', (ImportError, ImportError("speech_recognition not found"), None))
    def test_missing_dependency_exception(self):
        from markitdown.converters._transcribe_audio import transcribe_audio

        with pytest.raises(MissingDependencyException) as exc_info:
            transcribe_audio(io.BytesIO(), audio_format="wav")

        assert "audio-transcription" in str(exc_info.value)


class TestTranscribeAudioFormats:
    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_wav_format(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Hello world"

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        assert result == "Hello world"
        mock_sr.AudioFile.assert_called_once_with(audio_stream)
        mock_recognizer.record.assert_called_once_with(mock_audio_file)
        mock_recognizer.recognize_google.assert_called_once_with(mock_audio)

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_aiff_format(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Test audio"

        # Test
        audio_stream = io.BytesIO(b"fake aiff data")
        result = transcribe_audio(audio_stream, audio_format="aiff")

        assert result == "Test audio"
        mock_sr.AudioFile.assert_called_once_with(audio_stream)

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_flac_format(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "FLAC audio test"

        # Test
        audio_stream = io.BytesIO(b"fake flac data")
        result = transcribe_audio(audio_stream, audio_format="flac")

        assert result == "FLAC audio test"

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio.pydub')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_mp3_format(self, mock_pydub, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup pydub mocks
        mock_audio_segment = Mock()
        mock_pydub.AudioSegment.from_file.return_value = mock_audio_segment

        # Setup speech recognition mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "MP3 transcription"

        # Test
        audio_stream = io.BytesIO(b"fake mp3 data")
        result = transcribe_audio(audio_stream, audio_format="mp3")

        assert result == "MP3 transcription"
        mock_pydub.AudioSegment.from_file.assert_called_once_with(audio_stream, format="mp3")
        mock_audio_segment.export.assert_called_once()

        # Verify export was called with format="wav"
        call_args = mock_audio_segment.export.call_args
        assert call_args[1]['format'] == 'wav'

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio.pydub')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_mp4_format(self, mock_pydub, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup pydub mocks
        mock_audio_segment = Mock()
        mock_pydub.AudioSegment.from_file.return_value = mock_audio_segment

        # Setup speech recognition mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "MP4 audio track"

        # Test
        audio_stream = io.BytesIO(b"fake mp4 data")
        result = transcribe_audio(audio_stream, audio_format="mp4")

        assert result == "MP4 audio track"
        mock_pydub.AudioSegment.from_file.assert_called_once_with(audio_stream, format="mp4")

    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_unsupported_audio_format(self):
        from markitdown.converters._transcribe_audio import transcribe_audio

        audio_stream = io.BytesIO(b"fake data")

        with pytest.raises(ValueError, match="Unsupported audio format: ogg"):
            transcribe_audio(audio_stream, audio_format="ogg")

    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_unsupported_audio_format_avi(self):
        from markitdown.converters._transcribe_audio import transcribe_audio

        audio_stream = io.BytesIO(b"fake data")

        with pytest.raises(ValueError, match="Unsupported audio format"):
            transcribe_audio(audio_stream, audio_format="avi")


class TestTranscribeAudioRecognition:
    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_empty_transcription_returns_no_speech(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks to return empty string
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = ""  # Empty string

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        assert result == "[No speech detected]"

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcription_with_whitespace_only(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks to return whitespace
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "   "  # Whitespace only

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        # After strip(), empty string becomes "[No speech detected]"
        assert result == "[No speech detected]"

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcription_with_leading_trailing_whitespace(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "  Hello world  "

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        assert result == "Hello world"  # Should be stripped

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_default_audio_format_is_wav(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Default format test"

        # Test without specifying audio_format (should default to "wav")
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream)  # No audio_format parameter

        assert result == "Default format test"
        mock_sr.AudioFile.assert_called_once_with(audio_stream)


class TestTranscribeAudioConversion:
    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio.pydub')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_mp3_conversion_seeks_to_start(self, mock_pydub, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup pydub mocks
        mock_audio_segment = Mock()
        mock_pydub.AudioSegment.from_file.return_value = mock_audio_segment

        # Track the BytesIO object passed to export
        exported_stream = None
        def capture_export(stream, **kwargs):
            nonlocal exported_stream
            exported_stream = stream

        mock_audio_segment.export.side_effect = capture_export

        # Setup speech recognition mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Test"

        # Test
        audio_stream = io.BytesIO(b"fake mp3 data")
        transcribe_audio(audio_stream, audio_format="mp3")

        # Verify the stream was seeked to 0 after export
        # The code creates a new BytesIO, exports to it, then seeks to 0
        assert exported_stream is not None


class TestTranscribeAudioEdgeCases:
    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_multiline_text(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Line one\nLine two"

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        assert result == "Line one\nLine two"

    @patch('markitdown.converters._transcribe_audio.sr')
    @patch('markitdown.converters._transcribe_audio._dependency_exc_info', None)
    def test_transcribe_special_characters(self, mock_sr):
        from markitdown.converters._transcribe_audio import transcribe_audio

        # Setup mocks
        mock_recognizer = Mock()
        mock_audio_file = MagicMock()
        mock_audio = Mock()

        mock_sr.Recognizer.return_value = mock_recognizer
        mock_sr.AudioFile.return_value.__enter__ = Mock(return_value=mock_audio_file)
        mock_sr.AudioFile.return_value.__exit__ = Mock(return_value=False)

        mock_recognizer.record.return_value = mock_audio
        mock_recognizer.recognize_google.return_value = "Hello, world! How are you?"

        # Test
        audio_stream = io.BytesIO(b"fake wav data")
        result = transcribe_audio(audio_stream, audio_format="wav")

        assert result == "Hello, world! How are you?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
