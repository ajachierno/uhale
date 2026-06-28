"""Constants for the Uhale Digital Picture Frame integration."""

from __future__ import annotations

DOMAIN = "uhale"

# Platforms this integration sets up.
PLATFORMS: list[str] = ["camera", "select", "sensor", "switch", "button"]

# ---------------------------------------------------------------------------
# Configuration / option keys
# ---------------------------------------------------------------------------
CONF_NAME = "name"
CONF_MODE = "mode"
CONF_FOLDER = "folder"
CONF_SHUFFLE = "shuffle"
CONF_INTERVAL = "interval"
CONF_PLEX_ENTITY = "plex_entity"
CONF_UPLOADER = "uploader"
CONF_DLNA_ENTITY = "dlna_entity"
CONF_LOCAL_TARGET = "local_target"
CONF_RECURSIVE = "recursive"

# ---------------------------------------------------------------------------
# Source modes
# ---------------------------------------------------------------------------
MODE_FOLDER = "folder"
MODE_PLEX = "plex"
MODES: list[str] = [MODE_FOLDER, MODE_PLEX]

# ---------------------------------------------------------------------------
# Uploader (frame transport) types
# ---------------------------------------------------------------------------
# Uhale frames expose no official local API. The uploader layer is pluggable so
# whatever transport works for a given frame/setup can be swapped in without
# touching the rest of the integration.
UPLOADER_DLNA = "dlna"
UPLOADER_LOCAL = "local"
UPLOADER_NONE = "none"
UPLOADERS: list[str] = [UPLOADER_DLNA, UPLOADER_LOCAL, UPLOADER_NONE]

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_MODE = MODE_FOLDER
DEFAULT_SHUFFLE = False
DEFAULT_INTERVAL = 60
DEFAULT_UPLOADER = UPLOADER_DLNA
DEFAULT_RECURSIVE = True

MIN_INTERVAL = 5

IMAGE_EXTENSIONS: tuple[str, ...] = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
)

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
SERVICE_NEXT = "next_image"
SERVICE_PREVIOUS = "previous_image"
SERVICE_REFRESH = "refresh"
SERVICE_SEND_IMAGE = "send_image"
SERVICE_SET_FOLDER = "set_folder"

ATTR_CONFIG_ENTRY_ID = "config_entry_id"
ATTR_PATH = "path"
ATTR_URL = "url"
ATTR_FOLDER = "folder"
