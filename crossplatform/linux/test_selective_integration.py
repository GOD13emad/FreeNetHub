#!/usr/bin/env python3
"""Scoped selectable provider integration checks: no host network mutation."""
import importlib.util
import pathlib
import sys

from unittest.mock import patch

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("fnh_selective_core", HERE / "freenet_hub_linux_r37.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

apply_calls = []
base = {"mode": "CFON", "provider": "warp-plus", "detail": {"scope": "BROWSER"}}
def settings():
    return {"selectiveDomains": "brave.com\nstripe.com", "customProxy": ""}

def current_session():
    return base.copy()

with patch.object(core.legacy, "session", side_effect=current_session), \
     patch.object(core, "settings", side_effect=settings), \
     patch.object(core, "_active_proxy_for_diagnostics", return_value=("socks5h://127.0.0.1:19414", "CFON")), \
     patch.object(core.selective, "apply", side_effect=lambda dom, port, mode:
                       apply_calls.append((dom, port, mode)) or
                       {"ok": True, "state": "enabled", "domains": ["brave.com", "stripe.com"], "method": mode}), \
     patch.object(core, "connect_method", wraps=core.connect_method) as conn, \
     patch.object(core, "save_settings", return_value={"ok": True}):
    r = core.selective_connect("AUTO")
    assert r["ok"] and r["scope"] == "SELECTIVE"
    assert apply_calls == [("brave.com\nstripe.com", 19414, "CFON")], apply_calls
    # An already active CFON must never be restarted by selective-apply.
    assert not conn.called
    bad = core.selective_connect("DIRECT")
    assert not bad["ok"] and bad["error"] == "SELECTIVE_DIRECT_IS_NOT_TUNNEL"
    bad = core.selective_connect("WARP")
    assert not bad["ok"] and bad["error"] == "SELECTIVE_ACTIVE_PROVIDER_CONFLICT"
    assert len(apply_calls) == 1

# Failing rollback must guard any full-system or scope switch.
with patch.object(core.selective, "status", return_value={"enabled": True}), \
     patch.object(core.selective, "disable", return_value={"ok": False, "error": "SELECTIVE_PROXY_SETTINGS_DRIFT"}):
    for scope in ("SYSTEM", "BROWSER", "CONSOLE"):
        r = core.connect_method("AUTO", scope)
        assert not r["ok"] and r["error"] == "SELECTIVE_DISABLE_REQUIRED", (scope,r)

# The UI must wire selectors, editable domain list and explicit restoration.
ui = (HERE / "freenet_hub_linux_gtk.py").read_text(encoding="utf-8")
for marker in (
    "SELECTIVE", "تونل انتخابی", "self.selective_domains_view",
    "self.apply_selective", "self.disable_selective", "core.selective_connect",
    "core.selective_disable", "self.refresh_selective",
):
    assert marker in ui, marker

assert "core.selective.GOOGLE_DOMAINS" in ui
assert "self.selective_url_entry" in ui
assert "self.selective_google_preset" in ui
assert "self.selective_probe_site" in ui
assert "core.selective_probe_403" in ui
print("LINUX_SELECTIVE_INTEGRATION_TEST_PASS")
