"""Local / NAS folder uploader.

Writes the current image into a target directory using a stable filename. Point
this at a folder the Uhale app (or the frame itself) syncs from -- e.g. a Samba
share, an SMB-mounted NAS folder, or a cloud-sync folder -- and the frame picks
up the latest image. A timestamped copy is also kept so a sequence builds up.
"""

from __future__ import annotations

import logging
import os
import time

from homeassistant.core import HomeAssistant

from .base import UhaleImage, UhaleUploader

_LOGGER = logging.getLogger(__name__)

_EXT_BY_TYPE = {
    "image/png": ".png",
    "image/gif": ".gif",
    "image/bmp": ".bmp",
    "image/webp": ".webp",
}


class LocalUploader(UhaleUploader):
    """Copy the current image to a (possibly network) folder."""

    name = "local"

    def __init__(self, hass: HomeAssistant, target_dir: str, keep_history: bool = True) -> None:
        self._hass = hass
        self._target_dir = target_dir
        self._keep_history = keep_history

    async def async_send(self, image: UhaleImage) -> None:
        if not self._target_dir:
            raise ValueError("No local target folder configured")
        await self._hass.async_add_executor_job(self._write, image)

    def _write(self, image: UhaleImage) -> None:
        os.makedirs(self._target_dir, exist_ok=True)
        ext = _EXT_BY_TYPE.get(image.content_type, ".jpg")

        # Stable "current" file the frame can always point at.
        current_path = os.path.join(self._target_dir, f"uhale_current{ext}")
        tmp_path = current_path + ".tmp"
        with open(tmp_path, "wb") as handle:
            handle.write(image.data)
        os.replace(tmp_path, current_path)

        if self._keep_history:
            stamped = os.path.join(
                self._target_dir, f"uhale_{int(time.time())}{ext}"
            )
            try:
                with open(stamped, "wb") as handle:
                    handle.write(image.data)
            except OSError as err:  # pragma: no cover - best effort only
                _LOGGER.debug("Could not write history copy %s: %s", stamped, err)
