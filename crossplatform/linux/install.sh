#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE"
APP_HOME="$HOME/.local/share/FreeNetHub"
BIN_HOME="$HOME/.local/bin"
DESKTOP_HOME="$HOME/.local/share/applications"
ICON_HOME="$HOME/.local/share/icons/hicolor/scalable/apps"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_HOME="$APP_HOME/backup/$STAMP"

mkdir -p "$APP_HOME" "$BIN_HOME" "$DESKTOP_HOME" "$ICON_HOME"
if [ -f "$APP_HOME/freenet_hub_linux.py" ]; then
  mkdir -p "$BACKUP_HOME"
  for f in freenet_hub_linux.py freenet_hub_linux_gtk.py warp_guard.py recover_warp_remote.sh INSTALL.sha256 INSTALL.json; do
    [ -f "$APP_HOME/$f" ] && cp -a "$APP_HOME/$f" "$BACKUP_HOME/$f"
  done
fi

install -m 0755 "$SRC/freenet_hub_linux.py" "$APP_HOME/freenet_hub_linux.py"
install -m 0755 "$SRC/freenet_hub_linux_gtk.py" "$APP_HOME/freenet_hub_linux_gtk.py"
install -m 0755 "$SRC/warp_guard.py" "$APP_HOME/warp_guard.py"
install -m 0755 "$SRC/recover_warp_remote.sh" "$APP_HOME/recover_warp_remote.sh"
if [ ! -f "$APP_HOME/bridges_obfs4.txt" ]; then
  install -m 0600 "$SRC/bridges_obfs4.txt" "$APP_HOME/bridges_obfs4.txt"
fi
if [ ! -f "$APP_HOME/bridges_snowflake.txt" ]; then
  install -m 0600 "$SRC/bridges_snowflake.txt" "$APP_HOME/bridges_snowflake.txt"
fi
install -m 0644 "$SRC/FreeNetHub.svg" "$ICON_HOME/freenethub.svg"

(
  cd "$APP_HOME"
  sha256sum freenet_hub_linux.py freenet_hub_linux_gtk.py warp_guard.py recover_warp_remote.sh > INSTALL.sha256
)
python3 - "$APP_HOME/INSTALL.json" <<'PY'
import json,pathlib,sys,time
p=pathlib.Path(sys.argv[1])
p.write_text(json.dumps({
  "schema":1,
  "version":"4.2.0-linux.4",
  "release":"PUBLIC_MAIN_R9",
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
chmod 0755 "$BIN_HOME/freenethub" "$BIN_HOME/freenethub-recover"

rm -f "$DESKTOP_HOME/freenethub.desktop"
sed "s|__HOME__|$HOME|g" "$SRC/freenethub.desktop" > "$DESKTOP_HOME/local.freenethub.desktop"
chmod 0644 "$DESKTOP_HOME/local.freenethub.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_HOME" >/dev/null 2>&1 || true
command -v gtk4-update-icon-cache >/dev/null 2>&1 && gtk4-update-icon-cache -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

(cd "$APP_HOME" && sha256sum -c INSTALL.sha256)
echo "Installed FreeNet Hub Linux 4.2.0-linux.4"
echo "No network connection was started."
