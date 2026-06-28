"""The Uhale Digital Picture Frame integration."""

from __future__ import annotations

import logging
import os

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_CONFIG_ENTRY_ID,
    ATTR_FOLDER,
    ATTR_PATH,
    ATTR_URL,
    CONF_FOLDER,
    DOMAIN,
    PLATFORMS,
    SERVICE_NEXT,
    SERVICE_PREVIOUS,
    SERVICE_REFRESH,
    SERVICE_SEND_IMAGE,
    SERVICE_SET_FOLDER,
)
from .coordinator import UhaleCoordinator
from .http import async_register_views

_LOGGER = logging.getLogger(__name__)

_SERVICES_REGISTERED = f"{DOMAIN}_services_registered"

_CONTENT_TYPE_BY_EXT = {
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uhale from a config entry."""
    coordinator = UhaleCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async_register_views(hass)

    # Do not hard-fail setup if the folder is momentarily empty/unavailable;
    # entities simply report unavailable until images flow.
    await coordinator.async_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _async_register_services(hass)
    _async_notify_display_url(hass, entry, coordinator)
    return True


def _async_notify_display_url(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: UhaleCoordinator
) -> None:
    """Drop a persistent notification with the full-screen page URL.

    This is the URL a kiosk app on the frame should load. It includes the
    access token, so it is only surfaced inside Home Assistant.
    """
    try:
        url = coordinator.show_url()
    except Exception:  # noqa: BLE001 - URL may be unavailable very early in setup
        return
    persistent_notification.async_create(
        hass,
        (
            f"Point your frame's kiosk app at this full-screen display page:\n\n"
            f"`{url}`\n\n"
            "It auto-advances using this integration's folder / Plex / shuffle "
            "settings. The same URL is on the **Current image** sensor's "
            "`display_url` attribute."
        ),
        title=f"Uhale: {entry.title} display URL",
        notification_id=f"{DOMAIN}_{entry.entry_id}_display_url",
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Re-read options without tearing down platforms."""
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_reload_from_entry()


def _coordinators_for_call(hass: HomeAssistant, call: ServiceCall) -> list[UhaleCoordinator]:
    entry_id = call.data.get(ATTR_CONFIG_ENTRY_ID)
    store: dict[str, UhaleCoordinator] = hass.data.get(DOMAIN, {})
    if entry_id:
        coordinator = store.get(entry_id)
        if coordinator is None:
            raise HomeAssistantError(f"Unknown config_entry_id: {entry_id}")
        return [coordinator]
    return list(store.values())


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.data.get(_SERVICES_REGISTERED):
        return

    async def _next(call: ServiceCall) -> None:
        for coordinator in _coordinators_for_call(hass, call):
            await coordinator.async_step(1)

    async def _previous(call: ServiceCall) -> None:
        for coordinator in _coordinators_for_call(hass, call):
            await coordinator.async_step(-1)

    async def _refresh(call: ServiceCall) -> None:
        for coordinator in _coordinators_for_call(hass, call):
            await coordinator.async_request_refresh()

    async def _set_folder(call: ServiceCall) -> None:
        folder = call.data[ATTR_FOLDER]
        for coordinator in _coordinators_for_call(hass, call):
            await coordinator.async_update_option(CONF_FOLDER, folder)

    async def _send_image(call: ServiceCall) -> None:
        path = call.data.get(ATTR_PATH)
        url = call.data.get(ATTR_URL)
        if not path and not url:
            raise HomeAssistantError("Provide either 'path' or 'url'")

        if path:
            if not hass.config.is_allowed_path(path):
                raise HomeAssistantError(f"Path not allowed: {path}")
            data = await hass.async_add_executor_job(_read_bytes, path)
            name = os.path.basename(path)
            content_type = _CONTENT_TYPE_BY_EXT.get(
                os.path.splitext(path)[1].lower(), "image/jpeg"
            )
        else:
            from homeassistant.helpers.aiohttp_client import async_get_clientsession

            session = async_get_clientsession(hass)
            async with session.get(url) as resp:
                resp.raise_for_status()
                data = await resp.read()
                content_type = resp.headers.get("Content-Type", "image/jpeg")
            name = url.rsplit("/", 1)[-1] or "image"

        for coordinator in _coordinators_for_call(hass, call):
            await coordinator.async_send_raw(data, name, content_type)

    entry_target = {vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string}

    hass.services.async_register(
        DOMAIN, SERVICE_NEXT, _next, schema=vol.Schema(entry_target)
    )
    hass.services.async_register(
        DOMAIN, SERVICE_PREVIOUS, _previous, schema=vol.Schema(entry_target)
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REFRESH, _refresh, schema=vol.Schema(entry_target)
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_FOLDER,
        _set_folder,
        schema=vol.Schema({**entry_target, vol.Required(ATTR_FOLDER): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_IMAGE,
        _send_image,
        schema=vol.Schema(
            {
                **entry_target,
                vol.Optional(ATTR_PATH): cv.string,
                vol.Optional(ATTR_URL): cv.url,
            }
        ),
    )

    hass.data[_SERVICES_REGISTERED] = True


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()
