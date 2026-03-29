"""Maps raw XHS-Downloader API response dicts to ContentItem models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from content_downloader.models import ContentItem


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_xhs_time(raw: Any) -> str:
    """Convert an XHS timestamp (milliseconds epoch int) to ISO 8601 string.

    XHS API returns ``time`` as a millisecond Unix timestamp.  Returns the
    current UTC time as a fallback when the value is missing or invalid.
    """
    if raw is None:
        return _now_iso()
    try:
        ts_ms = int(raw)
        ts_sec = ts_ms / 1000.0
        dt = datetime.fromtimestamp(ts_sec, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except (ValueError, OSError, OverflowError):
        return _now_iso()


def _safe_int(value: Any, default: int = 0) -> int:
    """Convert *value* to int, returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def note_to_content_item(
    note_data: dict[str, Any],
    source_url: str,
    media_files: list[str] | None = None,
    cover_file: str | None = None,
) -> ContentItem:
    """Convert a raw XHS-Downloader note response dict to a ContentItem.

    XHS-Downloader returns a flat dict with fields such as:
    - ``note_id`` / ``id`` — note identifier
    - ``type`` — ``"normal"`` (图文) or ``"video"``
    - ``title`` — note title
    - ``desc`` — note description / caption
    - ``user_id`` / ``author_id`` — author identifier
    - ``nickname`` — author display name
    - ``time`` — publish timestamp in **milliseconds**
    - ``note_url`` — canonical note URL
    - ``liked_count`` / ``comment_count`` / ``share_count`` / ``collected_count``
      — engagement counters

    Args:
        note_data: Raw dict from the XHS-Downloader ``/xhs/detail`` endpoint.
        source_url: Original URL used to request the note (fallback for note_url).
        media_files: Relative paths to downloaded media files.
        cover_file: Relative path to the cover image, or ``None``.

    Returns:
        Populated :class:`~content_downloader.models.ContentItem`.
    """
    note_id = str(note_data.get("note_id") or note_data.get("id") or "")

    # XHS note types: "normal" = image gallery, "video" = video note
    raw_type = note_data.get("type", "normal")
    content_type = "gallery" if raw_type == "normal" else "video"

    # Author fields — XHS uses "user_id" and "nickname"
    author_id = str(note_data.get("user_id") or note_data.get("author_id") or "")
    author_name = str(note_data.get("nickname") or "")

    return ContentItem(
        platform="xhs",
        content_id=note_id,
        content_type=content_type,
        title=str(note_data.get("title") or ""),
        description=str(note_data.get("desc") or ""),
        author_id=author_id,
        author_name=author_name,
        publish_time=_parse_xhs_time(note_data.get("time")),
        source_url=str(note_data.get("note_url") or source_url),
        media_files=media_files or [],
        cover_file=cover_file,
        metadata_file="metadata.json",
        likes=_safe_int(note_data.get("liked_count")),
        comments=_safe_int(note_data.get("comment_count")),
        shares=_safe_int(note_data.get("share_count")),
        collects=_safe_int(note_data.get("collected_count")),
        views=0,  # XHS does not expose view counts
        downloaded_at=_now_iso(),
    )
