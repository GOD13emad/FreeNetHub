#!/usr/bin/env bash
set -euo pipefail

APP_HOME="$HOME/.local/share/FreeNetHub"
BIN_HOME="$HOME/.local/bin"
DESKTOP_HOME="$HOME/.local/share/applications"
ICON="$HOME/.local/share/icons/hicolor/scalable/apps/freenethub.svg"

if [ -f "$APP_HOME/tailnet_cfon_gateway.py" ] || [ -e "$APP_HOME/tailnet_cfon_gateway.json" ]; then
  if [ ! -f "$APP_HOME/tailnet_cfon_gateway.py" ]; then
    echo "FNH_TAILNET_OWNER_MODULE_MISSING: cannot prove safe cleanup" >&2
    exit 20
  fi
  python3 - "$APP_HOME/tailnet_cfon_gateway.py" "$APP_HOME" <<'TAILUN'
import importlib.util,pathlib,sys,json
app=pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0,str(app))
spec=importlib.util.spec_from_file_location("fnh_tailnet_owner_uninstall",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.stop()
if not r.get("ok"):raise SystemExit("FNH_TAILNET_STOP_REQUIRED "+json.dumps(r))
# Private owner/installed unit cleanup only after positive stop verification.
if m.UNIT.exists():
    if m.UNIT.is_symlink() or not m.UNIT.read_text(encoding="utf-8").startswith(m.MARKER):
        raise SystemExit("FNH_TAILNET_FOREIGN_UNIT_REFUSED")
    m.UNIT.unlink()
    import subprocess
    subprocess.run(["systemctl","--user","daemon-reload"],check=True,timeout=8)
if m.OWNER.is_file():
    if not m._load().get("enabled") is False:
        raise SystemExit("FNH_TAILNET_OWNER_STILL_ENABLED")
    m.OWNER.unlink()
TAILUN
fi
# Stop only the project's own isolated peer Firefox; no unrelated profile.
if [ -f "$APP_HOME/tailnet_client_browser.py" ]; then
  python3 - "$APP_HOME" <<'CLIENTUN'
import pathlib,sys,json
app=pathlib.Path(sys.argv[1])
sys.path.insert(0,str(app))
import tailnet_client_browser as helper
result=helper.stop_browser()
if not result.get("ok"):
    print("TAILNET_CLIENT_BROWSER_STOP_REQUIRED",json.dumps(result),file=sys.stderr)
    raise SystemExit(20)
CLIENTUN
fi
if [ -f "$APP_HOME/selective_tunnel.py" ]; then
  python3 - "$APP_HOME/selective_tunnel.py" <<'SELECTIVEPY'
import importlib.util,sys
spec=importlib.util.spec_from_file_location("fnh_selective_uninstall",sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
r=m.disable()
if not r.get("ok"):
    print("SELECTIVE_ROLLBACK_REQUIRED_BEFORE_UNINSTALL:",r,file=sys.stderr)
    raise SystemExit(20)
SELECTIVEPY
fi
if [ -f "$APP_HOME/freenet_hub_linux.py" ]; then
  python3 - "$APP_HOME/freenet_hub_linux.py" <<'PY'
import importlib.util,json,pathlib,sys
p=pathlib.Path(sys.argv[1])
spec=importlib.util.spec_from_file_location("freenethub_uninstall_core",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
# Upgrade-safe ownership migration is allowed only when the legacy profile
# fingerprint (including the stored PSK) proves it is the prior FreeNet Hub profile.
try:
    m.migrate_legacy_console_profile(m.load_json(m.CONSOLE, {}))
except Exception:
    pass
r=m.stop_all()
print(json.dumps(r))
if not r.get("ok"):
    raise SystemExit(20)
PY
fi

python3 - "$APP_HOME" <<'PY'
import json,os,pathlib,signal,subprocess,sys,time
app=pathlib.Path(sys.argv[1])
ui=str((app/"freenet_hub_linux_gtk.py").resolve())

# Stop only the exact current-user UI process.
for proc in pathlib.Path("/proc").iterdir():
    if not proc.name.isdigit():
        continue
    try:
        args=[x.decode(errors="replace") for x in (proc/"cmdline").read_bytes().split(b"\0") if x]
    except Exception:
        continue
    if ui in args:
        try: os.kill(int(proc.name),signal.SIGTERM)
        except (ProcessLookupError,PermissionError): pass

# Delete only the exact NetworkManager profile UUID recorded as project-owned.
cfg_path=app/"console.json"
try:
    cfg=json.loads(cfg_path.read_text(encoding="utf-8"))
except Exception:
    cfg={}
uuid=str(cfg.get("connection_uuid") or "")
if cfg.get("created_by")=="FreeNet Hub" and cfg.get("connection_name")=="FreeNetHub-Console" and uuid:
    try:
        p=subprocess.run(["nmcli","-g","connection.id","connection","show","uuid",uuid],
                         stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=8)
        if p.returncode==0 and p.stdout.strip()=="FreeNetHub-Console":
            subprocess.run(["nmcli","connection","down","uuid",uuid],
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
            d=subprocess.run(["nmcli","connection","delete","uuid",uuid],
                             stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=15)
            if d.returncode!=0:
                raise SystemExit("owned console profile cleanup failed: "+d.stdout.strip())
    except FileNotFoundError:
        pass
PY

rm -f "$BIN_HOME/freenethub" "$BIN_HOME/freenethub-recover" "$BIN_HOME/freenethub-uninstall"
rm -f "$DESKTOP_HOME/local.freenethub.desktop" "$DESKTOP_HOME/freenethub.desktop"
rm -f "$ICON"
rm -f   "$APP_HOME/freenet_hub_linux.py"   "$APP_HOME/freenet_hub_linux_r37.py"   "$APP_HOME/freenet_hub_linux_gtk.py"   "$APP_HOME/nodehub_shared.py"   "$APP_HOME/selective_tunnel.py"   "$APP_HOME/tailnet_cfon_gateway.py"   "$APP_HOME/tailnet_client_browser.py"   "$APP_HOME/warp_guard.py"   "$APP_HOME/recover_warp_remote.sh"   "$APP_HOME/uninstall.sh"   "$APP_HOME/INSTALL.sha256"   "$APP_HOME/INSTALL.json"

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_HOME" >/dev/null 2>&1 || true
command -v gtk4-update-icon-cache >/dev/null 2>&1 && gtk4-update-icon-cache -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

echo "FreeNet Hub Linux application files removed."
echo "Private runtime state/evidence/bridge files were preserved under $APP_HOME."
