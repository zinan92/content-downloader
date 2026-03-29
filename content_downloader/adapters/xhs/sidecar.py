"""XHS-Downloader sidecar health check and startup guidance."""

from __future__ import annotations

import logging

from content_downloader.adapters.xhs.api_client import XHSAPIClient

logger = logging.getLogger(__name__)

_START_INSTRUCTIONS = (
    "XHS-Downloader is not running.\n"
    "Start it with:\n"
    "  cd /path/to/XHS-Downloader\n"
    "  python main.py api\n"
    "It will start on http://127.0.0.1:5556"
)


class XHSSidecar:
    """Helper for checking whether the XHS-Downloader sidecar is available.

    Usage::

        sidecar = XHSSidecar()
        if not await sidecar.check_health():
            print(sidecar.get_start_instructions())
    """

    def __init__(self, base_url: str = "http://127.0.0.1:5556") -> None:
        self._base_url = base_url

    async def check_health(self) -> bool:
        """Return ``True`` if the XHS-Downloader sidecar is reachable."""
        async with XHSAPIClient(base_url=self._base_url) as client:
            available = await client.is_available()
        logger.debug("XHS sidecar health check: %s", "OK" if available else "unavailable")
        return available

    def get_start_instructions(self) -> str:
        """Return a human-readable guide for starting XHS-Downloader."""
        return _START_INSTRUCTIONS
