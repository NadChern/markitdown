import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import io
from pathlib import Path
import pytest

from markitdown import MarkItDown
from markitdown.converters import _exiftool


def make_jpeg(tmp: Path) -> Path:
    p = tmp / "dummy.jpg"
    p.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 16)
    return p


@pytest.fixture(autouse=True)
def unset_env(monkeypatch):
    monkeypatch.delenv("EXIFTOOL_PATH", raising=False)


def mock_run(monkeypatch):
    calls = []

    def run(cmd, *args, **kwargs):
        calls.append((cmd, kwargs))
        if "-ver" in cmd:
            class R:
                stdout = "12.50"
            return R()
        class R:
            stdout = b'[{"foo":"bar"}]'
        return R()

    monkeypatch.setattr("markitdown.converters._exiftool.subprocess.run", run, raising=True)
    return calls


def test_explicit_exiftool_path(monkeypatch, tmp_path):
    calls = mock_run(monkeypatch)
    img = make_jpeg(tmp_path)

    md = MarkItDown(exiftool_path="/my/exiftool")
    md.convert(str(img))

    assert calls
    used = {cmd[0] for cmd, _ in calls}
    assert used == {"/my/exiftool"}


def test_env_exiftool_path(monkeypatch, tmp_path):
    calls = mock_run(monkeypatch)
    img = make_jpeg(tmp_path)

    monkeypatch.setenv("EXIFTOOL_PATH", "/env/exiftool")

    m = MarkItDown()
    m.convert(str(img))

    used = {cmd[0] for cmd, _ in calls}
    assert used == {"/env/exiftool"}


def test_fallback_to_which(monkeypatch, tmp_path):
    calls = mock_run(monkeypatch)
    img = make_jpeg(tmp_path)

    def which(name):
        if name == "exiftool":
            return "/usr/bin/exiftool"
        return None

    monkeypatch.setattr("markitdown._markitdown.shutil.which", which, raising=True)

    MarkItDown().convert(str(img))

    used = {cmd[0] for cmd, _ in calls}
    assert used == {"/usr/bin/exiftool"}


def test_stream_position_and_metadata(monkeypatch):
    calls = mock_run(monkeypatch)

    b = io.BytesIO(b"abcdef")
    b.read(2)
    start = b.tell()

    out = _exiftool.exiftool_metadata(b, exiftool_path="/some/exiftool")
    assert out == {"foo": "bar"}
    assert b.tell() == start

    json_call = None
    for cmd, kwargs in calls:
        if "-json" in cmd:
            json_call = kwargs
            break

    assert json_call is not None
    assert json_call["input"] == b"cdef"


def test_exiftool_raises_on_vulnerable_version(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        class R:
            stdout = "12.10"
        return R()

    monkeypatch.setattr(
        "markitdown.converters._exiftool.subprocess.run",
        fake_run,
        raising=True,
    )

    stream = io.BytesIO(b"dummy")
    with pytest.raises(RuntimeError) as excinfo:
        _exiftool.exiftool_metadata(stream, exiftool_path="/usr/bin/exiftool")

    msg = str(excinfo.value)
    assert "vulnerable to CVE-2021-22204" in msg
    assert "12.10" in msg


def test_exiftool_raises_when_version_check_fails(monkeypatch):
    def fake_run(cmd, *args, **kwargs):
        class R:
            stdout = "not-a-version"
        return R()

    monkeypatch.setattr(
        "markitdown.converters._exiftool.subprocess.run",
        fake_run,
        raising=True,
    )

    stream = io.BytesIO(b"dummy")
    with pytest.raises(RuntimeError) as excinfo:
        _exiftool.exiftool_metadata(stream, exiftool_path="/usr/bin/exiftool")

    assert "Failed to verify ExifTool version." in str(excinfo.value)