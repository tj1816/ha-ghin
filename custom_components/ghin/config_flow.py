"""Config flow for the GHIN integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GhinApiError, GhinAuthError, GhinClient
from .const import (
    CONF_CLIENT_TOKEN,
    CONF_EMAIL,
    CONF_PASSWORD,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CLIENT_TOKEN): str,
    }
)


async def _validate_login(
    hass: HomeAssistant, email: str, password: str, client_token: str
) -> dict:
    session = async_get_clientsession(hass)
    client = GhinClient(email, password, client_token, session)
    golfer = await client.async_login()
    return golfer


class GhinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GHIN."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                golfer = await _validate_login(
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_CLIENT_TOKEN],
                )
            except GhinAuthError:
                errors["base"] = "invalid_auth"
            except GhinApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating GHIN login")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(golfer["ghin_number"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=golfer.get("player_name", "GHIN"),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow updating credentials/token (e.g. after GHIN rotates the token)."""
        errors: dict[str, str] = {}
        reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            try:
                golfer = await _validate_login(
                    self.hass,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                    user_input[CONF_CLIENT_TOKEN],
                )
            except GhinAuthError:
                errors["base"] = "invalid_auth"
            except GhinApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating GHIN login")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(golfer["ghin_number"])
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    title=golfer.get("player_name", "GHIN"),
                    data=user_input,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, reconfigure_entry.data
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return GhinOptionsFlow(config_entry)


class GhinOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval_hours",
                        default=self.config_entry.options.get(
                            "scan_interval_hours", DEFAULT_SCAN_INTERVAL_HOURS
                        ),
                    ): vol.All(int, vol.Range(min=1, max=24)),
                }
            ),
        )
