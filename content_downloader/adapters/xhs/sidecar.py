"""XHS-Downloader sidecar — auto-install, auto-start, health check."""

from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

from content_downloader.adapters.xhs.api_client import XHSAPIClient

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 5556
_STARTUP_TIMEOUT = 15  # seconds to wait for sidecar to become healthy
_HEALTH_POLL_INTERVAL = 1.0


class XHSSidecar:
    """Manages the XHS-Downloader sidecar process lifecycle.

    Automatically installs (pip) and starts XHS-Downloader if not running.
    """

    def __init__(self, base_url: str = f"http://127.0.0.1:{_DEFAULT_PORT}") -> None:
        self._base_url = base_url
        self._process: subprocess.Popen | None = None

    async def ensure_running(self) -> bool:
        """Ensure XHS-Downloader is running. Auto-start if needed.

        Returns True if sidecar is healthy.
        """
        # 1. Already running?
        if await self._check_health():
            logger.debug("XHS sidecar already running at %s", self._base_url)
            return True

        # 2. Is xhs-downloader installed?
        if not self._is_installed():
            logger.info("XHS-Downloader not found, installing via pip...")
            self._install()

        # 3. Start sidecar
        logger.info("Starting XHS-Downloader sidecar...")
        self._start()

        # 4. Wait for healthy
        return await self._wait_for_healthy()

    async def _check_health(self) -> bool:
        try:
            async with XHSAPIClient(base_url=self._base_url) as client:
                return await client.is_available()
        except Exception:
            return False

    def _is_installed(self) -> bool:
        """Check if XHS-Downloader CLI is available."""
        # Try importing the package
        try:
            result = subprocess.run(
                [sys.executable, "-c", "import source; print('ok')"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

        # Check if xhs-downloader command exists
        return shutil.which("xhs-downloader") is not None

    def _install(self) -> None:
        """Install XHS-Downloader via pip."""
        logger.info("Running: pip install xhs-downloader")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "xhs-downloader", "-q"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            logger.warning("pip install failed: %s", result.stderr)
            # Try cloning from GitHub as fallback
            self._install_from_github()

    def _install_from_github(self) -> None:
        """Clone and install XHS-Downloader from GitHub."""
        install_dir = Path.home() / ".content-downloader" / "XHS-Downloader"
        if not install_dir.exists():
            logger.info("Cloning XHS-Downloader from GitHub...")
            subprocess.run(
                ["git", "clone", "--depth", "1",
                 "https://github.com/JoeanAmier/XHS-Downloader.git",
                 str(install_dir)],
                capture_output=True, text=True, timeout=120,
            )
        # Install requirements
        req_file = install_dir / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
                capture_output=True, text=True, timeout=120,
            )

    def _start(self) -> None:
        """Start XHS-Downloader in API mode as a background process."""
        # Try 1: installed package
        try:
            self._process = subprocess.Popen(
                [sys.executable, "-m", "xhs_downloader", "api"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return
        except Exception:
            pass

        # Try 2: cloned repo
        repo_dir = Path.home() / ".content-downloader" / "XHS-Downloader"
        main_py = repo_dir / "main.py"
        if main_py.exists():
            self._process = subprocess.Popen(
                [sys.executable, str(main_py), "api"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=str(repo_dir),
            )
            return

        logger.error("Cannot start XHS-Downloader — not found")

    async def _wait_for_healthy(self) -> bool:
        """Poll until sidecar is healthy or timeout."""
        deadline = time.monotonic() + _STARTUP_TIMEOUT
        while time.monotonic() < deadline:
            if await self._check_health():
                logger.info("XHS sidecar is ready at %s", self._base_url)
                return True
            await asyncio.sleep(_HEALTH_POLL_INTERVAL)

        logger.error("XHS sidecar failed to start within %ds", _STARTUP_TIMEOUT)
        return False

    def stop(self) -> None:
        """Stop the sidecar process if we started it."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None
