"""Config and options flow for the Uhale integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_DLNA_ENTITY,
    CONF_FOLDER,
    CONF_INTERVAL,
    CONF_LOCAL_TARGET,
    CONF_MODE,
    CONF_NAME,
    CONF_PLEX_ENTITY,
    CONF_RECURSIVE,
    CONF_SHUFFLE,
    CONF_SMB_PASSWORD,
    CONF_SMB_USERNAME,
    CONF_UPLOADER,
    DEFAULT_INTERVAL,
    DEFAULT_MODE,
    DEFAULT_RECURSIVE,
    DEFAULT_SHUFFLE,
    DEFAULT_UPLOADER,
    DOMAIN,
    MIN_INTERVAL,
    MODES,
    UPLOADERS,
)

_MODE_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=MODES,
        translation_key="mode",
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)

_UPLOADER_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=UPLOADERS,
        translation_key="uploader",
        mode=selector.SelectSelectorMode.DROPDOWN,
    )
)

_MEDIA_PLAYER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="media_player")
)

_TEXT_SELECTOR = selector.TextSelector()

_INTERVAL_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_INTERVAL,
        max=86400,
        step=1,
        unit_of_measurement="s",
        mode=selector.NumberSelectorMode.BOX,
    )
)


def _common_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Schema shared by the create and options flows (minus the name)."""
    return vol.Schema(
        {
            vol.Required(
                CONF_MODE, default=defaults.get(CONF_MODE, DEFAULT_MODE)
            ): _MODE_SELECTOR,
            vol.Optional(
                CONF_FOLDER, default=defaults.get(CONF_FOLDER, "")
            ): _TEXT_SELECTOR,
            vol.Optional(
                CONF_RECURSIVE,
                default=defaults.get(CONF_RECURSIVE, DEFAULT_RECURSIVE),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_SHUFFLE, default=defaults.get(CONF_SHUFFLE, DEFAULT_SHUFFLE)
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_PLEX_ENTITY,
                description={"suggested_value": defaults.get(CONF_PLEX_ENTITY)},
            ): _MEDIA_PLAYER_SELECTOR,
            vol.Optional(
                CONF_INTERVAL,
                default=defaults.get(CONF_INTERVAL, DEFAULT_INTERVAL),
            ): _INTERVAL_SELECTOR,
            vol.Required(
                CONF_UPLOADER,
                default=defaults.get(CONF_UPLOADER, DEFAULT_UPLOADER),
            ): _UPLOADER_SELECTOR,
            vol.Optional(
                CONF_DLNA_ENTITY,
                description={"suggested_value": defaults.get(CONF_DLNA_ENTITY)},
            ): _MEDIA_PLAYER_SELECTOR,
            vol.Optional(
                CONF_LOCAL_TARGET, default=defaults.get(CONF_LOCAL_TARGET, "")
            ): _TEXT_SELECTOR,
            vol.Optional(
                CONF_SMB_USERNAME,
                description={"suggested_value": defaults.get(CONF_SMB_USERNAME)},
            ): _TEXT_SELECTOR,
            vol.Optional(
                CONF_SMB_PASSWORD,
                description={"suggested_value": defaults.get(CONF_SMB_PASSWORD)},
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }
    )


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce numeric values and drop empty optional fields."""
    cleaned = dict(data)
    if CONF_INTERVAL in cleaned and cleaned[CONF_INTERVAL] is not None:
        cleaned[CONF_INTERVAL] = int(cleaned[CONF_INTERVAL])
    for key in (
        CONF_FOLDER,
        CONF_LOCAL_TARGET,
        CONF_PLEX_ENTITY,
        CONF_DLNA_ENTITY,
        CONF_SMB_USERNAME,
        CONF_SMB_PASSWORD,
    ):
        if cleaned.get(key) in ("", None):
            cleaned.pop(key, None)
    return cleaned


class UhaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            name = user_input.pop(CONF_NAME)
            return self.async_create_entry(title=name, data=_clean(user_input))

        schema = vol.Schema(
            {vol.Required(CONF_NAME, default="Uhale Frame"): _TEXT_SELECTOR}
        ).extend(_common_schema({}).schema)

        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> UhaleOptionsFlow:
        return UhaleOptionsFlow()


class UhaleOptionsFlow(OptionsFlow):
    """Allow editing every setting after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=_clean(user_input))

        defaults = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_common_schema(defaults)
        )
