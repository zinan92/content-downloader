"""Douyin API client — migrated from douyin-downloader-1/core/api_client.py.

Key changes from original:
- httpx replaces aiohttp for HTTP calls (consistent with project deps)
- Removed browser fallback methods (Playwright not required)
- Removed get_user_like/music/mix/collects (Phase 2: post mode only)
- Error handling maps to DownloadError conventions
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx

from content_downloader.adapters.douyin.cookie_manager import _sanitize_cookies
from content_downloader.adapters.douyin.ms_token import MsTokenManager
from content_downloader.adapters.douyin.xbogus import XBogus

try:
    from content_downloader.adapters.douyin.abogus import ABogus, BrowserFingerprintGenerator
except Exception:  # pragma: no cover
    ABogus = None  # type: ignore[assignment,misc]
    BrowserFingerprintGenerator = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_USER_AGENT_POOL = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) "
        "Gecko/20100101 Firefox/133.0"
    ),
]


class DouyinAPIClient:
    """Async Douyin web API client with XBogus/ABogus request signing."""

    BASE_URL = "https://www.douyin.com"

    def __init__(
        self,
        cookies: Optional[Dict[str, str]] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self.cookies = _sanitize_cookies(cookies or {})
        self.proxy = str(proxy or "").strip() or None
        self._client: Optional[httpx.AsyncClient] = None
        selected_ua = random.choice(_USER_AGENT_POOL)
        self.headers = {
            "User-Agent": selected_ua,
            "Referer": "https://www.douyin.com/",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
        }
        self._signer = XBogus(self.headers["User-Agent"])
        self._ms_token_manager = MsTokenManager(user_agent=self.headers["User-Agent"])
        self._ms_token = (self.cookies.get("msToken") or "").strip()
        self._abogus_enabled = (
            ABogus is not None and BrowserFingerprintGenerator is not None
        )

    async def __aenter__(self) -> "DouyinAPIClient":
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _ensure_client(self) -> None:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                cookies=self.cookies,
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                proxy=self.proxy,
            )

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _ensure_ms_token(self) -> str:
        if self._ms_token:
            return self._ms_token

        token = await asyncio.to_thread(
            self._ms_token_manager.ensure_ms_token,
            self.cookies,
        )
        self._ms_token = token.strip()
        if self._ms_token:
            self.cookies["msToken"] = self._ms_token
        return self._ms_token

    async def _default_query(self) -> Dict[str, Any]:
        ms_token = await self._ensure_ms_token()
        return {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "pc_client_type": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "123.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "123.0.0.0",
            "os_name": "Windows",
            "os_version": "10",
            "cpu_core_num": "8",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "50",
            "msToken": ms_token,
        }

    def sign_url(self, url: str) -> Tuple[str, str]:
        """Sign URL with XBogus. Returns (signed_url, user_agent)."""
        signed_url, _xbogus, ua = self._signer.build(url)
        return signed_url, ua

    def build_signed_path(self, path: str, params: Dict[str, Any]) -> Tuple[str, str]:
        """Build a signed URL for the given API path and params."""
        query = urlencode(params)
        base_url = f"{self.BASE_URL}{path}"
        ab_signed = self._build_abogus_url(base_url, query)
        if ab_signed:
            return ab_signed
        return self.sign_url(f"{base_url}?{query}")

    def _build_abogus_url(
        self, base_url: str, query: str
    ) -> Optional[Tuple[str, str]]:
        if not self._abogus_enabled:
            return None
        try:
            browser_fp = BrowserFingerprintGenerator.generate_fingerprint("Edge")
            signer = ABogus(fp=browser_fp, user_agent=self.headers["User-Agent"])
            params_with_ab, _ab, ua, _body = signer.generate_abogus(query, "")
            return f"{base_url}?{params_with_ab}", ua
        except Exception as exc:
            logger.warning("Failed to generate a_bogus, fallback to X-Bogus: %s", exc)
            return None

    async def _request_json(
        self,
        path: str,
        params: Dict[str, Any],
        *,
        suppress_error: bool = False,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        await self._ensure_client()
        delays = [1, 2, 5]
        last_exc: Optional[Exception] = None

        for attempt in range(max_retries):
            signed_url, ua = self.build_signed_path(path, params)
            try:
                assert self._client is not None
                response = await self._client.get(
                    signed_url,
                    headers={**self.headers, "User-Agent": ua},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data if isinstance(data, dict) else {}
                if response.status_code < 500 and response.status_code != 429:
                    log_fn = logger.debug if suppress_error else logger.error
                    log_fn(
                        "Request failed: path=%s, status=%s",
                        path,
                        response.status_code,
                    )
                    return {}
                last_exc = RuntimeError(
                    f"HTTP {response.status_code} for {path}"
                )
            except Exception as exc:
                last_exc = exc

            if attempt < max_retries - 1:
                delay = delays[min(attempt, len(delays) - 1)]
                logger.debug(
                    "Request retry %d/%d for %s in %ds",
                    attempt + 1, max_retries, path, delay,
                )
                await asyncio.sleep(delay)

        log_fn = logger.debug if suppress_error else logger.error
        log_fn(
            "Request failed after %d attempts: path=%s, error=%s",
            max_retries, path, last_exc,
        )
        return {}

    @staticmethod
    def _normalize_paged_response(
        raw_data: Any,
        *,
        item_keys: Optional[List[str]] = None,
        source: str = "api",
    ) -> Dict[str, Any]:
        raw = raw_data if isinstance(raw_data, dict) else {}
        keys = item_keys or []
        keys = ["items", *keys, "aweme_list", "mix_list", "music_list"]

        items: List[Dict[str, Any]] = []
        for key in keys:
            value = raw.get(key)
            if isinstance(value, list):
                items = value
                break

        has_more_value = raw.get("has_more", False)
        try:
            has_more = bool(int(has_more_value))
        except (TypeError, ValueError):
            has_more = bool(has_more_value)

        max_cursor_value = raw.get("max_cursor")
        if max_cursor_value is None:
            max_cursor_value = raw.get("cursor", 0)
        try:
            max_cursor = int(max_cursor_value or 0)
        except (TypeError, ValueError):
            max_cursor = 0

        status_code_value = raw.get("status_code", 0)
        try:
            status_code = int(status_code_value or 0)
        except (TypeError, ValueError):
            status_code = 0

        risk_flags = {
            "login_tip": bool(
                ((raw.get("not_login_module") or {}).get("guide_login_tip_exist"))
                if isinstance(raw.get("not_login_module"), dict)
                else False
            ),
            "verify_page": bool(raw.get("verify_ticket")),
        }

        normalized = {
            "items": items,
            "aweme_list": items,
            "has_more": has_more,
            "max_cursor": max_cursor,
            "status_code": status_code,
            "source": source,
            "risk_flags": risk_flags,
            "raw": raw,
        }
        for key, value in raw.items():
            if key not in normalized:
                normalized[key] = value
        return normalized

    async def _build_user_page_params(
        self, sec_uid: str, max_cursor: int, count: int
    ) -> Dict[str, Any]:
        params = await self._default_query()
        params.update(
            {
                "sec_user_id": sec_uid,
                "max_cursor": max_cursor,
                "count": count,
                "locate_query": "false",
            }
        )
        return params

    async def get_video_detail(
        self, aweme_id: str, *, suppress_error: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Fetch metadata for a single video by aweme_id."""
        params = await self._default_query()
        params.update(
            {
                "aweme_id": aweme_id,
                "aid": "1128",
            }
        )
        data = await self._request_json(
            "/aweme/v1/web/aweme/detail/",
            params,
            suppress_error=suppress_error,
        )
        if data:
            return data.get("aweme_detail")
        return None

    async def get_user_post(
        self, sec_uid: str, max_cursor: int = 0, count: int = 20
    ) -> Dict[str, Any]:
        """Fetch paginated list of a user's posts."""
        params = await self._build_user_page_params(sec_uid, max_cursor, count)
        params.update(
            {
                "show_live_replay_strategy": "1",
                "need_time_list": "1",
                "time_list_query": "0",
                "whale_cut_token": "",
                "cut_version": "1",
                "publish_video_strategy_type": "2",
            }
        )
        raw = await self._request_json("/aweme/v1/web/aweme/post/", params)
        return self._normalize_paged_response(raw, item_keys=["aweme_list"])

    async def resolve_short_url(self, short_url: str) -> Optional[str]:
        """Resolve a v.douyin.com short URL to its canonical long URL."""
        try:
            await self._ensure_client()
            assert self._client is not None
            response = await self._client.get(
                short_url,
                follow_redirects=True,
            )
            return str(response.url)
        except Exception as exc:
            logger.error("Failed to resolve short URL: %s, error: %s", short_url, exc)
            return None
