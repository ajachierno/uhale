"""DLNA / media-renderer uploader.

If the frame (or a casting target near it) appears in Home Assistant as a
``media_player`` that accepts images, this uploader casts the current image to
it via the ``media_player.play_media`` service. The image is served by the
integration's own authenticated-by-token HTTP view so the renderer can fetch it
over the LAN.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from homeassistant.core import HomeAssistant

from .base import UhaleImage, UhaleUploader

_LOGGER = logging.getLogger(__name__)


class DlnaUploader(UhaleUploader):
    """Cast the current image to a media_player renderer."""

    name = "dlna"

    def __init__(
        self,
        hass: HomeAssistant,
        renderer_entity_id: str,
        url_factory: Callable[[], str],
    ) -> None:
        self._hass = hass
        self._renderer = renderer_entity_id
        self._url_factory = url_factory

    async def async_send(self, image: UhaleImage) -> None:
        if not self._renderer:
            raise ValueError("No DLNA renderer entity configured")
        url = self._url_factory()
        _LOGGER.debug("Casting %s to %s", url, self._renderer)
        await self._hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": self._renderer,
                "media_content_id": url,
                "media_content_type": "image",
            },
            blocking=True,
        )
