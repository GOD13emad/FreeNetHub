#!/usr/bin/env python3
"""No network mutation: Cloudflare WARP owner agreement must not be accepted by FNH."""
import importlib.util
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
entry = root / "freenet_hub_linux.py"
spec = importlib.util.spec_from_file_location("fnh_tos_policy", entry)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

calls = []
m.executable = lambda name: "/usr/bin/warp-cli" if name == "warp-cli" else None
def fake_run(args, timeout=20, env=None):
    calls.append(args)
    assert args[0] == "/usr/bin/warp-cli"
    assert "--accept-tos" not in args, args
    if args[1] == "status":
        return subprocess.CompletedProcess(args, 1, "", "Please accept the WARP Terms of Service by running this command in a TTY or by passing the --accept-tos flag.")
    raise AssertionError("Unexpected CLI mutation or registration before consent: "+repr(args))
m.run = fake_run
m.ensure_warp_registration = lambda: (_ for _ in ()).throw(AssertionError("registration called"))
m.start_warp_guard = lambda: (_ for _ in ()).throw(AssertionError("guard called"))
status = m.warp_status()
assert status["requires_owner_tos"] and not status["ok"] and not status["connected"], status
result = m.warp_connect_safe()
assert result["stage"] == "owner_consent" and result["error"] == "WARP_TOS_OWNER_ACTION_REQUIRED", result
assert calls == [["/usr/bin/warp-cli","status"],["/usr/bin/warp-cli","status"]], calls

for name in ("warp_guard.py","recover_warp_remote.sh","install_warp_official.sh"):
    contents = (root / name).read_text(encoding="utf8")
    assert "--accept-tos" not in contents, name
for name in ("warp_status", "ensure_warp_registration", "warp_connect_safe", "warp_disconnect"):
    assert callable(getattr(m, name))

print("LINUX_WARP_TOS_OWNER_CONSENT_TEST=PASS")
