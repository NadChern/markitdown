import io
from types import SimpleNamespace

import pytest

from markitdown._stream_info import StreamInfo
from markitdown.converters._llm_caption import llm_caption


class FakeChatCompletions:
    def __init__(self):
        self.last_model = None
        self.last_messages = None

    def create(self, model, messages):
        self.last_model = model
        self.last_messages = messages
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Hello it's Lucian"),
                )
            ]
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeChatCompletions())


@pytest.fixture
def client():
    return FakeClient()


def test_llm_caption_default_prompt_and_restores_stream(client):
    data = b"abcdef"
    stream = io.BytesIO(data)
    stream.seek(2)
    start_pos = stream.tell()
    stream_info = StreamInfo(mimetype="image/jpeg", extension=".jpg")

    result = llm_caption(
        stream,
        stream_info,
        client=client,
        model="test-model",
        prompt="  ",
    )

    assert result == "Hello it's Lucian"
    assert stream.tell() == start_pos
    assert client.chat.completions.last_model == "test-model"
    messages = client.chat.completions.last_messages
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    text_part = next(p for p in content if p["type"] == "text")
    assert "Write a detailed caption for this image." in text_part["text"]
    image_part = next(p for p in content if p["type"] == "image_url")
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")


def test_llm_caption_uses_mimetypes_guess_type(monkeypatch, client):
    stream = io.BytesIO(b"x")
    stream_info = StreamInfo(mimetype=None, extension=".png")

    def fake_guess_type(name):
        return "image/png", None

    monkeypatch.setattr(
        "markitdown.converters._llm_caption.mimetypes.guess_type",
        fake_guess_type,
    )

    result = llm_caption(
        stream,
        stream_info,
        client=client,
        model="test-model",
        prompt="prompt",
    )

    assert result == "Hello it's Lucian"
    url = client.chat.completions.last_messages[0]["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")


def test_llm_caption_falls_back_to_octet_stream(monkeypatch, client):
    stream = io.BytesIO(b"x")
    stream_info = StreamInfo(mimetype=None, extension=".bin")
    def fake_guess_type(name):
        return None, None
    monkeypatch.setattr(
        "markitdown.converters._llm_caption.mimetypes.guess_type",
        fake_guess_type,
    )

    result = llm_caption(
        stream,
        stream_info,
        client=client,
        model="test-model",
        prompt="prompt",
    )

    assert result == "Hello it's Lucian"
    url = client.chat.completions.last_messages[0]["content"][1]["image_url"]["url"]
    assert url.startswith("data:application/octet-stream;base64,")


class FailingStream:
    def __init__(self):
        self.pos = 5
        self.seek_pos = None

    def tell(self):
        return self.pos

    def read(self):
        raise IOError("boom")

    def seek(self, pos):
        self.seek_pos = pos
        self.pos = pos


def test_llm_caption_returns_none_when_read_fails():
    stream = FailingStream()
    stream_info = StreamInfo(mimetype="image/jpeg", extension=".jpg")
    result = llm_caption(
        stream,
        stream_info,
        client=None,
        model="test-model",
        prompt="prompt",
    )

    assert result is None
    assert stream.seek_pos == 5