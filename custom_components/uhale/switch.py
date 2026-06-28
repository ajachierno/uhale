"""Switch entity to enable/disable shuffle for the folder slideshow."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SHUFFLE, DOMAIN
from .coordinator import UhaleCoordinator
from .entity import UhaleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UhaleShuffleSwitch(coordinator)])


class UhaleShuffleSwitch(UhaleEntity, SwitchEntity):
    """Present folder images in a random order when on."""

    _attr_name = "Shuffle"
    _attr_icon = "mdi:shuffle-variant"

    def __init__(self, coordinator: UhaleCoordinator) -> None:
        super().__init__(coordinator, "shuffle")

    @property
    def is_on(self) -> bool:
        return self.coordinator.shuffle

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_update_option(CONF_SHUFFLE, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_update_option(CONF_SHUFFLE, False)
