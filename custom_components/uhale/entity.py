"""Shared base entity for the Uhale integration."""

from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import UhaleCoordinator


class UhaleEntity(CoordinatorEntity[UhaleCoordinator]):
    """Base class wiring entities to the per-frame device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: UhaleCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name=self.coordinator.entry.title,
            manufacturer="Uhale",
            model="Digital Picture Frame",
        )
