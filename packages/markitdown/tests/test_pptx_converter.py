import io
import sys
import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from markitdown import DocumentConverterResult, StreamInfo
from markitdown.converters._pptx_converter import (
    PptxConverter,
    ACCEPTED_MIME_TYPE_PREFIXES,
    ACCEPTED_FILE_EXTENSIONS,
)
from markitdown._exceptions import MissingDependencyException


def create_mock_shapes(shapes_list, title=None):
    """Helper to create a mock shapes collection that's both iterable and has a title attribute"""
    mock_shapes = Mock()
    mock_shapes.__iter__ = Mock(return_value=iter(shapes_list))
    mock_shapes.title = title
    return mock_shapes


class TestPptxConverterAccepts:
    def test_accepts_pptx_extension(self):
        converter = PptxConverter()
        stream_info = StreamInfo(extension=".pptx")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_pptx_extension_uppercase(self):
        converter = PptxConverter()
        stream_info = StreamInfo(extension=".PPTX")
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_pptx_mimetype(self):
        converter = PptxConverter()
        stream_info = StreamInfo(
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_pptx_mimetype_with_suffix(self):
        converter = PptxConverter()
        stream_info = StreamInfo(
            mimetype="application/vnd.openxmlformats-officedocument.presentationml.slideshow"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_accepts_mimetype_case_insensitive(self):
        converter = PptxConverter()
        stream_info = StreamInfo(
            mimetype="APPLICATION/VND.OPENXMLFORMATS-OFFICEDOCUMENT.PRESENTATIONML.PRESENTATION"
        )
        assert converter.accepts(io.BytesIO(), stream_info) is True

    def test_rejects_wrong_extension(self):
        converter = PptxConverter()
        stream_info = StreamInfo(extension=".pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_wrong_mimetype(self):
        converter = PptxConverter()
        stream_info = StreamInfo(mimetype="application/pdf")
        assert converter.accepts(io.BytesIO(), stream_info) is False

    def test_rejects_empty_stream_info(self):
        converter = PptxConverter()
        stream_info = StreamInfo()
        assert converter.accepts(io.BytesIO(), stream_info) is False


class TestPptxConverterDependencies:
    @patch('markitdown.converters._pptx_converter._dependency_exc_info', (ImportError, ImportError("pptx not found"), None))
    def test_convert_raises_missing_dependency_exception(self):
        converter = PptxConverter()
        stream_info = StreamInfo(extension=".pptx")

        with pytest.raises(MissingDependencyException):
            converter.convert(io.BytesIO(), stream_info)


class TestPptxConverterConvert:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_simple_presentation(self, mock_pptx):
        # Create mock presentation with one slide
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_shape = Mock()

        # Setup shape
        mock_shape.shape_type = Mock()
        mock_shape.has_text_frame = True
        mock_shape.text = "Test content"
        mock_shape.has_chart = False
        mock_shape.top = 100
        mock_shape.left = 100

        # Setup slide
        mock_slide.shapes = create_mock_shapes([mock_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        stream_info = StreamInfo(extension=".pptx")

        result = converter.convert(io.BytesIO(), stream_info)

        assert isinstance(result, DocumentConverterResult)
        assert "Test content" in result.markdown
        assert "Slide number: 1" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_presentation_with_title(self, mock_pptx):
        # Create mock presentation
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_title_shape = Mock()

        # Setup title shape
        mock_title_shape.shape_type = Mock()
        mock_title_shape.has_text_frame = True
        mock_title_shape.text = "Test Title"
        mock_title_shape.has_chart = False
        mock_title_shape.top = 100
        mock_title_shape.left = 100

        # Setup slide
        mock_slide.shapes = create_mock_shapes([mock_title_shape], title=mock_title_shape)
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "# Test Title" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_presentation_with_notes(self, mock_pptx):
        # Create mock presentation
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_notes_slide = Mock()
        mock_notes_frame = Mock()

        mock_notes_frame.text = "These are notes"
        mock_notes_slide.notes_text_frame = mock_notes_frame

        mock_slide.shapes = create_mock_shapes([])
        mock_slide.shapes.title = None
        mock_slide.has_notes_slide = True
        mock_slide.notes_slide = mock_notes_slide

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "### Notes:" in result.markdown
        assert "These are notes" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_presentation_with_notes_none_frame(self, mock_pptx):
        # Create mock presentation with notes_text_frame = None
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_notes_slide = Mock()

        mock_notes_slide.notes_text_frame = None

        mock_slide.shapes = create_mock_shapes([])
        mock_slide.shapes.title = None
        mock_slide.has_notes_slide = True
        mock_slide.notes_slide = mock_notes_slide

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "### Notes:" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_multiple_slides(self, mock_pptx):
        # Create mock presentation with multiple slides
        mock_presentation = Mock()
        mock_slide1 = Mock()
        mock_slide2 = Mock()

        for slide in [mock_slide1, mock_slide2]:
            slide.shapes = create_mock_shapes([])
            slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide1, mock_slide2]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "Slide number: 1" in result.markdown
        assert "Slide number: 2" in result.markdown


class TestPptxConverterPictures:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_picture_without_llm(self, mock_pptx):
        # Create mock presentation with picture
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_picture = Mock()

        # Setup picture shape - shape_type needs to match the enum value for comparison
        picture_type = Mock()
        mock_picture.shape_type = picture_type
        mock_picture.has_text_frame = False
        mock_picture.has_chart = False
        mock_picture.top = 100
        mock_picture.left = 100
        mock_picture.name = "Picture1"

        # Setup image
        mock_image = Mock()
        mock_image.blob = b"fake_image_data"
        mock_image.content_type = "image/png"
        mock_image.filename = "test.png"
        mock_picture.image = mock_image

        # Mock _element for alt text
        mock_element = Mock()
        mock_element._nvXxPr.cNvPr.attrib.get.return_value = "Alt text"
        mock_picture._element = mock_element

        mock_slide.shapes = create_mock_shapes([mock_picture])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        # Set the enum value to match shape_type
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = picture_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "![" in result.markdown
        assert ".jpg)" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_picture_with_data_uri(self, mock_pptx):
        # Create mock presentation with picture
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_picture = Mock()

        mock_picture.shape_type = Mock()
        mock_picture.has_text_frame = False
        mock_picture.has_chart = False
        mock_picture.top = 100
        mock_picture.left = 100
        mock_picture.name = "Picture1"

        mock_image = Mock()
        mock_image.blob = b"test"
        mock_image.content_type = "image/png"
        mock_image.filename = "test.png"
        mock_picture.image = mock_image

        # Mock alt text to raise exception
        mock_picture._element = Mock()
        mock_picture._element._nvXxPr.cNvPr.attrib.get.side_effect = Exception("No alt text")

        mock_slide.shapes = create_mock_shapes([mock_picture])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = mock_picture.shape_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"), keep_data_uris=True)

        assert "data:image/png;base64," in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    @patch('markitdown.converters._pptx_converter.llm_caption')
    def test_convert_picture_with_llm_caption(self, mock_llm_caption, mock_pptx):
        # Create mock presentation with picture
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_picture = Mock()

        mock_picture.shape_type = Mock()
        mock_picture.has_text_frame = False
        mock_picture.has_chart = False
        mock_picture.top = 100
        mock_picture.left = 100
        mock_picture.name = "Picture1"

        mock_image = Mock()
        mock_image.blob = b"test"
        mock_image.content_type = "image/png"
        mock_image.filename = "test.png"
        mock_picture.image = mock_image

        mock_picture._element = Mock()
        mock_picture._element._nvXxPr.cNvPr.attrib.get.return_value = ""

        mock_slide.shapes = create_mock_shapes([mock_picture])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = mock_picture.shape_type

        mock_llm_caption.return_value = "LLM generated caption"

        converter = PptxConverter()
        mock_llm_client = Mock()
        result = converter.convert(
            io.BytesIO(),
            StreamInfo(extension=".pptx"),
            llm_client=mock_llm_client,
            llm_model="gpt-4",
            llm_prompt="Describe this"
        )

        assert "LLM generated caption" in result.markdown
        mock_llm_caption.assert_called_once()

    @patch('markitdown.converters._pptx_converter.pptx')
    @patch('markitdown.converters._pptx_converter.llm_caption')
    def test_convert_picture_llm_caption_exception(self, mock_llm_caption, mock_pptx):
        # Create mock presentation
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_picture = Mock()

        mock_picture.shape_type = Mock()
        mock_picture.has_text_frame = False
        mock_picture.has_chart = False
        mock_picture.top = 100
        mock_picture.left = 100
        mock_picture.name = "Picture1"

        mock_image = Mock()
        mock_image.blob = b"test"
        mock_image.content_type = "image/png"
        mock_image.filename = "test.png"
        mock_picture.image = mock_image

        mock_picture._element = Mock()
        mock_picture._element._nvXxPr.cNvPr.attrib.get.return_value = "Alt text"

        mock_slide.shapes = create_mock_shapes([mock_picture])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = mock_picture.shape_type

        # Make llm_caption raise an exception
        mock_llm_caption.side_effect = Exception("LLM error")

        converter = PptxConverter()
        mock_llm_client = Mock()
        result = converter.convert(
            io.BytesIO(),
            StreamInfo(extension=".pptx"),
            llm_client=mock_llm_client,
            llm_model="gpt-4"
        )

        # Should still succeed with alt text
        assert "Alt text" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_picture_no_filename(self, mock_pptx):
        # Create mock presentation with picture without filename
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_picture = Mock()

        mock_picture.shape_type = Mock()
        mock_picture.has_text_frame = False
        mock_picture.has_chart = False
        mock_picture.top = 100
        mock_picture.left = 100
        mock_picture.name = "Picture 1"

        mock_image = Mock()
        mock_image.blob = b"test"
        mock_image.content_type = "image/png"
        mock_image.filename = None  # No filename
        mock_picture.image = mock_image

        mock_picture._element = Mock()
        mock_picture._element._nvXxPr.cNvPr.attrib.get.return_value = ""

        mock_slide.shapes = create_mock_shapes([mock_picture])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = mock_picture.shape_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "![" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_is_picture_placeholder_with_image(self, mock_pptx):
        # Test _is_picture with PLACEHOLDER type that has image
        mock_shape = Mock()
        mock_shape.shape_type = Mock()
        mock_shape.image = Mock()

        placeholder_type = Mock()
        picture_type = Mock()
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PLACEHOLDER = mock_shape.shape_type
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = picture_type

        converter = PptxConverter()
        assert converter._is_picture(mock_shape) is True

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_is_picture_placeholder_without_image(self, mock_pptx):
        # Test _is_picture with PLACEHOLDER type that doesn't have image
        mock_shape = Mock(spec=['shape_type'])  # spec ensures no 'image' attribute
        mock_shape.shape_type = Mock()

        picture_type = Mock()
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PLACEHOLDER = mock_shape.shape_type
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = picture_type

        converter = PptxConverter()
        assert converter._is_picture(mock_shape) is False

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_is_not_picture(self, mock_pptx):
        # Test _is_picture returns False for non-picture shapes
        mock_shape = Mock()
        mock_shape.shape_type = Mock()

        picture_type = Mock()
        placeholder_type = Mock()
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE = picture_type
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.PLACEHOLDER = placeholder_type

        converter = PptxConverter()
        assert converter._is_picture(mock_shape) is False


class TestPptxConverterTables:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_table(self, mock_pptx):
        # Create mock presentation with table
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_table_shape = Mock()

        mock_table_shape.shape_type = Mock()
        mock_table_shape.has_text_frame = False
        mock_table_shape.has_chart = False
        mock_table_shape.top = 100
        mock_table_shape.left = 100

        # Create mock table
        mock_table = Mock()
        mock_row1 = Mock()
        mock_row2 = Mock()

        mock_cell1 = Mock()
        mock_cell1.text = "Header1"
        mock_cell2 = Mock()
        mock_cell2.text = "Header2"
        mock_cell3 = Mock()
        mock_cell3.text = "Data1"
        mock_cell4 = Mock()
        mock_cell4.text = "Data2"

        mock_row1.cells = [mock_cell1, mock_cell2]
        mock_row2.cells = [mock_cell3, mock_cell4]
        mock_table.rows = [mock_row1, mock_row2]

        mock_table_shape.table = mock_table

        mock_slide.shapes = create_mock_shapes([mock_table_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.TABLE = mock_table_shape.shape_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "Header1" in result.markdown
        assert "Header2" in result.markdown
        assert "Data1" in result.markdown
        assert "Data2" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_is_table(self, mock_pptx):
        # Test _is_table method
        mock_shape = Mock()
        mock_shape.shape_type = Mock()

        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.TABLE = mock_shape.shape_type

        converter = PptxConverter()
        assert converter._is_table(mock_shape) is True

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_is_not_table(self, mock_pptx):
        # Test _is_table returns False for non-table
        mock_shape = Mock()
        mock_shape.shape_type = Mock()

        table_type = Mock()
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.TABLE = table_type

        converter = PptxConverter()
        assert converter._is_table(mock_shape) is False


class TestPptxConverterCharts:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_chart_with_title(self, mock_pptx):
        # Create mock presentation with chart
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_chart_shape = Mock()

        mock_chart_shape.shape_type = Mock()
        mock_chart_shape.has_text_frame = False
        mock_chart_shape.has_chart = True
        mock_chart_shape.top = 100
        mock_chart_shape.left = 100

        # Create mock chart
        mock_chart = Mock()
        mock_chart.has_title = True
        mock_chart.chart_title.text_frame.text = "Sales Chart"

        # Create mock plot and categories
        mock_plot = Mock()
        mock_cat1 = Mock()
        mock_cat1.label = "Q1"
        mock_cat2 = Mock()
        mock_cat2.label = "Q2"
        mock_plot.categories = [mock_cat1, mock_cat2]
        mock_chart.plots = [mock_plot]

        # Create mock series
        mock_series = Mock()
        mock_series.name = "Revenue"
        mock_series.values = [100, 200]
        mock_chart.series = [mock_series]

        mock_chart_shape.chart = mock_chart

        mock_slide.shapes = create_mock_shapes([mock_chart_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "### Chart: Sales Chart" in result.markdown
        assert "Q1" in result.markdown
        assert "Q2" in result.markdown
        assert "Revenue" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_chart_without_title(self, mock_pptx):
        # Create mock chart without title
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_chart_shape = Mock()

        mock_chart_shape.has_chart = True
        mock_chart_shape.has_text_frame = False
        mock_chart_shape.top = 100
        mock_chart_shape.left = 100

        mock_chart = Mock()
        mock_chart.has_title = False

        mock_plot = Mock()
        mock_cat = Mock()
        mock_cat.label = "Category"
        mock_plot.categories = [mock_cat]
        mock_chart.plots = [mock_plot]

        mock_series = Mock()
        mock_series.name = "Series"
        mock_series.values = [50]
        mock_chart.series = [mock_series]

        mock_chart_shape.chart = mock_chart

        mock_slide.shapes = create_mock_shapes([mock_chart_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "### Chart\n\n" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_chart_unsupported_plot_type(self, mock_pptx):
        # Create mock chart that raises ValueError with "unsupported plot type"
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_chart_shape = Mock()

        mock_chart_shape.has_chart = True
        mock_chart_shape.has_text_frame = False
        mock_chart_shape.top = 100
        mock_chart_shape.left = 100

        mock_chart = Mock()
        mock_chart.has_title = False
        mock_chart.plots = Mock(side_effect=ValueError("unsupported plot type XYZ"))

        mock_chart_shape.chart = mock_chart

        mock_slide.shapes = create_mock_shapes([mock_chart_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "[unsupported chart]" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_chart_generic_exception(self, mock_pptx):
        # Create mock chart that raises a generic exception
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_chart_shape = Mock()

        mock_chart_shape.has_chart = True
        mock_chart_shape.has_text_frame = False
        mock_chart_shape.top = 100
        mock_chart_shape.left = 100

        mock_chart = Mock()
        mock_chart.has_title = Mock(side_effect=Exception("Unexpected error"))

        mock_chart_shape.chart = mock_chart

        mock_slide.shapes = create_mock_shapes([mock_chart_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "[unsupported chart]" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_chart_value_error_exact_message(self, mock_pptx):
        # Test that ValueError with exact "unsupported plot type" message triggers line 260-261
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_chart_shape = Mock()

        mock_chart_shape.has_chart = True
        mock_chart_shape.has_text_frame = False
        mock_chart_shape.top = 100
        mock_chart_shape.left = 100

        mock_chart = Mock()
        mock_chart.has_title = False
        # Make plots raise ValueError when accessed
        mock_chart.plots = Mock()
        mock_chart.plots.__getitem__ = Mock(side_effect=ValueError("This contains unsupported plot type in message"))

        mock_chart_shape.chart = mock_chart

        mock_slide.shapes = create_mock_shapes([mock_chart_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "[unsupported chart]" in result.markdown


class TestPptxConverterGroupShapes:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_group_shape(self, mock_pptx):
        # Create mock presentation with group shape
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_group_shape = Mock()

        mock_group_shape.shape_type = Mock()
        mock_group_shape.has_text_frame = False
        mock_group_shape.has_chart = False
        mock_group_shape.top = 100
        mock_group_shape.left = 100

        # Create subshapes within group
        mock_subshape1 = Mock()
        mock_subshape1.shape_type = Mock()
        mock_subshape1.has_text_frame = True
        mock_subshape1.has_chart = False
        mock_subshape1.text = "Text in group"
        mock_subshape1.top = 110
        mock_subshape1.left = 110

        mock_subshape2 = Mock()
        mock_subshape2.shape_type = Mock()
        mock_subshape2.has_text_frame = True
        mock_subshape2.has_chart = False
        mock_subshape2.text = "More text"
        mock_subshape2.top = 120
        mock_subshape2.left = 120

        mock_group_shape.shapes = [mock_subshape1, mock_subshape2]

        mock_slide.shapes = create_mock_shapes([mock_group_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.GROUP = mock_group_shape.shape_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "Text in group" in result.markdown
        assert "More text" in result.markdown

    @patch('markitdown.converters._pptx_converter.pptx')
    def test_convert_group_shape_with_none_positions(self, mock_pptx):
        # Test group shapes with None top/left positions
        mock_presentation = Mock()
        mock_slide = Mock()
        mock_group_shape = Mock()

        mock_group_shape.shape_type = Mock()
        mock_group_shape.has_text_frame = False
        mock_group_shape.has_chart = False
        mock_group_shape.top = None  # None position
        mock_group_shape.left = None

        mock_subshape = Mock()
        mock_subshape.shape_type = Mock()
        mock_subshape.has_text_frame = True
        mock_subshape.has_chart = False
        mock_subshape.text = "Text"
        mock_subshape.top = None  # None position
        mock_subshape.left = None

        mock_group_shape.shapes = [mock_subshape]

        mock_slide.shapes = create_mock_shapes([mock_group_shape])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation
        mock_pptx.enum.shapes.MSO_SHAPE_TYPE.GROUP = mock_group_shape.shape_type

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        assert "Text" in result.markdown


class TestPptxConverterShapeSorting:
    @patch('markitdown.converters._pptx_converter.pptx')
    def test_shapes_sorted_by_position(self, mock_pptx):
        # Test that shapes are sorted by top then left position
        mock_presentation = Mock()
        mock_slide = Mock()

        # Create shapes with different positions
        mock_shape1 = Mock()
        mock_shape1.has_text_frame = True
        mock_shape1.has_chart = False
        mock_shape1.text = "Bottom"
        mock_shape1.top = 200
        mock_shape1.left = 100
        mock_shape1.shape_type = Mock()

        mock_shape2 = Mock()
        mock_shape2.has_text_frame = True
        mock_shape2.has_chart = False
        mock_shape2.text = "Top"
        mock_shape2.top = 100
        mock_shape2.left = 100
        mock_shape2.shape_type = Mock()

        # Add shapes in wrong order
        mock_slide.shapes = create_mock_shapes([mock_shape1, mock_shape2])
        mock_slide.has_notes_slide = False

        mock_presentation.slides = [mock_slide]
        mock_pptx.Presentation.return_value = mock_presentation

        converter = PptxConverter()
        result = converter.convert(io.BytesIO(), StreamInfo(extension=".pptx"))

        # "Top" should appear before "Bottom" in output
        top_index = result.markdown.index("Top")
        bottom_index = result.markdown.index("Bottom")
        assert top_index < bottom_index


class TestPptxConverterConstants:
    def test_accepted_mime_type_prefixes(self):
        assert "application/vnd.openxmlformats-officedocument.presentationml" in ACCEPTED_MIME_TYPE_PREFIXES
        assert len(ACCEPTED_MIME_TYPE_PREFIXES) >= 1

    def test_accepted_file_extensions(self):
        assert ".pptx" in ACCEPTED_FILE_EXTENSIONS
        assert len(ACCEPTED_FILE_EXTENSIONS) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
