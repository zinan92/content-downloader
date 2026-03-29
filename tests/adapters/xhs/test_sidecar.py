"""Unit tests for XHSSidecar health check and startup guidance."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from content_downloader.adapters.xhs.sidecar import XHSSidecar


@pytest.mark.asyncio
async def test_check_health_returns_true_when_available():
    """check_health returns True when the sidecar is reachable."""
    sidecar = XHSSidecar()
    with patch(
        "content_downloader.adapters.xhs.sidecar.XHSAPIClient"
    ) as MockClient:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.is_available = AsyncMock(return_value=True)
        MockClient.return_value = mock_instance

        result = await sidecar.check_health()

    assert result is True


@pytest.mark.asyncio
async def test_check_health_returns_false_when_not_available():
    """check_health returns False when the sidecar is not reachable."""
    sidecar = XHSSidecar()
    with patch(
        "content_downloader.adapters.xhs.sidecar.XHSAPIClient"
    ) as MockClient:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.is_available = AsyncMock(return_value=False)
        MockClient.return_value = mock_instance

        result = await sidecar.check_health()

    assert result is False


def test_get_start_instructions_contains_key_info():
    """get_start_instructions returns guidance mentioning the API port."""
    sidecar = XHSSidecar()
    instructions = sidecar.get_start_instructions()

    assert "5556" in instructions
    assert "main.py" in instructions
    assert "api" in instructions


def test_get_start_instructions_is_human_readable():
    """get_start_instructions is a non-empty string with multiple lines."""
    sidecar = XHSSidecar()
    instructions = sidecar.get_start_instructions()
    assert isinstance(instructions, str)
    assert len(instructions) > 20
    assert "\n" in instructions  # multiline


def test_custom_base_url_passed_to_client():
    """XHSSidecar forwards custom base_url to XHSAPIClient."""
    sidecar = XHSSidecar(base_url="http://127.0.0.1:9999")
    with patch(
        "content_downloader.adapters.xhs.sidecar.XHSAPIClient"
    ) as MockClient:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.is_available = AsyncMock(return_value=True)
        MockClient.return_value = mock_instance

        import asyncio
        asyncio.run(sidecar.check_health())

    MockClient.assert_called_once_with(base_url="http://127.0.0.1:9999")
