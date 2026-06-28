"""Coordinator that selects the current image and pushes it to the frame."""

from __future__ import annotations

import logging
import os
import random
import secrets
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DLNA_ENTITY,
    CONF_FOLDER,
    CONF_INTERVAL,
    CONF_LOCAL_TARGET,
    CONF_MODE,
    CONF_PLEX_ENTITY,
    CONF_RECURSIVE,
    CONF_SHUFFLE,
    CONF_UPLOADER,
    DEFAULT_INTERVAL,
    DEFAULT_MODE,
    DEFAULT_RECURSIVE,
    DEFAULT_SHUFFLE,
    DEFAULT_UPLOADER,
    DOMAIN,
    IMAGE_EXTENSIONS,
    MIN_INTERVAL,
    MODE_PLEX,
    UPLOADER_DLNA,
    UPLOADER_LOCAL,
)
from .uploaders.base import UhaleImage, UhaleUploader
from .uploaders.dlna import DlnaUploader
from .uploaders.local import LocalUploader

_LOGGER = logging.getLogger(__name__)

_CONTENT_TYPE_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".webp": "image/webp",
}


def _content_type(path: str) -> str:
    return _CONTENT_TYPE_BY_EXT.get(os.path.splitext(path)[1].lower(), "image/jpeg")


class UhaleCoordinator(DataUpdateCoordinator[dict]):
    """Drive the slideshow: pick the next image and deliver it to the frame."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self._options: dict = {}
        self._reload_options(initial=True)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=timedelta(seconds=self.interval),
        )

        # Random token guards the HTTP view that serves the current image.
        self.token = secrets.token_hex(16)

        self._playlist: list[str] = []
        self._index = -1
        self._pending_step = 1
        self._shuffle_state = self.shuffle

        self.current_bytes: bytes | None = None
        self.current_name: str | None = None
        self.current_source: str | None = None
        self.current_content_type = "image/jpeg"

        self._uploader: UhaleUploader | None = self._build_uploader()

    # ------------------------------------------------------------------
    # Option accessors
    # ------------------------------------------------------------------
    def _reload_options(self, initial: bool = False) -> None:
        self._options = {**self.entry.data, **self.entry.options}
        if not initial:
            self.update_interval = timedelta(seconds=self.interval)
            self._uploader = self._build_uploader()
            # Force a rescan so a new folder / shuffle setting takes effect.
            self._playlist = []
            self._index = -1

    @property
    def mode(self) -> str:
        return self._options.get(CONF_MODE, DEFAULT_MODE)

    @property
    def shuffle(self) -> bool:
        return bool(self._options.get(CONF_SHUFFLE, DEFAULT_SHUFFLE))

    @property
    def folder(self) -> str | None:
        return self._options.get(CONF_FOLDER)

    @property
    def recursive(self) -> bool:
        return bool(self._options.get(CONF_RECURSIVE, DEFAULT_RECURSIVE))

    @property
    def plex_entity(self) -> str | None:
        return self._options.get(CONF_PLEX_ENTITY)

    @property
    def interval(self) -> int:
        return max(MIN_INTERVAL, int(self._options.get(CONF_INTERVAL, DEFAULT_INTERVAL)))

    # ------------------------------------------------------------------
    # Public control surface (used by entities / services)
    # ------------------------------------------------------------------
    async def async_reload_from_entry(self) -> None:
        """Re-read options after the config entry changed and refresh."""
        self._reload_options()
        await self.async_request_refresh()

    async def async_update_option(self, key: str, value) -> None:
        """Persist a single option; the update listener re-reads and refreshes."""
        new_options = {**self.entry.options}
        # Seed from data on first edit so existing values are preserved.
        for src_key, src_val in self.entry.data.items():
            new_options.setdefault(src_key, src_val)
        new_options[key] = value
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)

    async def async_step(self, step: int) -> None:
        """Advance (or rewind) the folder slideshow by ``step`` and push."""
        self._pending_step = step
        await self.async_request_refresh()

    async def async_send_raw(self, data: bytes, name: str, content_type: str) -> None:
        """Push an explicit image immediately (used by the send_image service)."""
        self.current_bytes = data
        self.current_name = name
        self.current_source = name
        self.current_content_type = content_type
        self._index = max(self._index, 0)
        await self._push()
        self.async_set_updated_data(
            {"name": name, "source": name, "mode": self.mode}
        )

    def image_url(self) -> str:
        """Absolute URL for the current image, served by the HTTP view."""
        try:
            base = get_url(self.hass, prefer_external=False, allow_external=False)
        except NoURLAvailableError:
            base = get_url(self.hass)
        return (
            f"{base}/api/{DOMAIN}/{self.entry.entry_id}/current"
            f"?token={self.token}&v={self._index}"
        )

    # ------------------------------------------------------------------
    # Uploader wiring
    # ------------------------------------------------------------------
    def _build_uploader(self) -> UhaleUploader | None:
        kind = self._options.get(CONF_UPLOADER, DEFAULT_UPLOADER)
        if kind == UPLOADER_LOCAL:
            return LocalUploader(self.hass, self._options.get(CONF_LOCAL_TARGET, ""))
        if kind == UPLOADER_DLNA:
            renderer = self._options.get(CONF_DLNA_ENTITY)
            if renderer:
                return DlnaUploader(self.hass, renderer, self.image_url)
            _LOGGER.warning("DLNA uploader selected but no renderer entity set")
        return None

    # ------------------------------------------------------------------
    # Refresh: select current image + push
    # ------------------------------------------------------------------
    async def _async_update_data(self) -> dict:
        step = self._pending_step
        self._pending_step = 1
        try:
            if self.mode == MODE_PLEX:
                await self._load_plex_image()
            else:
                await self._load_folder_image(step)
        except UpdateFailed:
            raise
        except Exception as err:  # noqa: BLE001 - surface as coordinator failure
            raise UpdateFailed(str(err)) from err

        await self._push()
        return {
            "name": self.current_name,
            "source": self.current_source,
            "mode": self.mode,
        }

    async def _load_folder_image(self, step: int) -> None:
        folder = self.folder
        if not folder:
            raise UpdateFailed("No folder configured")

        files = await self.hass.async_add_executor_job(self._scan_folder, folder)
        if not files:
            raise UpdateFailed(f"No images found in {folder}")

        if set(files) != set(self._playlist) or self._shuffle_state != self.shuffle:
            self._playlist = list(files)
            if self.shuffle:
                random.shuffle(self._playlist)
            self._shuffle_state = self.shuffle
            if self._index >= len(self._playlist):
                self._index = -1

        self._index = (self._index + step) % len(self._playlist)
        path = self._playlist[self._index]

        data = await self.hass.async_add_executor_job(self._read_file, path)
        self.current_bytes = data
        self.current_name = os.path.basename(path)
        self.current_source = path
        self.current_content_type = _content_type(path)

    def _scan_folder(self, folder: str) -> list[str]:
        result: list[str] = []
        if self.recursive:
            for root, _dirs, names in os.walk(folder):
                for name in names:
                    if name.lower().endswith(IMAGE_EXTENSIONS):
                        result.append(os.path.join(root, name))
        else:
            with os.scandir(folder) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS):
                        result.append(entry.path)
        return sorted(result)

    @staticmethod
    def _read_file(path: str) -> bytes:
        with open(path, "rb") as handle:
            return handle.read()

    async def _load_plex_image(self) -> None:
        entity_id = self.plex_entity
        if not entity_id:
            raise UpdateFailed("No Plex media_player entity configured")

        state = self.hass.states.get(entity_id)
        if state is None:
            raise UpdateFailed(f"Entity {entity_id} not found")

        picture = state.attributes.get("entity_picture")
        if not picture:
            raise UpdateFailed(f"{entity_id} is not showing any artwork right now")

        if picture.startswith("http"):
            url = picture
        else:
            try:
                base = get_url(self.hass, prefer_external=False, allow_external=False)
            except NoURLAvailableError:
                base = get_url(self.hass)
            url = f"{base}{picture}"

        session = async_get_clientsession(self.hass)
        async with session.get(url) as resp:
            resp.raise_for_status()
            self.current_bytes = await resp.read()
            self.current_content_type = resp.headers.get("Content-Type", "image/jpeg")

        self.current_name = (
            state.attributes.get("media_title")
            or state.attributes.get("friendly_name")
            or "Plex artwork"
        )
        self.current_source = entity_id

    async def _push(self) -> None:
        if self._uploader is None or self.current_bytes is None:
            return
        image = UhaleImage(
            data=self.current_bytes,
            name=self.current_name or "image",
            content_type=self.current_content_type,
        )
        try:
            await self._uploader.async_send(image)
        except Exception as err:  # noqa: BLE001 - never let a push break the loop
            _LOGGER.warning("Failed to push image to Uhale frame: %s", err)
