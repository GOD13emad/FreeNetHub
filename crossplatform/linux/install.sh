#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP_HOME="$HOME/.local/share/FreeNetHub"
BIN_HOME="$HOME/.local/bin"
DESKTOP_HOME="$HOME/.local/share/applications"
ICON_HOME="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$APP_HOME" "$BIN_HOME" "$DESKTOP_HOME" "$ICON_HOME"
install -m 0755 "$HERE/freenet_hub_linux.py" "$APP_HOME/freenet_hub_linux.py"
install -m 0644 "$HERE/FreeNetHub.svg" "$ICON_HOME/freenethub.svg"
printf '%s\n' '#!/usr/bin/env bash' 'exec python3 "$HOME/.local/share/FreeNetHub/freenet_hub_linux.py"' > "$BIN_HOME/freenethub"
chmod 0755 "$BIN_HOME/freenethub"
sed "s|__HOME__|$HOME|g" "$HERE/freenethub.desktop" > "$DESKTOP_HOME/freenethub.desktop"
echo "Installed UI only. No provider package or network setting was changed."
