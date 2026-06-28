"""Camera entity exposing the current slideshow image."""

from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UhaleCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([UhaleCamera(coordinator)])


class UhaleCamera(CoordinatorEntity[UhaleCoordinator], Camera):
    """Preview of the image currently shown on the frame."""

    _attr_has_entity_name = True
    _attr_name = "Current image"
    _attr_icon = "mdi:image"

    def __init__(self, coordinator: UhaleCoordinator) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        Camera.__init__(self)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_camera"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer="Uhale",
            model="Digital Picture Frame",
        )

    @property
    def available(self) -> bool:
        return True

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        return self.coordinator.current_bytes
