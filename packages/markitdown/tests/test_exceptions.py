import pytest
import sys
from unittest.mock import Mock

from markitdown._exceptions import (
    MarkItDownException,
    MissingDependencyException,
    UnsupportedFormatException,
    FileConversionException,
    FailedConversionAttempt,
    MISSING_DEPENDENCY_MESSAGE,
)


class TestMarkItDownException:
    """Test the base MarkItDown exception class."""

    def test_can_be_raised(self):
        """Test that MarkItDownException can be raised."""
        with pytest.raises(MarkItDownException):
            raise MarkItDownException()

    def test_can_be_raised_with_message(self):
        """Test that MarkItDownException can be raised with a custom message."""
        with pytest.raises(MarkItDownException) as exc_info:
            raise MarkItDownException("Custom error message")
        assert str(exc_info.value) == "Custom error message"

    def test_inherits_from_exception(self):
        """Test that MarkItDownException inherits from Exception."""
        assert issubclass(MarkItDownException, Exception)

    def test_can_be_caught_as_exception(self):
        """Test that MarkItDownException can be caught as a generic Exception."""
        with pytest.raises(Exception):
            raise MarkItDownException("Test error")


class TestMissingDependencyException:
    """Test the MissingDependencyException class."""

    def test_can_be_raised(self):
        """Test that MissingDependencyException can be raised."""
        with pytest.raises(MissingDependencyException):
            raise MissingDependencyException()

    def test_can_be_raised_with_message(self):
        """Test that MissingDependencyException can be raised with a custom message."""
        with pytest.raises(MissingDependencyException) as exc_info:
            raise MissingDependencyException("Missing required library")
        assert str(exc_info.value) == "Missing required library"

    def test_inherits_from_markitdown_exception(self):
        """Test that MissingDependencyException inherits from MarkItDownException."""
        assert issubclass(MissingDependencyException, MarkItDownException)

    def test_can_be_caught_as_markitdown_exception(self):
        """Test that MissingDependencyException can be caught as MarkItDownException."""
        with pytest.raises(MarkItDownException):
            raise MissingDependencyException("Test error")

    def test_can_be_caught_as_exception(self):
        """Test that MissingDependencyException can be caught as generic Exception."""
        with pytest.raises(Exception):
            raise MissingDependencyException("Test error")


class TestUnsupportedFormatException:
    """Test the UnsupportedFormatException class."""

    def test_can_be_raised(self):
        """Test that UnsupportedFormatException can be raised."""
        with pytest.raises(UnsupportedFormatException):
            raise UnsupportedFormatException()

    def test_can_be_raised_with_message(self):
        """Test that UnsupportedFormatException can be raised with a custom message."""
        with pytest.raises(UnsupportedFormatException) as exc_info:
            raise UnsupportedFormatException("Unsupported file format: .xyz")
        assert str(exc_info.value) == "Unsupported file format: .xyz"

    def test_inherits_from_markitdown_exception(self):
        """Test that UnsupportedFormatException inherits from MarkItDownException."""
        assert issubclass(UnsupportedFormatException, MarkItDownException)

    def test_can_be_caught_as_markitdown_exception(self):
        """Test that UnsupportedFormatException can be caught as MarkItDownException."""
        with pytest.raises(MarkItDownException):
            raise UnsupportedFormatException("Test error")

    def test_can_be_caught_as_exception(self):
        """Test that UnsupportedFormatException can be caught as generic Exception."""
        with pytest.raises(Exception):
            raise UnsupportedFormatException("Test error")


class TestFailedConversionAttempt:
    """Test the FailedConversionAttempt helper class."""

    def test_constructor_with_converter_and_exc_info(self):
        """Test FailedConversionAttempt with both converter and exc_info."""
        mock_converter = Mock()
        mock_converter.__class__.__name__ = "TestConverter"

        # Create real exception info
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        attempt = FailedConversionAttempt(mock_converter, exc_info)

        assert attempt.converter is mock_converter
        assert attempt.exc_info is exc_info
        assert attempt.exc_info[0] is ValueError

    def test_constructor_with_converter_only(self):
        """Test FailedConversionAttempt with converter only (exc_info defaults to None)."""
        mock_converter = Mock()
        mock_converter.__class__.__name__ = "TestConverter"

        attempt = FailedConversionAttempt(mock_converter)

        assert attempt.converter is mock_converter
        assert attempt.exc_info is None

    def test_constructor_with_none_exc_info(self):
        """Test FailedConversionAttempt with explicitly None exc_info."""
        mock_converter = Mock()

        attempt = FailedConversionAttempt(mock_converter, None)

        assert attempt.converter is mock_converter
        assert attempt.exc_info is None


class TestFileConversionException:
    """Test the FileConversionException class."""

    def test_can_be_raised(self):
        """Test that FileConversionException can be raised."""
        with pytest.raises(FileConversionException):
            raise FileConversionException()

    def test_inherits_from_markitdown_exception(self):
        """Test that FileConversionException inherits from MarkItDownException."""
        assert issubclass(FileConversionException, MarkItDownException)

    def test_constructor_with_custom_message(self):
        """Test FileConversionException with a custom message."""
        exc = FileConversionException(message="Custom conversion error")
        assert str(exc) == "Custom conversion error"
        assert exc.attempts is None

    def test_constructor_with_custom_message_and_attempts(self):
        """Test FileConversionException with custom message and attempts."""
        mock_converter = Mock()
        attempts = [FailedConversionAttempt(mock_converter)]

        exc = FileConversionException(message="Custom error", attempts=attempts)

        assert str(exc) == "Custom error"
        assert exc.attempts is attempts
        assert len(exc.attempts) == 1

    def test_constructor_no_message_no_attempts(self):
        """Test FileConversionException with no message and no attempts (default message)."""
        exc = FileConversionException()
        assert str(exc) == "File conversion failed."
        assert exc.attempts is None

    def test_constructor_no_message_with_attempts_no_exc_info(self):
        """Test FileConversionException generates message from attempts without exc_info."""
        mock_converter = Mock()
        mock_converter.__class__.__name__ = "TestConverter"

        attempts = [FailedConversionAttempt(mock_converter, None)]
        exc = FileConversionException(attempts=attempts)

        assert exc.attempts is attempts
        assert "File conversion failed after 1 attempts:" in str(exc)
        assert "TestConverter provided no execution info." in str(exc)

    def test_constructor_no_message_with_attempts_with_exc_info(self):
        """Test FileConversionException generates message from attempts with exc_info."""
        mock_converter = Mock()
        mock_converter.__class__.__name__ = "PdfConverter"

        # Create real exception info
        try:
            raise ValueError("Invalid PDF format")
        except ValueError:
            exc_info = sys.exc_info()

        attempts = [FailedConversionAttempt(mock_converter, exc_info)]
        exc = FileConversionException(attempts=attempts)

        assert exc.attempts is attempts
        assert "File conversion failed after 1 attempts:" in str(exc)
        assert "PdfConverter threw ValueError with message: Invalid PDF format" in str(exc)

    def test_constructor_multiple_attempts_mixed_exc_info(self):
        """Test FileConversionException with multiple attempts, some with exc_info and some without."""
        # First converter with no exc_info
        mock_converter1 = Mock()
        mock_converter1.__class__.__name__ = "Converter1"
        attempt1 = FailedConversionAttempt(mock_converter1, None)

        # Second converter with exc_info
        mock_converter2 = Mock()
        mock_converter2.__class__.__name__ = "Converter2"
        try:
            raise RuntimeError("Runtime error occurred")
        except RuntimeError:
            exc_info2 = sys.exc_info()
        attempt2 = FailedConversionAttempt(mock_converter2, exc_info2)

        # Third converter with different exception
        mock_converter3 = Mock()
        mock_converter3.__class__.__name__ = "Converter3"
        try:
            raise KeyError("Key error occurred")
        except KeyError:
            exc_info3 = sys.exc_info()
        attempt3 = FailedConversionAttempt(mock_converter3, exc_info3)

        attempts = [attempt1, attempt2, attempt3]
        exc = FileConversionException(attempts=attempts)

        message = str(exc)
        assert "File conversion failed after 3 attempts:" in message
        assert "Converter1 provided no execution info." in message
        assert "Converter2 threw RuntimeError with message: Runtime error occurred" in message
        assert "Converter3 threw KeyError with message: 'Key error occurred'" in message

    def test_can_be_caught_as_markitdown_exception(self):
        """Test that FileConversionException can be caught as MarkItDownException."""
        with pytest.raises(MarkItDownException):
            raise FileConversionException("Test error")

    def test_can_be_caught_as_exception(self):
        """Test that FileConversionException can be caught as generic Exception."""
        with pytest.raises(Exception):
            raise FileConversionException("Test error")


class TestMissingDependencyMessage:
    """Test the MISSING_DEPENDENCY_MESSAGE constant."""

    def test_message_is_string(self):
        """Test that MISSING_DEPENDENCY_MESSAGE is a string."""
        assert isinstance(MISSING_DEPENDENCY_MESSAGE, str)

    def test_message_can_be_formatted(self):
        """Test that MISSING_DEPENDENCY_MESSAGE can be formatted with placeholders."""
        formatted = MISSING_DEPENDENCY_MESSAGE.format(
            converter="PdfConverter",
            extension=".pdf",
            feature="pdf"
        )

        assert "PdfConverter" in formatted
        assert ".pdf" in formatted
        assert "pip install markitdown[pdf]" in formatted
        assert "pip install markitdown[all]" in formatted

    def test_message_contains_required_placeholders(self):
        """Test that MISSING_DEPENDENCY_MESSAGE contains the expected placeholders."""
        assert "{converter}" in MISSING_DEPENDENCY_MESSAGE
        assert "{extension}" in MISSING_DEPENDENCY_MESSAGE
        assert "{feature}" in MISSING_DEPENDENCY_MESSAGE

    def test_message_contains_pip_install_instructions(self):
        """Test that MISSING_DEPENDENCY_MESSAGE contains pip install instructions."""
        assert "pip install" in MISSING_DEPENDENCY_MESSAGE
        assert "markitdown[" in MISSING_DEPENDENCY_MESSAGE

    def test_formatted_message_example(self):
        """Test a realistic example of formatting the message."""
        formatted = MISSING_DEPENDENCY_MESSAGE.format(
            converter="DocxConverter",
            extension=".docx",
            feature="docx"
        )

        assert "DocxConverter recognized the input as a potential .docx file" in formatted
        assert "pip install markitdown[docx]" in formatted
        assert "dependencies needed to read .docx files have not been installed" in formatted


# Parametrized tests for exception hierarchy
class TestExceptionHierarchy:
    """Test the exception hierarchy relationships."""

    @pytest.mark.parametrize("exception_class,parent_class", [
        (MarkItDownException, Exception),
        (MissingDependencyException, MarkItDownException),
        (UnsupportedFormatException, MarkItDownException),
        (FileConversionException, MarkItDownException),
    ])
    def test_inheritance_hierarchy(self, exception_class, parent_class):
        """Test that each exception class inherits from the correct parent."""
        assert issubclass(exception_class, parent_class)

    @pytest.mark.parametrize("exception_class", [
        MissingDependencyException,
        UnsupportedFormatException,
        FileConversionException,
    ])
    def test_all_custom_exceptions_inherit_from_base(self, exception_class):
        """Test that all custom exceptions inherit from MarkItDownException."""
        assert issubclass(exception_class, MarkItDownException)

    @pytest.mark.parametrize("exception_class", [
        MarkItDownException,
        MissingDependencyException,
        UnsupportedFormatException,
        FileConversionException,
    ])
    def test_all_exceptions_inherit_from_exception(self, exception_class):
        """Test that all exception classes ultimately inherit from Exception."""
        assert issubclass(exception_class, Exception)


if __name__ == "__main__":
    """Runs this file's tests from the command line."""
    pytest.main([__file__, "-v"])
