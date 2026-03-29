"""X (Twitter) content fetcher using yt-dlp as an external CLI tool."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_YTDLP_NOT_INSTALLED_MESSAGE = (
    "yt-dlp is not installed or not found in PATH.\n"
    "Install it with:\n"
    "  pip install yt-dlp\n"
    "or:\n"
    "  brew install yt-dlp"
)


def _find_info_json(directory: Path) -> "Path | None":
    """Return the first .info.json file found in *directory*, or None."""
    matches = list(directory.glob("*.info.json"))
    if not matches:
        return None
    return matches[0]


class XFetcher:
    """Fetch X/Twitter post metadata and media using yt-dlp as a subprocess.

    yt-dlp is invoked via asyncio.create_subprocess_exec (not shell) to
    avoid command-injection vulnerabilities. The URL is passed as a positional
    argument, never interpolated into a shell string.
    """

    async def is_available(self) -> bool:
        """Return True if yt-dlp is installed and accessible."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except (FileNotFoundError, OSError):
            return False

    async def fetch_post(self, url: str, output_dir: Path) -> "dict[str, Any]":
        """Download a tweet's media and return its yt-dlp info dict.

        Runs yt-dlp with --write-info-json --write-thumbnail --no-playlist
        to download media files and a .info.json metadata file.

        Args:
            url: The tweet URL (x.com or twitter.com).
            output_dir: Directory where yt-dlp output files are written.
                        Media files go into output_dir/media/.

        Returns:
            Parsed dict from the .info.json file produced by yt-dlp.

        Raises:
            RuntimeError: If yt-dlp exits with a non-zero return code.
            FileNotFoundError: If no .info.json file is found after yt-dlp
                               completes (text-only tweets produce no info.json).
        """
        media_dir = output_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        output_template = str(media_dir / "%(id)s.%(ext)s")

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--write-info-json",
            "--write-thumbnail",
            "--no-playlist",
            "--no-warnings",
            "-o",
            output_template,
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if stdout:
            logger.debug("yt-dlp stdout: %s", stdout.decode(errors="replace"))
        if stderr:
            logger.debug("yt-dlp stderr: %s", stderr.decode(errors="replace"))

        if proc.returncode != 0:
            stderr_text = stderr.decode(errors="replace") if stderr else ""
            raise RuntimeError(
                f"yt-dlp exited with code {proc.returncode}.\n"
                f"URL: {url!r}\n"
                f"stderr: {stderr_text}"
            )

        info_json_path = _find_info_json(media_dir)
        if info_json_path is None:
            raise FileNotFoundError(
                f"yt-dlp produced no .info.json file in {media_dir}. "
                f"The tweet may be text-only or was unavailable."
            )

        return json.loads(info_json_path.read_text(encoding="utf-8"))
