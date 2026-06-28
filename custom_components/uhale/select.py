"""Select entity to toggle between the Plex and folder source."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_MODE, DOMAIN, MODES
from .coordinator import UhaleCoordinator
from .entity import UhaleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UhaleModeSelect(coordinator)])


class UhaleModeSelect(UhaleEntity, SelectEntity):
    """Choose whether the frame shows the folder slideshow or Plex artwork."""

    _attr_name = "Source mode"
    _attr_icon = "mdi:image-multiple"
    _attr_translation_key = "mode"
    _attr_options = MODES

    def __init__(self, coordinator: UhaleCoordinator) -> None:
        super().__init__(coordinator, "mode")

    @property
    def current_option(self) -> str:
        return self.coordinator.mode

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_update_option(CONF_MODE, option)
