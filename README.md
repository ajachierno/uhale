# Uhale Digital Picture Frame — Home Assistant integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Validate](https://github.com/ajachierno/uhale/actions/workflows/validate.yml/badge.svg)](https://github.com/ajachierno/uhale/actions/workflows/validate.yml)

Send photos to a **Uhale** digital picture frame from Home Assistant. Point it at a
folder (local path or a mounted NAS share), shuffle the order, or mirror the
**current artwork from a Plex player** — and flip between the two with a single
toggle.

> **Heads up on Uhale frames.** Uhale frames (made by Zeasn) are driven by the
> Uhale mobile app and the Uhale cloud. There is **no official, documented local
> API** for pushing an image straight to the frame. This integration is built
> around that reality: image selection (folder/Plex/shuffle) is fully implemented,
> and delivery to the frame goes through a small **pluggable transport** layer so
> you can use whatever method works for your frame. See
> [How images reach the frame](#how-images-reach-the-frame).

## Features

- **Folder source** — local path or mounted NAS share (SMB/NFS), with optional
  recursion into subfolders.
- **Shuffle** — present folder images in random order, toggled live.
- **Plex source** — show the artwork currently playing on a selected Plex
  `media_player` (reuses Home Assistant's existing Plex integration).
- **One toggle** — a `select` entity flips between *Folder slideshow* and
  *Plex current artwork*.
- **Pluggable frame transport** — DLNA/cast renderer, or copy-to-folder
  (local/NAS), or preview-only.
- Entities per frame: a **camera** preview, **source mode** select, **shuffle**
  switch, **current image** sensor, and **Next / Previous / Refresh** buttons.
- Services: `uhale.next_image`, `uhale.previous_image`, `uhale.refresh`,
  `uhale.set_folder`, `uhale.send_image`.

## Installation (HACS)

1. In HACS go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/ajachierno/uhale` with category **Integration**.
3. Download **Uhale Digital Picture Frame**, then restart Home Assistant.
4. **Settings → Devices & services → Add integration → Uhale**.

[![Open your Home Assistant instance and open a repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ajachierno&repository=uhale&category=integration)

### Manual installation

Copy `custom_components/uhale` into your Home Assistant `config/custom_components/`
folder and restart.

## Configuration

Everything is set up from the UI (config flow) and editable later under the
integration's **Configure** (options):

| Option | What it does |
| --- | --- |
| **Source mode** | `Folder slideshow` or `Plex current artwork`. |
| **Image folder** | Absolute path to a local folder or mounted NAS share. |
| **Include subfolders** | Recurse into subdirectories when scanning. |
| **Shuffle** | Random order for the folder slideshow. |
| **Plex media player** | The `media_player` whose now-playing art is mirrored. |
| **Slideshow interval** | Seconds between images (folder) / refresh (Plex). |
| **Frame transport** | `DLNA / cast renderer`, `Local / NAS folder`, or `None`. |
| **DLNA renderer** | The `media_player` to cast to (DLNA transport). |
| **Target folder** | Folder to write the current image into (local transport). |

> **Folder access:** local paths must be readable by Home Assistant. For the
> `send_image` service the path must also sit under an
> [allowlisted directory](https://www.home-assistant.io/integrations/homeassistant/#allowlist_external_dirs).
> NAS shares should be mounted into the HA host/container first.

## How images reach the frame

Because there's no official Uhale local API, delivery is handled by a small
**uploader** interface (`custom_components/uhale/uploaders/`). Pick the transport
that matches your setup:

- **Local / NAS folder** *(most reliable for Uhale today)* — writes the current
  image as `uhale_current.*` (plus timestamped copies) into a folder. Point this
  at the folder your frame or the Uhale app syncs from (e.g. an SMB share). The
  frame then displays whatever lands there.
- **DLNA / cast renderer** — if the frame (or a casting device next to it)
  appears in Home Assistant as a `media_player` that accepts images, the current
  image is cast to it via `media_player.play_media`. The image is served by the
  integration's own token-guarded HTTP view at
  `/api/uhale/<entry_id>/current`.
- **None** — selects nothing; the camera entity still previews the chosen image,
  which is handy while wiring things up or for use in your own automations.

### Adding a different transport

Subclass `UhaleUploader` (see `uploaders/base.py`), implement `async_send`, and
return it from `UhaleCoordinator._build_uploader`. If someone documents a working
Uhale cloud/local push, it drops in here without touching the rest of the
integration.

## Services

| Service | Description |
| --- | --- |
| `uhale.next_image` | Advance the folder slideshow and push. |
| `uhale.previous_image` | Go back one image. |
| `uhale.refresh` | Re-evaluate the source and push now. |
| `uhale.set_folder` | Change the source folder at runtime. |
| `uhale.send_image` | Push a specific image by `path` or `url`. |

Each service accepts an optional `config_entry_id` to target one frame; omit it
to apply to all configured frames.

## Disclaimer

Not affiliated with or endorsed by Uhale / Zeasn. "Uhale" is used only to
describe compatibility. Provided as-is under the MIT license.
