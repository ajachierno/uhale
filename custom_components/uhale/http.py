"""HTTP views: serve the current image, a JSON state, and a full-screen page.

The display page is what a kiosk app on the frame loads. It polls the state
endpoint and cross-fades to the new image whenever the coordinator advances --
so the frame becomes a live window onto whatever the integration selects
(folder slideshow, Plex artwork, shuffle, etc.). All three views are guarded by
the per-entry token.
"""

from __future__ import annotations

import json

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_VIEWS_REGISTERED = f"{DOMAIN}_views_registered"


def _coordinator(hass: HomeAssistant, entry_id: str):
    return hass.data.get(DOMAIN, {}).get(entry_id)


class UhaleImageView(HomeAssistantView):
    """Serve the current image bytes for a config entry."""

    url = "/api/" + DOMAIN + "/{entry_id}/current"
    name = "api:" + DOMAIN + ":current"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        coordinator = _coordinator(self.hass, entry_id)
        if coordinator is None:
            return web.Response(status=404)
        if request.query.get("token") != coordinator.token:
            return web.Response(status=401)
        if coordinator.current_bytes is None:
            return web.Response(status=404)
        return web.Response(
            body=coordinator.current_bytes,
            content_type=coordinator.current_content_type,
            headers={"Cache-Control": "no-store"},
        )


class UhaleStateView(HomeAssistantView):
    """Return the current image version + name as JSON (polled by the page)."""

    url = "/api/" + DOMAIN + "/{entry_id}/state"
    name = "api:" + DOMAIN + ":state"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        coordinator = _coordinator(self.hass, entry_id)
        if coordinator is None:
            return web.Response(status=404)
        if request.query.get("token") != coordinator.token:
            return web.Response(status=401)
        body = json.dumps(
            {
                "version": coordinator.current_version,
                "name": coordinator.current_name,
                "mode": coordinator.mode,
            }
        )
        return web.Response(
            body=body,
            content_type="application/json",
            headers={"Cache-Control": "no-store"},
        )


_PAGE = """<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Uhale</title>
<style>
  html,body{{margin:0;height:100%;width:100%;background:#000;overflow:hidden;
    cursor:none;-webkit-user-select:none;user-select:none}}
  .layer{{position:absolute;inset:0;width:100%;height:100%;
    background-position:center;background-repeat:no-repeat;background-size:contain;
    opacity:0;transition:opacity .8s ease-in-out}}
  .layer.on{{opacity:1}}
</style></head>
<body>
  <div id="a" class="layer"></div>
  <div id="b" class="layer"></div>
<script>
  var ENTRY={entry!r};
  var TOKEN={token!r};
  var ver=-1, cur=0;
  var layers=[document.getElementById("a"), document.getElementById("b")];
  function swap(v){{
    var img=new Image();
    img.onload=function(){{
      var next=layers[cur^1];
      next.style.backgroundImage="url('"+img.src+"')";
      next.classList.add("on");
      layers[cur].classList.remove("on");
      cur^=1;
    }};
    img.src="/api/{domain}/"+ENTRY+"/current?token="+TOKEN+"&v="+v;
  }}
  function tick(){{
    fetch("/api/{domain}/"+ENTRY+"/state?token="+TOKEN, {{cache:"no-store"}})
      .then(function(r){{return r.json();}})
      .then(function(j){{ if(j.version!==ver){{ ver=j.version; swap(ver); }} }})
      .catch(function(){{}});
  }}
  setInterval(tick, 2000);
  tick();
  // Best-effort: keep the screen awake on browsers that support it.
  if ("wakeLock" in navigator) {{
    var relock=function(){{ navigator.wakeLock.request("screen").catch(function(){{}}); }};
    relock();
    document.addEventListener("visibilitychange", function(){{
      if (document.visibilityState==="visible") relock();
    }});
  }}
</script></body></html>"""


class UhaleShowView(HomeAssistantView):
    """Serve the full-screen auto-advancing display page."""

    url = "/api/" + DOMAIN + "/{entry_id}/show"
    name = "api:" + DOMAIN + ":show"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        coordinator = _coordinator(self.hass, entry_id)
        if coordinator is None:
            return web.Response(status=404)
        if request.query.get("token") != coordinator.token:
            return web.Response(status=401)
        html = _PAGE.format(entry=entry_id, token=coordinator.token, domain=DOMAIN)
        return web.Response(
            body=html, content_type="text/html", headers={"Cache-Control": "no-store"}
        )


def async_register_views(hass: HomeAssistant) -> None:
    """Register all HTTP views exactly once."""
    if hass.data.get(_VIEWS_REGISTERED):
        return
    hass.http.register_view(UhaleImageView(hass))
    hass.http.register_view(UhaleStateView(hass))
    hass.http.register_view(UhaleShowView(hass))
    hass.data[_VIEWS_REGISTERED] = True
