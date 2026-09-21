#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP_HOME="$HOME/.local/share/FreeNetHub"
BIN_HOME="$HOME/.local/bin"
DESKTOP_HOME="$HOME/.local/share/applications"
ICON_HOME="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$APP_HOME" "$BIN_HOME" "$DESKTOP_HOME" "$ICON_HOME"
install -m 0755 "$HERE/freenet_hub_linux.py" "$APP_HOME/freenet_hub_linux.py"
install -m 0755 "$HERE/freenet_hub_linux_gtk.py" "$APP_HOME/freenet_hub_linux_gtk.py"
install -m 0755 "$HERE/warp_guard.py" "$APP_HOME/warp_guard.py"
install -m 0755 "$HERE/recover_warp_remote.sh" "$APP_HOME/recover_warp_remote.sh"
if [ ! -f "$APP_HOME/bridges_obfs4.txt" ]; then
  install -m 0600 "$HERE/bridges_obfs4.txt" "$APP_HOME/bridges_obfs4.txt"
fi
install -m 0644 "$HERE/FreeNetHub.svg" "$ICON_HOME/freenethub.svg"
cat > "$BIN_HOME/freenethub" <<'EOF'
#!/usr/bin/env bash
set -e
APP="$HOME/.local/share/FreeNetHub"
export PATH="$APP/runtime/usr/bin:$PATH"
if python3 -c 'import tkinter' >/dev/null 2>&1; then
  exec python3 "$APP/freenet_hub_linux.py"
fi
exec python3 "$APP/freenet_hub_linux_gtk.py"
EOF
cat > "$BIN_HOME/freenethub-recover" <<'EOF'
#!/usr/bin/env bash
exec "$HOME/.local/share/FreeNetHub/recover_warp_remote.sh"
EOF
chmod 0755 "$BIN_HOME/freenethub" "$BIN_HOME/freenethub-recover"
sed "s|__HOME__|$HOME|g" "$HERE/freenethub.desktop" > "$DESKTOP_HOME/freenethub.desktop"
chmod 0644 "$DESKTOP_HOME/freenethub.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$DESKTOP_HOME" >/dev/null 2>&1 || true
echo "Installed FreeNet Hub Linux with Tor direct/obfs4/Snowflake support, WARP anti-lockout guard, and recovery command. Existing private bridge files were preserved. No network connection was started."
