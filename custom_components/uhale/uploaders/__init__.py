"""Pluggable transports for delivering images to a Uhale frame."""

from __future__ import annotations

from .base import UhaleImage, UhaleUploader

__all__ = ["UhaleImage", "UhaleUploader"]
