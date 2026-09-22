#!/usr/bin/env bash
set -euo pipefail
if ! command -v pkexec >/dev/null 2>&1; then
  echo "pkexec is required for the official system WARP package." >&2
  exit 2
fi
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
cat > "$tmp" <<'SH'
set -euo pipefail
KEY=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
LIST=/etc/apt/sources.list.d/cloudflare-client.list
. /etc/os-release
CODENAME="${VERSION_CODENAME:-}"
[ -n "$CODENAME" ] || { echo "VERSION_CODENAME missing in /etc/os-release" >&2; exit 3; }
keytmp="$(mktemp)"
trap 'rm -f "$keytmp"' EXIT
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg -o "$keytmp"
gpg --yes --dearmor --output "$KEY" "$keytmp"
printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ %s main\n' "$CODENAME" > "$LIST"
apt-get update
apt-get install -y cloudflare-warp
systemctl enable --now warp-svc
SH
pkexec /bin/bash "$tmp"
warp-cli --accept-tos --version
