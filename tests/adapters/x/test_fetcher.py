"""Tests for XFetcher — mocks asyncio subprocess."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from content_downloader.adapters.x.fetcher import XFetcher, _find_info_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_proc(returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> AsyncMock:
    """Create an AsyncMock simulating asyncio.subprocess.Process."""
    proc = AsyncMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    proc.wait = AsyncMock(return_value=returncode)
    return proc


# ---------------------------------------------------------------------------
# _find_info_json
# ---------------------------------------------------------------------------


def test_find_info_json_returns_file(tmp_path: Path) -> None:
    info_file = tmp_path / "1234567890.info.json"
    info_file.write_text("{}")
    result = _find_info_json(tmp_path)
    assert result == info_file


def test_find_info_json_returns_none_when_missing(tmp_path: Path) -> None:
    result = _find_info_json(tmp_path)
    assert result is None


def test_find_info_json_ignores_non_info_json_files(tmp_path: Path) -> None:
    (tmp_path / "video.mp4").write_bytes(b"fake")
    (tmp_path / "thumb.jpg").write_bytes(b"fake")
    result = _find_info_json(tmp_path)
    assert result is None


# ---------------------------------------------------------------------------
# XFetcher.is_available
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_available_returns_true_when_yt_dlp_exits_zero() -> None:
    mock_proc = _make_mock_proc(returncode=0, stdout=b"2024.01.01")
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        fetcher = XFetcher()
        result = await fetcher.is_available()
    assert result is True
    call_args = mock_exec.call_args[0]
    assert call_args[0] == "yt-dlp"
    assert "--version" in call_args


@pytest.mark.asyncio
async def test_is_available_returns_false_when_yt_dlp_not_found() -> None:
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError()):
        fetcher = XFetcher()
        result = await fetcher.is_available()
    assert result is False


@pytest.mark.asyncio
async def test_is_available_returns_false_when_yt_dlp_exits_nonzero() -> None:
    mock_proc = _make_mock_proc(returncode=1)
    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        fetcher = XFetcher()
        result = await fetcher.is_available()
    assert result is False


# ---------------------------------------------------------------------------
# XFetcher.fetch_post
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_post_returns_parsed_info_json(tmp_path: Path) -> None:
    sample_info = {"id": "123", "title": "Test tweet", "uploader": "user"}
    url = "https://x.com/user/status/123"

    mock_proc = _make_mock_proc(returncode=0, stdout=b"[download] Done")

    def fake_subprocess_exec(*args, **kwargs):
        # Write the .info.json file to simulate yt-dlp output
        media_dir = tmp_path / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        (media_dir / "123.info.json").write_text(json.dumps(sample_info))
        return mock_proc

    with patch("asyncio.create_subprocess_exec", side_effect=fake_subprocess_exec):
        fetcher = XFetcher()
        result = await fetcher.fetch_post(url, tmp_path)

    assert result["id"] == "123"
    assert result["title"] == "Test tweet"


@pytest.mark.asyncio
async def test_fetch_post_raises_runtime_error_on_nonzero_exit(tmp_path: Path) -> None:
    mock_proc = _make_mock_proc(returncode=1, stderr=b"ERROR: Unsupported URL")

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        fetcher = XFetcher()
        with pytest.raises(RuntimeError, match="yt-dlp exited with code 1"):
            await fetcher.fetch_post("https://x.com/user/status/123", tmp_path)


@pytest.mark.asyncio
async def test_fetch_post_raises_file_not_found_when_no_info_json(tmp_path: Path) -> None:
    mock_proc = _make_mock_proc(returncode=0)

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        fetcher = XFetcher()
        with pytest.raises(FileNotFoundError, match="no .info.json"):
            await fetcher.fetch_post("https://x.com/user/status/123", tmp_path)


@pytest.mark.asyncio
async def test_fetch_post_uses_exec_not_shell(tmp_path: Path) -> None:
    """Verify create_subprocess_exec is called with positional args (not shell)."""
    sample_info = {"id": "abc", "title": ""}
    mock_proc = _make_mock_proc(returncode=0)

    captured_args = []

    def fake_subprocess_exec(*args, **kwargs):
        captured_args.extend(args)
        media_dir = tmp_path / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        (media_dir / "abc.info.json").write_text(json.dumps(sample_info))
        return mock_proc

    url = "https://x.com/user/status/abc"
    with patch("asyncio.create_subprocess_exec", side_effect=fake_subprocess_exec):
        fetcher = XFetcher()
        await fetcher.fetch_post(url, tmp_path)

    # URL should be a separate argument, not embedded in a shell string
    assert captured_args[0] == "yt-dlp"
    assert url in captured_args
    # shell=True should not be in kwargs
    assert "--write-info-json" in captured_args
