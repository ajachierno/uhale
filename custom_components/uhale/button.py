"""Button entities for manual slideshow control."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import UhaleCoordinator
from .entity import UhaleEntity


@dataclass(frozen=True, kw_only=True)
class UhaleButtonDescription(ButtonEntityDescription):
    """Describe a Uhale button and the coordinator action it triggers."""

    action: Callable[[UhaleCoordinator], Awaitable[None]]


BUTTONS: tuple[UhaleButtonDescription, ...] = (
    UhaleButtonDescription(
        key="next",
        name="Next image",
        icon="mdi:skip-next",
        action=lambda c: c.async_step(1),
    ),
    UhaleButtonDescription(
        key="previous",
        name="Previous image",
        icon="mdi:skip-previous",
        action=lambda c: c.async_step(-1),
    ),
    UhaleButtonDescription(
        key="refresh",
        name="Refresh",
        icon="mdi:refresh",
        action=lambda c: c.async_request_refresh(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: UhaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(UhaleButton(coordinator, desc) for desc in BUTTONS)


class UhaleButton(UhaleEntity, ButtonEntity):
    """A button that runs a coordinator action."""

    entity_description: UhaleButtonDescription

    def __init__(
        self, coordinator: UhaleCoordinator, description: UhaleButtonDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await self.entity_description.action(self.coordinator)
