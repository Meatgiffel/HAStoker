from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import StokerCloudAuthError, StokerCloudClient, StokerCloudError
from .const import CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _validate_input(hass: HomeAssistant, username: str) -> dict[str, Any]:
    client = StokerCloudClient(async_get_clientsession(hass))
    login = await client.login(username)
    data = await client.fetch_controller_data(login.token)

    serial = data.get("serial")
    alias = data.get("alias")
    return {"serial": serial, "alias": alias}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            try:
                info = await _validate_input(self.hass, username)
            except StokerCloudAuthError:
                errors["base"] = "auth"
            except StokerCloudError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating StokerCloud account")
                errors["base"] = "unknown"
            else:
                unique_id = str(info.get("serial") or username)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                title = (
                    f"{info['serial']} / {info['alias']}"
                    if info.get("serial") and info.get("alias")
                    else username
                )
                return self.async_create_entry(
                    title=title,
                    data={CONF_USERNAME: username},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_USERNAME): str}),
            errors=errors,
        )

