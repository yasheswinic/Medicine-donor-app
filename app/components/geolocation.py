"""Browser live GPS for Streamlit (free, no API key)."""

from __future__ import annotations

from typing import Any, Optional

import streamlit.components.v1 as components


_GEO_HTML = """
<div id="meddonate-geo-status" style="font-size:12px;color:#64748b;padding:4px 0;">
  Requesting location permission…
</div>
<script>
(function() {
  const statusEl = document.getElementById("meddonate-geo-status");
  function send(value) {
    window.parent.postMessage({ type: "streamlit:setComponentValue", value: value }, "*");
  }
  if (!navigator.geolocation) {
    statusEl.textContent = "Geolocation not supported in this browser.";
    send({ error: "Geolocation not supported in this browser." });
    return;
  }
  navigator.geolocation.getCurrentPosition(
    function(pos) {
      const payload = {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy_m: Math.round(pos.coords.accuracy || 0),
      };
      statusEl.textContent = "Location received (" + payload.lat.toFixed(4) + ", " + payload.lng.toFixed(4) + ")";
      send(payload);
    },
    function(err) {
      let msg = err.message || "Location denied";
      if (err.code === 1) msg = "Permission denied — allow location access in your browser.";
      if (err.code === 2) msg = "Position unavailable — try again outdoors or check GPS.";
      if (err.code === 3) msg = "Timed out — try again.";
      statusEl.textContent = msg;
      send({ error: msg });
    },
    { enableHighAccuracy: true, timeout: 20000, maximumAge: 60000 }
  );
})();
</script>
"""


def request_live_location() -> Optional[dict[str, Any]]:
    """
    Trigger browser GPS. Returns {lat, lng, accuracy_m} or {error: ...}.
    User must allow location in the browser popup.
    """
    result = components.html(_GEO_HTML, height=60)
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            import json
            return json.loads(result)
        except Exception:
            pass
    return None
