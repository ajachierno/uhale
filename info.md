# Uhale Digital Picture Frame

Send photos to a Uhale digital picture frame from Home Assistant.

- **Folder source** (local path or mounted NAS share), with optional subfolders
- **Shuffle** for random order
- **Plex source** — mirror the current artwork from a selected Plex player
- **One toggle** to flip between the folder slideshow and Plex
- **Pluggable frame transport**: DLNA/cast renderer, copy-to-folder (local/NAS),
  or preview-only

> Uhale frames have no official local API, so delivery to the frame goes through
> a small pluggable transport layer — use whichever method works for your frame.
> See the README for details.
