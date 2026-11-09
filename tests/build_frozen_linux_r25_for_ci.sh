#!/usr/bin/env bash
# Reconstruct the historical SHA-pinned R25 preview from its accepted source.
# Never generate an old accepted R25 artifact from a moving PR's Linux code.
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
frozen='d9ae15b7333f86e2728dcfee371a3f87af8794b7'
expected_sha='4F035E158F9580F1ACA0554ED1FAE6DC45F6D74FD02F686744433CF35E75AD22'
name='FreeNetHub_4.2.0_Linux_R25.zip'
out_dir="${FNH_R25_OUTPUT_DIR:-$repo/delivery/github_v4.2.0}"
test "$(git -C "$repo" cat-file -t "$frozen")" = commit
mkdir -p "$out_dir"
scratch="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/fnh-frozen-r25.XXXXXX")"
rmdir "$scratch"
cleanup() {
  if [ -e "$scratch" ]; then
    git -C "$repo" worktree remove --force "$scratch" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
git -C "$repo" worktree add --detach "$scratch" "$frozen" >/dev/null
test "$(git -C "$scratch" rev-parse HEAD)" = "$frozen"
PYTHONDONTWRITEBYTECODE=1 python3 "$scratch/tests/build_linux_r25_package.py"
produced="$scratch/delivery/github_v4.2.0/$name"
test -s "$produced"
printf '%s  %s\n' "$expected_sha" "$produced" | sha256sum -c -
destination="$out_dir/$name"
if [ -e "$destination" ]; then
  test -f "$destination" && ! test -L "$destination"
  printf '%s  %s\n' "$expected_sha" "$destination" | sha256sum -c -
else
  cp --no-clobber "$produced" "$destination"
fi
printf '%s  %s\n' "$expected_sha" "$destination" | sha256sum -c -
git -C "$repo" worktree remove --force "$scratch" >/dev/null
trap - EXIT
echo "FNH_FROZEN_R25_PREVIEW_EXACT_SHA_PASS"
