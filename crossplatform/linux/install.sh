#!/usr/bin/env bash
set -euo pipefail
umask 077
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE"
APP_HOME="$HOME/.local/share/FreeNetHub"
BIN_HOME="$HOME/.local/bin"
DESKTOP_HOME="$HOME/.local/share/applications"
ICON_HOME="$HOME/.local/share/icons/hicolor/scalable/apps"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_HOME="$APP_HOME/backup/$STAMP"
UI_PATH="$APP_HOME/freenet_hub_linux_gtk.py"
RESTART_UI=0

if [ -f "$UI_PATH" ]; then
  RESTART_UI="$(python3 - "$UI_PATH" <<'PY'
from pathlib import Path
import pathlib,os,signal,sys,time
want=str(Path(sys.argv[1]).resolve())
pids=[]
for p in Path('/proc').iterdir():
    if not p.name.isdigit():
        continue
    try:
        args=[x.decode(errors='replace') for x in (p/'cmdline').read_bytes().split(b'\0') if x]
    except Exception:
        continue
    if len(args) >= 2 and pathlib.Path(args[1]).resolve() == pathlib.Path(want):
        pids.append(int(p.name))
for pid in pids:
    try: os.kill(pid,signal.SIGTERM)
    except (ProcessLookupError,PermissionError): pass
end=time.time()+5
while time.time()<end and any(Path(f'/proc/{pid}').exists() for pid in pids):
    time.sleep(.15)
for pid in pids:
    if Path(f'/proc/{pid}').exists():
        try: os.kill(pid,signal.SIGKILL)
        except (ProcessLookupError,PermissionError): pass
print(1 if pids else 0)
PY
)"
fi

for cmd in python3 sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Required command missing: $cmd" >&2; exit 3; }
done
python3 - <<'PY'
import gi
gi.require_version("Gtk","4.0")
gi.require_version("Adw","1")
from gi.repository import Gtk,Adw
PY

mkdir -p "$APP_HOME" "$APP_HOME/evidence" "$APP_HOME/tor" "$BIN_HOME" "$DESKTOP_HOME" "$ICON_HOME"
chmod 0700 "$APP_HOME" "$APP_HOME/evidence" "$APP_HOME/tor"
for f in "$APP_HOME/session.json" "$APP_HOME/console.json" "$APP_HOME/bridges_obfs4.txt" "$APP_HOME/bridges_snowflake.txt"; do
  [ -f "$f" ] && chmod 0600 "$f"
done
find "$APP_HOME/evidence" "$APP_HOME/tor" -type f -exec chmod 0600 {} + 2>/dev/null || true
find "$APP_HOME" -maxdepth 1 -type f \( -name 'warp_guard_*.log' -o -name 'warp_keep_*.ok' \) -exec chmod 0600 {} + 2>/dev/null || true
if [ -f "$APP_HOME/freenet_hub_linux.py" ]; then
  mkdir -p "$BACKUP_HOME"
  for f in freenet_hub_linux.py freenet_hub_linux_gtk.py warp_guard.py recover_warp_remote.sh uninstall.sh INSTALL.sha256 INSTALL.json; do
    [ -f "$APP_HOME/$f" ] && cp -a "$APP_HOME/$f" "$BACKUP_HOME/$f"
  done
fi

install -m 0755 "$SRC/freenet_hub_linux.py" "$APP_HOME/freenet_hub_linux.py"
install -m 0755 "$SRC/freenet_hub_linux_gtk.py" "$APP_HOME/freenet_hub_linux_gtk.py"
install -m 0755 "$SRC/warp_guard.py" "$APP_HOME/warp_guard.py"
install -m 0755 "$SRC/recover_warp_remote.sh" "$APP_HOME/recover_warp_remote.sh"
install -m 0755 "$SRC/uninstall.sh" "$APP_HOME/uninstall.sh"
if [ ! -f "$APP_HOME/bridges_obfs4.txt" ]; then
  install -m 0600 "$SRC/bridges_obfs4.txt" "$APP_HOME/bridges_obfs4.txt"
fi
if [ ! -f "$APP_HOME/bridges_snowflake.txt" ]; then
  install -m 0600 "$SRC/bridges_snowflake.txt" "$APP_HOME/bridges_snowflake.txt"
fi
install -m 0644 "$SRC/FreeNetHub.svg" "$ICON_HOME/freenethub.svg"

(
  cd "$APP_HOME"
  sha256sum freenet_hub_linux.py freenet_hub_linux_gtk.py warp_guard.py recover_warp_remote.sh uninstall.sh > INSTALL.sha256
)
python3 - "$APP_HOME/INSTALL.json" <<'PY'
import json,pathlib,sys,time
p=pathlib.Path(sys.argv[1])
p.write_text(json.dumps({
  "schema":1,
  "version":"4.2.0-linux.7",
  "release":"LINUX_4.2.0_R7",
  "installed_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
  "network_mutation_on_install":False,
  "integrity_manifest":"INSTALL.sha256"
},indent=2)+"\n",encoding="utf-8")
PY

cat > "$BIN_HOME/freenethub" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
APP="$HOME/.local/share/FreeNetHub"
export PATH="$APP/runtime/usr/bin:$PATH"
if ! (cd "$APP" && sha256sum -c INSTALL.sha256 >/dev/null 2>&1); then
  command -v notify-send >/dev/null 2>&1 && notify-send --urgency=critical "FreeNet Hub" "Integrity check failed. Reinstall the accepted FreeNet Hub Linux release."
  exit 70
fi
exec python3 "$APP/freenet_hub_linux_gtk.py"
EOF

cat > "$BIN_HOME/freenethub-recover" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/FreeNetHub/recover_warp_remote.sh"
EOF

cat > "$BIN_HOME/freenethub-uninstall" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/FreeNetHub/uninstall.sh"
EOF
chmod 0755 "$BIN_HOME/freenethub" "$BIN_HOME/freenethub-recover" "$BIN_HOME/freenethub-uninstall"

rm -f "$DESKTOP_HOME/freenethub.desktop"
sed "s|__HOME__|$HOME|g" "$SRC/freenethub.desktop" > "$DESKTOP_HOME/local.freenethub.desktop"
chmod 0644 "$DESKTOP_HOME/local.freenethub.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_HOME" >/dev/null 2>&1 || true
command -v gtk4-update-icon-cache >/dev/null 2>&1 && gtk4-update-icon-cache -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

(cd "$APP_HOME" && sha256sum -c INSTALL.sha256)
if [ "$RESTART_UI" = "1" ] && command -v gtk-launch >/dev/null 2>&1 && [ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]; then
  gtk-launch local.freenethub >/dev/null 2>&1 &
fi
echo "Installed FreeNet Hub Linux 4.2.0-linux.7"
echo "No network connection was started."
