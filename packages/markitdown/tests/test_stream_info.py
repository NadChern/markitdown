import pytest
from dataclasses import asdict

from markitdown._stream_info import StreamInfo


class TestStreamInfoConstructor:
    """Test StreamInfo dataclass construction."""

    def test_constructor_empty(self):
        """Test that StreamInfo can be created with no arguments (all fields default to None)."""
        stream_info = StreamInfo()
        assert stream_info.mimetype is None
        assert stream_info.extension is None
        assert stream_info.charset is None
        assert stream_info.filename is None
        assert stream_info.local_path is None
        assert stream_info.url is None

    def test_constructor_all_fields(self):
        """Test that StreamInfo can be created with all fields."""
        stream_info = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
            filename="test.txt",
            local_path="/path/to/test.txt",
            url="https://example.com/test.txt",
        )
        assert stream_info.mimetype == "text/plain"
        assert stream_info.extension == ".txt"
        assert stream_info.charset == "utf-8"
        assert stream_info.filename == "test.txt"
        assert stream_info.local_path == "/path/to/test.txt"
        assert stream_info.url == "https://example.com/test.txt"

    def test_constructor_single_field(self):
        """Test that StreamInfo can be created with a single field."""
        stream_info = StreamInfo(mimetype="application/pdf")
        assert stream_info.mimetype == "application/pdf"
        assert stream_info.extension is None
        assert stream_info.charset is None
        assert stream_info.filename is None
        assert stream_info.local_path is None
        assert stream_info.url is None

    def test_constructor_multiple_fields(self):
        """Test that StreamInfo can be created with multiple fields."""
        stream_info = StreamInfo(
            extension=".csv",
            mimetype="text/csv",
            charset="utf-8",
        )
        assert stream_info.extension == ".csv"
        assert stream_info.mimetype == "text/csv"
        assert stream_info.charset == "utf-8"
        assert stream_info.filename is None
        assert stream_info.local_path is None
        assert stream_info.url is None

    def test_constructor_requires_keyword_arguments(self):
        """Test that StreamInfo requires keyword arguments (kw_only=True)."""
        with pytest.raises(TypeError):
            # This should fail because positional arguments are not allowed
            StreamInfo("text/plain", ".txt")  # type: ignore

    def test_constructor_rejects_unknown_fields(self):
        """Test that StreamInfo rejects unknown field names."""
        with pytest.raises(TypeError):
            StreamInfo(unknown_field="value")  # type: ignore

    def test_constructor_with_none_values(self):
        """Test that StreamInfo can be created with explicit None values."""
        stream_info = StreamInfo(
            mimetype="text/plain",
            extension=None,
            charset=None,
        )
        assert stream_info.mimetype == "text/plain"
        assert stream_info.extension is None
        assert stream_info.charset is None


class TestStreamInfoImmutability:
    """Test that StreamInfo is immutable (frozen=True)."""

    def test_cannot_modify_mimetype(self):
        """Test that mimetype field cannot be modified after creation."""
        stream_info = StreamInfo(mimetype="text/plain")
        with pytest.raises(AttributeError):
            stream_info.mimetype = "application/pdf"  # type: ignore

    def test_cannot_modify_extension(self):
        """Test that extension field cannot be modified after creation."""
        stream_info = StreamInfo(extension=".txt")
        with pytest.raises(AttributeError):
            stream_info.extension = ".pdf"  # type: ignore

    def test_cannot_modify_charset(self):
        """Test that charset field cannot be modified after creation."""
        stream_info = StreamInfo(charset="utf-8")
        with pytest.raises(AttributeError):
            stream_info.charset = "ascii"  # type: ignore

    def test_cannot_modify_filename(self):
        """Test that filename field cannot be modified after creation."""
        stream_info = StreamInfo(filename="test.txt")
        with pytest.raises(AttributeError):
            stream_info.filename = "other.txt"  # type: ignore

    def test_cannot_modify_local_path(self):
        """Test that local_path field cannot be modified after creation."""
        stream_info = StreamInfo(local_path="/path/to/file")
        with pytest.raises(AttributeError):
            stream_info.local_path = "/other/path"  # type: ignore

    def test_cannot_modify_url(self):
        """Test that url field cannot be modified after creation."""
        stream_info = StreamInfo(url="https://example.com")
        with pytest.raises(AttributeError):
            stream_info.url = "https://other.com"  # type: ignore

    def test_cannot_add_new_attributes(self):
        """Test that new attributes cannot be added to StreamInfo."""
        stream_info = StreamInfo()
        with pytest.raises(AttributeError):
            stream_info.new_field = "value"  # type: ignore


class TestStreamInfoCopyAndUpdate:
    """Test the copy_and_update method."""

    def test_copy_and_update_with_single_streaminfo(self):
        """Test updating with a single StreamInfo object."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
        )
        update = StreamInfo(mimetype="application/pdf", extension=".pdf")

        result = original.copy_and_update(update)

        # Updated fields from update
        assert result.mimetype == "application/pdf"
        assert result.extension == ".pdf"
        # Preserved field from original
        assert result.charset == "utf-8"
        # Original remains unchanged (immutability check)
        assert original.mimetype == "text/plain"
        assert original.extension == ".txt"

    def test_copy_and_update_with_kwargs_only(self):
        """Test updating with keyword arguments only."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
        )

        result = original.copy_and_update(mimetype="application/pdf", charset="utf-8")

        assert result.mimetype == "application/pdf"
        assert result.extension == ".txt"
        assert result.charset == "utf-8"

    def test_copy_and_update_with_streaminfo_and_kwargs(self):
        """Test updating with both StreamInfo objects and keyword arguments."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
        )
        update = StreamInfo(mimetype="application/pdf")

        result = original.copy_and_update(update, extension=".pdf", filename="test.pdf")

        assert result.mimetype == "application/pdf"  # From StreamInfo
        assert result.extension == ".pdf"  # From kwargs
        assert result.filename == "test.pdf"  # From kwargs
        assert result.charset == "utf-8"  # From original

    def test_copy_and_update_multiple_streaminfo_objects(self):
        """Test updating with multiple StreamInfo objects (later ones override earlier)."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
        )
        update1 = StreamInfo(mimetype="application/json", charset="utf-8")
        update2 = StreamInfo(mimetype="application/xml", filename="test.xml")

        result = original.copy_and_update(update1, update2)

        # update2 overrides update1's mimetype
        assert result.mimetype == "application/xml"
        assert result.extension == ".txt"  # From original
        assert result.charset == "utf-8"  # From update1
        assert result.filename == "test.xml"  # From update2

    def test_copy_and_update_kwargs_override_streaminfo(self):
        """Test that keyword arguments override StreamInfo objects."""
        original = StreamInfo(mimetype="text/plain")
        update = StreamInfo(mimetype="application/json")

        result = original.copy_and_update(update, mimetype="application/xml")

        # kwargs should override the StreamInfo argument
        assert result.mimetype == "application/xml"

    def test_copy_and_update_ignores_none_values_in_streaminfo(self):
        """Test that None values from StreamInfo objects are not copied."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
        )
        # Update has None for extension (should not override original)
        update = StreamInfo(mimetype="application/pdf", extension=None)

        result = original.copy_and_update(update)

        assert result.mimetype == "application/pdf"
        # Extension should remain from original, not be overwritten with None
        assert result.extension == ".txt"
        assert result.charset == "utf-8"

    def test_copy_and_update_allows_none_values_in_kwargs(self):
        """Test that None values in kwargs ARE applied (unlike StreamInfo args)."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
        )

        result = original.copy_and_update(extension=None)

        # kwargs None values should be applied
        assert result.mimetype == "text/plain"
        assert result.extension is None

    def test_copy_and_update_empty_call(self):
        """Test copy_and_update with no arguments creates an identical copy."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
        )

        result = original.copy_and_update()

        assert result.mimetype == original.mimetype
        assert result.extension == original.extension
        assert result.charset == original.charset
        assert result.filename == original.filename
        assert result.local_path == original.local_path
        assert result.url == original.url
        # Should be a different object
        assert result is not original

    def test_copy_and_update_all_fields(self):
        """Test updating all fields at once."""
        original = StreamInfo()

        result = original.copy_and_update(
            mimetype="application/pdf",
            extension=".pdf",
            charset="utf-8",
            filename="document.pdf",
            local_path="/path/to/document.pdf",
            url="https://example.com/document.pdf",
        )

        assert result.mimetype == "application/pdf"
        assert result.extension == ".pdf"
        assert result.charset == "utf-8"
        assert result.filename == "document.pdf"
        assert result.local_path == "/path/to/document.pdf"
        assert result.url == "https://example.com/document.pdf"

    def test_copy_and_update_rejects_non_streaminfo(self):
        """Test that copy_and_update raises AssertionError for non-StreamInfo arguments."""
        original = StreamInfo(mimetype="text/plain")

        with pytest.raises(AssertionError):
            original.copy_and_update({"mimetype": "application/pdf"})  # type: ignore

        with pytest.raises(AssertionError):
            original.copy_and_update("not a streaminfo")  # type: ignore

    def test_copy_and_update_preserves_unspecified_fields(self):
        """Test that fields not mentioned in update are preserved from original."""
        original = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
            filename="test.txt",
            local_path="/path/to/test.txt",
            url="https://example.com/test.txt",
        )

        result = original.copy_and_update(mimetype="application/json")

        # Only mimetype changed
        assert result.mimetype == "application/json"
        # All others preserved
        assert result.extension == ".txt"
        assert result.charset == "utf-8"
        assert result.filename == "test.txt"
        assert result.local_path == "/path/to/test.txt"
        assert result.url == "https://example.com/test.txt"


class TestStreamInfoDataclassFeatures:
    """Test dataclass-specific features of StreamInfo."""

    def test_asdict_works(self):
        """Test that asdict() works with StreamInfo."""
        stream_info = StreamInfo(
            mimetype="text/plain",
            extension=".txt",
            charset="utf-8",
        )

        result = asdict(stream_info)

        assert isinstance(result, dict)
        assert result["mimetype"] == "text/plain"
        assert result["extension"] == ".txt"
        assert result["charset"] == "utf-8"
        assert result["filename"] is None
        assert result["local_path"] is None
        assert result["url"] is None

    def test_equality_comparison(self):
        """Test that StreamInfo supports equality comparison."""
        info1 = StreamInfo(mimetype="text/plain", extension=".txt")
        info2 = StreamInfo(mimetype="text/plain", extension=".txt")
        info3 = StreamInfo(mimetype="text/plain", extension=".csv")

        assert info1 == info2
        assert info1 != info3

    def test_repr_works(self):
        """Test that StreamInfo has a useful repr."""
        stream_info = StreamInfo(mimetype="text/plain", extension=".txt")
        repr_str = repr(stream_info)

        assert "StreamInfo" in repr_str
        assert "mimetype='text/plain'" in repr_str
        assert "extension='.txt'" in repr_str

    def test_hash_works_for_frozen_dataclass(self):
        """Test that frozen StreamInfo objects are hashable."""
        stream_info = StreamInfo(mimetype="text/plain")
        # Should not raise an error
        hash_value = hash(stream_info)
        assert isinstance(hash_value, int)

        # Can be used in sets and as dict keys
        info_set = {stream_info}
        assert stream_info in info_set

        info_dict = {stream_info: "value"}
        assert info_dict[stream_info] == "value"


# Parametrized tests for field assignment
class TestStreamInfoParametrized:
    """Parametrized tests for StreamInfo fields."""

    @pytest.mark.parametrize("field,value", [
        ("mimetype", "text/plain"),
        ("extension", ".txt"),
        ("charset", "utf-8"),
        ("filename", "test.txt"),
        ("local_path", "/path/to/file"),
        ("url", "https://example.com"),
    ])
    def test_individual_field_assignment(self, field, value):
        """Test that each field can be set individually."""
        stream_info = StreamInfo(**{field: value})
        assert getattr(stream_info, field) == value

    @pytest.mark.parametrize("field", [
        "mimetype",
        "extension",
        "charset",
        "filename",
        "local_path",
        "url",
    ])
    def test_individual_field_defaults_to_none(self, field):
        """Test that each field defaults to None when not specified."""
        stream_info = StreamInfo()
        assert getattr(stream_info, field) is None

    @pytest.mark.parametrize("field,value", [
        ("mimetype", "application/json"),
        ("extension", ".json"),
        ("charset", "ascii"),
        ("filename", "new.json"),
        ("local_path", "/new/path"),
        ("url", "https://new.com"),
    ])
    def test_copy_and_update_individual_fields(self, field, value):
        """Test that copy_and_update works for each field."""
        original = StreamInfo(mimetype="text/plain")
        result = original.copy_and_update(**{field: value})
        assert getattr(result, field) == value


if __name__ == "__main__":
    """Runs this file's tests from the command line."""
    pytest.main([__file__, "-v"])
