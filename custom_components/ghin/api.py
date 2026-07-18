"""GHIN API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import GHIN_SOURCE, LOGIN_URL, SCORES_URL

_LOGGER = logging.getLogger(__name__)


class GhinApiError(Exception):
    """Raised when a GHIN API call fails."""


class GhinAuthError(GhinApiError):
    """Raised when login fails (bad credentials or expired session)."""


class GhinClient:
    """Thin async client for the unofficial GHIN API."""

    def __init__(
        self,
        email: str,
        password: str,
        client_token: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._email = email
        self._password = password
        self._client_token = client_token
        self._session = session
        self._token: str | None = None
        self._golfer: dict[str, Any] | None = None

    @property
    def ghin_number(self) -> str | None:
        return self._golfer["ghin_number"] if self._golfer else None

    @property
    def handicap_index(self) -> float | None:
        if not self._golfer or self._golfer.get("display") in (None, "-"):
            return None
        try:
            return float(self._golfer["display"])
        except (TypeError, ValueError):
            return None

    @property
    def low_hi_display(self) -> str | None:
        return self._golfer.get("low_hi_display") if self._golfer else None

    @property
    def club_name(self) -> str | None:
        return self._golfer.get("club_name") if self._golfer else None

    @property
    def revision_date(self) -> str | None:
        return self._golfer.get("rev_date") if self._golfer else None

    async def async_login(self) -> dict[str, Any]:
        """Log in and cache the session token + golfer profile."""
        payload = {
            "source": GHIN_SOURCE,
            "token": self._client_token,
            "user": {
                "email_or_ghin": self._email,
                "password": self._password,
                "remember_me": False,
            },
        }
        try:
            async with self._session.post(LOGIN_URL, json=payload) as resp:
                if resp.status == 401 or resp.status == 403:
                    raise GhinAuthError(
                        f"GHIN login rejected credentials or client token "
                        f"(status {resp.status})"
                    )
                if resp.status != 200:
                    text = await resp.text()
                    raise GhinApiError(
                        f"GHIN login failed with status {resp.status}: {text[:200]}"
                    )
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise GhinApiError(f"Network error contacting GHIN: {err}") from err

        try:
            golfer_user = data["golfer_user"]
            self._token = golfer_user["golfer_user_token"]
            self._golfer = golfer_user["golfers"][0]
        except (KeyError, IndexError) as err:
            raise GhinApiError(
                f"Unexpected GHIN login response shape: {err}"
            ) from err

        return self._golfer

    async def async_get_scores_payload(self, limit: int = 1) -> dict[str, Any]:
        """Fetch recent scores plus summary stats. Requires a prior login.

        Confirmed response shape:
        {"scores": [...], "total_count": int, "highest_score": int,
         "lowest_score": int, "average": float}
        """
        if not self._token or not self.ghin_number:
            await self.async_login()

        params = {
            "golfer_id": self.ghin_number,
            "offset": 1,
            "limit": limit,
            "source": GHIN_SOURCE,
        }
        headers = {"Authorization": f"Bearer {self._token}"}

        try:
            async with self._session.get(
                SCORES_URL, params=params, headers=headers
            ) as resp:
                if resp.status in (401, 403):
                    # Token likely expired (they're short-lived JWTs) - retry once.
                    await self.async_login()
                    headers = {"Authorization": f"Bearer {self._token}"}
                    async with self._session.get(
                        SCORES_URL, params=params, headers=headers
                    ) as retry_resp:
                        retry_resp.raise_for_status()
                        return await retry_resp.json()
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientError as err:
            raise GhinApiError(f"Network error fetching GHIN scores: {err}") from err

    async def async_update(self) -> dict[str, Any]:
        """Full refresh: re-login (cheap) and fetch latest score + stats."""
        await self.async_login()
        payload = await self.async_get_scores_payload(limit=1)
        scores = payload.get("scores") or []

        return {
            "handicap_index": self.handicap_index,
            "low_hi_display": self.low_hi_display,
            "club_name": self.club_name,
            "rev_date": self.revision_date,
            "ghin_number": self.ghin_number,
            "last_score": scores[0] if scores else None,
            "total_count": payload.get("total_count"),
            "highest_score": payload.get("highest_score"),
            "lowest_score": payload.get("lowest_score"),
            "average": payload.get("average"),
        }
