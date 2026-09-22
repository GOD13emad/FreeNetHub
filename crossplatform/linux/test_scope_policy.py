#!/usr/bin/env python3
import importlib.util
import pathlib

p = pathlib.Path(__file__).with_name("freenet_hub_linux.py")
spec = importlib.util.spec_from_file_location("fnh_scope", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

calls = []

m._disconnect_owned_system_warp = lambda: calls.append("disconnect-system") or {"ok": True}
m.stop_tor = lambda: calls.append("stop-tor") or {"ok": True}
m.start_tor = lambda force_mode=None: calls.append(("start-tor", force_mode)) or {"ok": True, "mode": force_mode or "direct"}
m.warp_connect_safe = lambda: calls.append("warp-system") or {"ok": True, "warp": "on"}

r = m.connect_mode("AUTO", full_system=False)
assert r["ok"] is True and r["scope"] == "BROWSER"
assert "warp-system" not in calls
assert ("start-tor", None) in calls
assert "disconnect-system" in calls

calls.clear()
r = m.connect_mode("WARP", full_system=False)
assert r["ok"] is False and r["error"] == "WARP_BROWSER_ONLY_UNAVAILABLE"
assert "warp-system" not in calls
assert "disconnect-system" in calls

calls.clear()
r = m.connect_mode("WARP", full_system=True)
assert r["ok"] is True and r["scope"] == "SYSTEM"
assert "warp-system" in calls

calls.clear()
r = m.connect_mode("TOR", full_system=True)
assert r["ok"] is False and r["error"] == "FULL_SYSTEM_WARP_ONLY"
assert "warp-system" not in calls

print("LINUX_SCOPE_POLICY_TEST=PASS")
