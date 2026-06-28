"""Sensor entity reporting the current image."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import UhaleCoordinator
from .entity import UhaleEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UhaleCurrentImageSensor(coordinator)])


class UhaleCurrentImageSensor(UhaleEntity, SensorEntity):
    """Name/source of the image currently being shown."""

    _attr_name = "Current image"
    _attr_icon = "mdi:image-text"

    def __init__(self, coordinator: UhaleCoordinator) -> None:
        super().__init__(coordinator, "current_image")

    @property
    def native_value(self) -> str | None:
        return self.coordinator.current_name

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        try:
            display_url = self.coordinator.show_url()
        except Exception:  # noqa: BLE001 - base URL may be unavailable
            display_url = None
        return {
            "mode": self.coordinator.mode,
            "source": self.coordinator.current_source,
            "shuffle": self.coordinator.shuffle,
            "display_url": display_url,
        }
