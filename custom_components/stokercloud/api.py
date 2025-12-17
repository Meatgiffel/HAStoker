from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_BASE,
    CONTROLLER_DATA_PATH,
    DEFAULT_SCREEN,
    EVENT_DATA_PATH,
    TRANSLATION_BASE,
)

_LOGGER = logging.getLogger(__name__)


class StokerCloudError(Exception):
    """Base error for StokerCloud."""


class StokerCloudAuthError(StokerCloudError):
    """Raised when authentication/token fails."""


@dataclass(frozen=True, slots=True)
class LoginResult:
    token: str
    credentials: str | None = None
    master: int | None = None


class StokerCloudClient:
    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def login(self, username: str) -> LoginResult:
        params = {"user": username}
        url = f"{API_BASE}/{LOGIN_PATH}"
        data = await self._request_json("post", url, params=params)

        if data.get("status") != 0 or "token" not in data:
            raise StokerCloudAuthError(data.get("message", "Login failed"))

        return LoginResult(
            token=str(data["token"]),
            credentials=data.get("credentials"),
            master=data.get("master"),
        )

    async def fetch_controller_data(self, token: str) -> dict[str, Any]:
        url = f"{API_BASE}/{CONTROLLER_DATA_PATH}"
        params = {"screen": DEFAULT_SCREEN, "token": token}
        payload = await self._request_json("get", url, params=params)

        if not isinstance(payload, dict):
            raise StokerCloudError("Unexpected controller data payload")

        if payload.get("status") in (401, 403, "401", "403"):
            raise StokerCloudAuthError("Token rejected")

        if "miscdata" not in payload:
            raise StokerCloudError("Unexpected controller data payload")

        return payload

    async def fetch_event_data(
        self, token: str, *, count: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        url = f"{API_BASE}/{EVENT_DATA_PATH}"
        params = {"count": count, "offset": offset, "token": token}
        payload = await self._request_json("get", url, params=params)
        return {"raw": payload, "events": self._extract_events(payload)}

    async def fetch_translations(self, language: str) -> dict[str, str]:
        url = f"{TRANSLATION_BASE}/{language}.json"
        payload = await self._request_json("get", url, params={})
        if not isinstance(payload, dict):
            raise StokerCloudError("Unexpected translation payload")
        return {
            str(key): str(value)
            for key, value in payload.items()
            if isinstance(key, str) and isinstance(value, str)
        }

    @staticmethod
    def _extract_events(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if isinstance(payload, dict):
            for key in ("events", "eventdata", "data", "items", "rows", "log"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]

            for value in payload.values():
                if isinstance(value, list) and any(
                    isinstance(item, dict) for item in value
                ):
                    return [item for item in value if isinstance(item, dict)]

        return []

    async def _request_json(
        self, method: str, url: str, params: dict[str, Any]
    ) -> Any:
        try:
            async with self._session.request(method, url, params=params) as resp:
                # StokerCloud doesn't consistently use HTTP status codes for errors.
                payload = await resp.json(content_type=None)
        except ClientError as err:
            raise StokerCloudError(str(err)) from err
        except ValueError as err:
            raise StokerCloudError("Invalid JSON response") from err

        if not isinstance(payload, (dict, list)):
            raise StokerCloudError("Unexpected response type")

        if isinstance(payload, dict):
            status = payload.get("status")
            if status not in (None, 0, "0"):
                message = payload.get("message", "Request failed")
                message_text = str(message)

                if status in (401, 403, "401", "403"):
                    raise StokerCloudAuthError(message_text)

                lowered = message_text.lower()
                if "token" in lowered and any(
                    hint in lowered for hint in ("expired", "invalid", "reject")
                ):
                    raise StokerCloudAuthError(message_text)

                raise StokerCloudError(message_text)

        return payload
