#!/usr/bin/env bash
set -euo pipefail
umask 077
APP_HOME="${1:-$HOME/.local/share/FreeNetHub}"
VERSION="1.14.2"
ASSET="sing-box-1.14.2-linux-amd64-glibc.tar.gz"
URL="https://github.com/SagerNet/sing-box/releases/download/v1.14.2/$ASSET"
ARCHIVE_SHA256="5c7bc18461827b28d0e5ee7e89d33b276d3ff7c818531104c8e8d26d85b0656e"
BIN_DIR="$APP_HOME/runtime/usr/bin"
BIN="$BIN_DIR/sing-box"
PIN="$APP_HOME/runtime/sing-box.pin.json"

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
    "$BIN" version >/dev/null 2>&1
    echo "sing-box $VERSION already verified"
    exit 0
  fi
fi

for cmd in curl sha256sum tar python3; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Required command missing: $cmd" >&2; exit 3; }
done

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fL --retry 2 --connect-timeout 15 --max-time 180 -o "$TMP/$ASSET" "$URL"
printf '%s  %s\n' "$ARCHIVE_SHA256" "$TMP/$ASSET" | sha256sum -c -
tar -xzf "$TMP/$ASSET" -C "$TMP"
SRC_BIN="$(find "$TMP" -type f -name sing-box -perm -u+x | head -n1)"
[ -n "$SRC_BIN" ] && [ -f "$SRC_BIN" ] || { echo "sing-box binary missing in archive" >&2; exit 4; }
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
"$BIN" version
echo "Pinned sing-box $VERSION installed"
