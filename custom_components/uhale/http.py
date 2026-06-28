"""HTTP view that serves the current image to LAN renderers (e.g. DLNA)."""

from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_VIEW_REGISTERED = f"{DOMAIN}_view_registered"


class UhaleImageView(HomeAssistantView):
    """Serve the current image for a config entry, guarded by a token."""

    url = "/api/" + DOMAIN + "/{entry_id}/current"
    name = "api:" + DOMAIN + ":current"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        coordinator = self.hass.data.get(DOMAIN, {}).get(entry_id)
        if coordinator is None:
            return web.Response(status=404)
        if request.query.get("token") != coordinator.token:
            return web.Response(status=401)
        if coordinator.current_bytes is None:
            return web.Response(status=404)
        return web.Response(
            body=coordinator.current_bytes,
            content_type=coordinator.current_content_type,
            headers={"Cache-Control": "no-store"},
        )


def async_register_view(hass: HomeAssistant) -> None:
    """Register the image view exactly once."""
    if hass.data.get(_VIEW_REGISTERED):
        return
    hass.http.register_view(UhaleImageView(hass))
    hass.data[_VIEW_REGISTERED] = True
