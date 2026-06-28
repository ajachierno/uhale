"""Uploader interface for the Uhale integration.

Uhale digital picture frames (made by Zeasn) are driven by the Uhale mobile app
and the Uhale cloud. There is no official, documented local API for pushing an
image to the frame. To keep the rest of the integration independent of that
reality, all delivery goes through the small :class:`UhaleUploader` interface
defined here. Add a new transport by subclassing it and returning the instance
from ``UhaleCoordinator._build_uploader``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class UhaleImage:
    """A single image to be delivered to a frame."""

    data: bytes
    name: str
    content_type: str = "image/jpeg"
    source_url: str | None = None


class UhaleUploader(ABC):
    """Base class for anything that can deliver an image to a Uhale frame."""

    #: Short identifier used in logs / diagnostics.
    name: str = "base"

    @abstractmethod
    async def async_send(self, image: UhaleImage) -> None:
        """Deliver a single image to the frame.

        Implementations should raise on failure so the coordinator can surface
        the problem; they must not block the event loop.
        """

    async def async_test(self) -> bool:
        """Optionally verify the transport is reachable. Defaults to True."""
        return True
