#!/usr/bin/env bash
set -euo pipefail
umask 077
APP_HOME="${1:-$HOME/.local/share/FreeNetHub}"
VERSION="1.2.6"
ASSET="warp-plus_linux-amd64.zip"
URL="https://github.com/bepass-org/warp-plus/releases/download/v1.2.6/$ASSET"
ARCHIVE_SHA256="380d2c8655b33db818adf407c706d52d14c2ab1764e702e91f356a7d7d9c3c98"
BIN_DIR="$APP_HOME/runtime/usr/bin"
BIN="$BIN_DIR/warp-plus"
PIN="$APP_HOME/runtime/warp-plus.pin.json"

if [ -f "$BIN" ] && [ -f "$PIN" ]; then
  if python3 - "$BIN" "$PIN" "$VERSION" <<'PY'
import hashlib,json,pathlib,sys
b=pathlib.Path(sys.argv[1]);p=pathlib.Path(sys.argv[2]);v=sys.argv[3]
try:j=json.loads(p.read_text(encoding="utf-8"))
except Exception:raise SystemExit(1)
h=hashlib.sha256(b.read_bytes()).hexdigest()
raise SystemExit(0 if j.get("version")==v and j.get("binarySha256")==h else 1)
PY
  then
    "$BIN" -h >/dev/null 2>&1
    echo "warp-plus $VERSION already verified"
    exit 0
  fi
fi

for cmd in curl sha256sum unzip python3; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Required command missing: $cmd" >&2; exit 3; }
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fL --retry 2 --connect-timeout 15 --max-time 180 -o "$TMP/$ASSET" "$URL"
printf '%s  %s\n' "$ARCHIVE_SHA256" "$TMP/$ASSET" | sha256sum -c -
unzip -q "$TMP/$ASSET" -d "$TMP/unpacked"
SRC_BIN="$(find "$TMP/unpacked" -type f \( -name 'warp-plus' -o -name 'warp' \) | head -n1)"
[ -n "$SRC_BIN" ] && [ -f "$SRC_BIN" ] || { echo "warp-plus binary missing in archive" >&2; find "$TMP/unpacked" -maxdepth 2 -type f -printf '%P\n' >&2; exit 4; }
mkdir -p "$BIN_DIR"
install -m 0755 "$SRC_BIN" "$BIN"
BIN_SHA256="$(sha256sum "$BIN" | awk '{print $1}')"
mkdir -p "$(dirname "$PIN")"
python3 - "$PIN" "$VERSION" "$ASSET" "$ARCHIVE_SHA256" "$BIN_SHA256" "$URL" <<'PY'
import json,pathlib,sys,time
p=pathlib.Path(sys.argv[1])
p.write_text(json.dumps({
 "schema":1,
 "version":sys.argv[2],
 "asset":sys.argv[3],
 "archiveSha256":sys.argv[4],
 "binarySha256":sys.argv[5],
 "source":sys.argv[6],
 "installedUtc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
},indent=2)+"\n",encoding="utf-8")
PY
chmod 0600 "$PIN"
"$BIN" -h >/dev/null 2>&1
echo "Pinned warp-plus $VERSION installed"
