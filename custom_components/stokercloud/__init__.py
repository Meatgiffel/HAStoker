from __future__ import annotations

from collections.abc import Awaitable, Callable
import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StokerCloudAuthError, StokerCloudClient, StokerCloudError
from .const import (
    CONF_USERNAME,
    DEFAULT_EVENT_COUNT,
    DEFAULT_EVENT_OFFSET,
    DEFAULT_EVENT_UPDATE_INTERVAL,
    DEFAULT_TRANSLATION_LANGUAGE,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    username: str = entry.data[CONF_USERNAME]
    session = async_get_clientsession(hass)
    client = StokerCloudClient(session)

    token: str | None = None
    token_lock = asyncio.Lock()

    translations: dict[str, str] | None = None
    try:
        translations = await client.fetch_translations(DEFAULT_TRANSLATION_LANGUAGE)
    except StokerCloudError as err:
        _LOGGER.debug("Failed to fetch StokerCloud translations: %s", err)

    def _apply_translations(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not translations:
            return events
        translated: list[dict[str, Any]] = []
        for event in events:
            out = dict(event)
            for key, value in event.items():
                if isinstance(value, str) and value in translations:
                    out[f"{key}_translated"] = translations[value]
            translated.append(out)
        return translated

    async def _fetch_with_auth_retry(
        fetcher: Callable[[str], Awaitable[Any]],
    ) -> Any:
        nonlocal token

        async with token_lock:
            if token is None:
                token = (await client.login(username)).token
            current_token = token

        try:
            return await fetcher(current_token)
        except StokerCloudAuthError:
            try:
                async with token_lock:
                    token = (await client.login(username)).token
                    current_token = token
                return await fetcher(current_token)
            except StokerCloudAuthError as err2:
                raise ConfigEntryAuthFailed(str(err2)) from err2

    async def _async_update_data() -> dict[str, Any]:
        try:
            return await _fetch_with_auth_retry(client.fetch_controller_data)
        except StokerCloudError as err:
            raise UpdateFailed(str(err)) from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}:{username}",
        update_method=_async_update_data,
        update_interval=DEFAULT_UPDATE_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    async def _async_update_event_data() -> dict[str, Any]:
        try:
            data: dict[str, Any] = await _fetch_with_auth_retry(
                lambda t: client.fetch_event_data(
                    t, count=DEFAULT_EVENT_COUNT, offset=DEFAULT_EVENT_OFFSET
                )
            )
        except StokerCloudError as err:
            raise UpdateFailed(str(err)) from err

        events = data.get("events")
        if isinstance(events, list):
            data["events"] = _apply_translations(
                [event for event in events if isinstance(event, dict)]
            )

        data["count"] = DEFAULT_EVENT_COUNT
        data["offset"] = DEFAULT_EVENT_OFFSET
        data["translation_language"] = DEFAULT_TRANSLATION_LANGUAGE
        data["translations_loaded"] = translations is not None
        return data

    event_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}:{username}:events",
        update_method=_async_update_event_data,
        update_interval=DEFAULT_EVENT_UPDATE_INTERVAL,
    )

    try:
        await event_coordinator.async_config_entry_first_refresh()
    except Exception:  # noqa: BLE001
        _LOGGER.warning(
            "Unable to fetch StokerCloud event log on startup", exc_info=True
        )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "event_coordinator": event_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
