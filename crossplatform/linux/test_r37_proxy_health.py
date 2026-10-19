#!/usr/bin/env python3
"""No-network contract: proxy connectivity and YouTube service probe remain separately visible."""
import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import freenet_hub_linux_r37 as core

ui_path = HERE / "freenet_hub_linux_gtk.py"
ui_code = ui_path.read_text(encoding="utf-8")
ui_tree = ast.parse(ui_code)
formatter = next(
    node for node in ui_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "method_youtube_status")
scope = {}
exec(compile(ast.Module(body=[formatter], type_ignores=[]), str(ui_path), "exec"), scope)
format_yt = scope["method_youtube_status"]

assert format_yt({"ok": True, "youtubeReachable": True}) == "YouTube HTTPS: PASS"
assert format_yt({"ok": True, "youtubeReachable": False}) == "YouTube HTTPS: FAIL"
assert format_yt({"ok": False, "youtubeReachable": False}) == "YouTube HTTPS: FAIL"
for unknown in ({"ok": True}, {"youtubeReachable": None}, {"youtubeReachable": "false"}):
    assert format_yt(unknown) == ""
print("PASS_UI_TYPED_YOUTUBE_PASS_FAIL_AND_UNKNOWN")

method = next(node for node in ast.walk(ui_tree)
              if isinstance(node, ast.FunctionDef) and node.name == "metric_done")
called = [
    node for node in ast.walk(method)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    and node.func.id == "method_youtube_status"]
assert len(called) == 1
assert 'if yt:fmt+=" · "+yt' in ui_code
assert 'vals[3].set_text(state+(" · "+yt if yt else ""))' in ui_code
print("PASS_UI_CARD_AND_COMPARISON_USE_SERVICE_PROBE")

original = {name: getattr(core, name) for name in (
    "settings", "_trace", "_curl", "_warpplus_owner", "_port_open")}
try:
    core.settings = lambda: {
        "pingTimeoutSec": 3, "downloadTimeoutSec": 3, "uploadTimeoutSec": 3}
    core._trace = lambda proxy=None, interface=None, timeout=3: (
        {"exit": 0, "code": "200", "seconds": 0.1},
        {"loc": "AT", "ip": "198.51.100.12", "warp": "off"})
    core._warpplus_owner = lambda mode: {"country": "AT"}
    core._port_open = lambda port: True
    core._curl = lambda *args, **kw: {
        "exit": 7, "code": "000", "seconds": None}

    partial = core._bench("socks5h://127.0.0.1:19414", True)
    assert partial["ok"] and not partial["youtubeReachable"] and partial["error"] == "", partial
    cf = core.warpplus_verify("CFON")
    assert cf["ok"] and not cf["youtubeReachable"], cf
    assert format_yt(cf) == "YouTube HTTPS: FAIL"
    print("PASS_CFON_PROVIDER_HEALTH_REMAINS_SEPARATE_FROM_YOUTUBE_FAILURE")

    direct = core._bench(None, True)
    assert direct["ok"] and not direct["youtubeReachable"], direct
    print("PASS_DIRECT_BASELINE_IS_NOT_MISCLASSIFIED")

    core._curl = lambda *args, **kw: {
        "exit": 0, "code": "204", "seconds": 0.2}
    good = core.warpplus_verify("CFON")
    assert good["ok"] and good["youtubeReachable"], good
    assert format_yt(good) == "YouTube HTTPS: PASS"
    print("PASS_CFON_PROVIDER_AND_YOUTUBE_HEALTHY")

    core._trace = lambda proxy=None, interface=None, timeout=3: (
        {"exit": 7, "code": "000", "seconds": 0.1}, {})
    broken = core._bench("socks5h://127.0.0.1:19414", True)
    assert not broken["ok"] and broken["error"] == "TRACE_FAILED", broken
    print("PASS_CLOUDFLARE_FAILURE_REJECTS_PROXY")
finally:
    for key, value in original.items():
        setattr(core, key, value)
