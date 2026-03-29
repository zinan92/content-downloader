"""Unit tests for XHS note → ContentItem mapper."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from content_downloader.adapters.xhs.mapper import note_to_content_item, _parse_xhs_time

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# _parse_xhs_time
# ---------------------------------------------------------------------------


def test_parse_xhs_time_milliseconds():
    """_parse_xhs_time converts a millisecond epoch to ISO 8601."""
    ts_ms = 1710000000000  # 2024-03-09T16:00:00Z
    result = _parse_xhs_time(ts_ms)
    assert result.startswith("2024-03-09")
    assert "T" in result


def test_parse_xhs_time_string_input():
    """_parse_xhs_time accepts string-encoded timestamps."""
    result = _parse_xhs_time("1710000000000")
    assert "2024-03-09" in result


def test_parse_xhs_time_none_returns_now():
    """_parse_xhs_time returns a valid ISO timestamp for None input."""
    result = _parse_xhs_time(None)
    assert "T" in result
    # Should be parseable
    datetime.fromisoformat(result.replace("Z", "+00:00"))


def test_parse_xhs_time_invalid_returns_now():
    """_parse_xhs_time returns a valid ISO timestamp for invalid input."""
    result = _parse_xhs_time("not-a-timestamp")
    assert "T" in result


# ---------------------------------------------------------------------------
# note_to_content_item — gallery note
# ---------------------------------------------------------------------------


def test_gallery_note_basic_fields():
    """note_to_content_item maps gallery note fields correctly."""
    fixture = _load_fixture("note_gallery.json")
    item = note_to_content_item(fixture, source_url="https://www.xiaohongshu.com/explore/abc123gallery")

    assert item.platform == "xhs"
    assert item.content_id == "abc123gallery"
    assert item.content_type == "gallery"
    assert item.title == "Beautiful Sunset Photos"
    assert "Bund" in item.description
    assert item.author_id == "user456"
    assert item.author_name == "SunsetPhotographer"
    assert item.source_url == "https://www.xiaohongshu.com/explore/abc123gallery"
    assert item.metadata_file == "metadata.json"


def test_gallery_note_engagement_fields():
    """note_to_content_item maps engagement counters for gallery note."""
    fixture = _load_fixture("note_gallery.json")
    item = note_to_content_item(fixture, source_url="https://www.xiaohongshu.com/explore/abc123gallery")

    assert item.likes == 1024
    assert item.comments == 88
    assert item.shares == 256
    assert item.collects == 512
    assert item.views == 0  # XHS does not expose view counts


def test_gallery_note_publish_time():
    """note_to_content_item parses the millisecond timestamp correctly."""
    fixture = _load_fixture("note_gallery.json")
    item = note_to_content_item(fixture, source_url="https://www.xiaohongshu.com/explore/abc123gallery")

    # timestamp 1710000000000 ms = 2024-03-09
    assert "2024-03-09" in item.publish_time


def test_gallery_note_media_files():
    """note_to_content_item stores provided media_files list."""
    fixture = _load_fixture("note_gallery.json")
    media = ["media/img_01.jpg", "media/img_02.jpg", "media/img_03.jpg"]
    item = note_to_content_item(fixture, source_url="...", media_files=media, cover_file="media/cover.jpg")

    assert item.media_files == media
    assert item.cover_file == "media/cover.jpg"


def test_gallery_note_no_media_files_defaults_to_empty():
    """note_to_content_item defaults media_files to [] when not provided."""
    fixture = _load_fixture("note_gallery.json")
    item = note_to_content_item(fixture, source_url="...")

    assert item.media_files == []
    assert item.cover_file is None


# ---------------------------------------------------------------------------
# note_to_content_item — video note
# ---------------------------------------------------------------------------


def test_video_note_content_type():
    """note_to_content_item sets content_type='video' for type='video'."""
    fixture = _load_fixture("note_video.json")
    item = note_to_content_item(fixture, source_url="https://www.xiaohongshu.com/explore/xyz789video")

    assert item.content_type == "video"
    assert item.content_id == "xyz789video"
    assert item.author_name == "FitnessGuru"


def test_video_note_engagement_fields():
    """note_to_content_item maps engagement counters for video note."""
    fixture = _load_fixture("note_video.json")
    item = note_to_content_item(fixture, source_url="...")

    assert item.likes == 5000
    assert item.comments == 320
    assert item.shares == 1100
    assert item.collects == 2400


def test_video_note_media_files():
    """note_to_content_item stores video media files."""
    fixture = _load_fixture("note_video.json")
    item = note_to_content_item(
        fixture,
        source_url="...",
        media_files=["media/video.mp4"],
        cover_file="media/cover.jpg",
    )

    assert "media/video.mp4" in item.media_files
    assert item.cover_file == "media/cover.jpg"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_missing_note_id_falls_back_to_id_field():
    """note_to_content_item uses 'id' field when 'note_id' is absent."""
    data = {"id": "fallback_id", "type": "normal", "time": 1710000000000}
    item = note_to_content_item(data, source_url="https://example.com")
    assert item.content_id == "fallback_id"


def test_missing_all_id_fields_uses_empty_string():
    """note_to_content_item returns empty string content_id when no id present."""
    data = {"type": "normal", "time": 1710000000000}
    item = note_to_content_item(data, source_url="https://example.com")
    assert item.content_id == ""


def test_missing_engagement_defaults_to_zero():
    """note_to_content_item uses 0 for missing engagement fields."""
    data = {"note_id": "test", "type": "normal", "time": 1710000000000}
    item = note_to_content_item(data, source_url="https://example.com")
    assert item.likes == 0
    assert item.comments == 0
    assert item.shares == 0
    assert item.collects == 0


def test_source_url_fallback_when_no_note_url():
    """note_to_content_item uses source_url when note_url is absent."""
    data = {"note_id": "test", "type": "normal", "time": 1710000000000}
    item = note_to_content_item(data, source_url="https://fallback.com/test")
    assert item.source_url == "https://fallback.com/test"


def test_note_url_overrides_source_url():
    """note_to_content_item prefers note_url over the passed source_url."""
    data = {
        "note_id": "test",
        "type": "normal",
        "time": 1710000000000,
        "note_url": "https://www.xiaohongshu.com/explore/test",
    }
    item = note_to_content_item(data, source_url="https://other.com/test")
    assert item.source_url == "https://www.xiaohongshu.com/explore/test"


def test_downloaded_at_is_valid_iso():
    """note_to_content_item sets downloaded_at to a valid ISO timestamp."""
    data = {"note_id": "test", "type": "normal", "time": 1710000000000}
    item = note_to_content_item(data, source_url="https://example.com")
    # Should be parseable
    datetime.fromisoformat(item.downloaded_at.replace("Z", "+00:00"))
