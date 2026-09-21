#!/usr/bin/env bash
set -uo pipefail
echo "[FreeNet Hub] recovering network/control path..."
if command -v warp-cli >/dev/null 2>&1; then
  timeout 20s warp-cli --accept-tos disconnect || true
fi
if command -v systemctl >/dev/null 2>&1 && systemctl --user list-unit-files 2>/dev/null | grep -q '^chatgpt-remote-commander.service'; then
  systemctl --user restart chatgpt-remote-commander.service || true
fi
sleep 2
if command -v curl >/dev/null 2>&1; then
  curl -4 --max-time 10 -fsS https://www.cloudflare.com/cdn-cgi/trace 2>/dev/null | grep -E '^(ip|loc|warp)=' || true
fi
systemctl --user is-active chatgpt-remote-commander.service 2>/dev/null || true
