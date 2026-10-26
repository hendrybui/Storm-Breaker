#!/usr/bin/env bash
# Deterministic Tauri v2 build for the Storm-Breaker shell.
#
# Forces ~/.cargo/bin onto PATH so a non-login shell cannot pick /usr/bin/cargo
# (1.75.0, below the Tauri v2 floor of 1.85). Then invokes the Tauri v2 CLI,
# preferring an installed cargo-tauri, else the locally pinned npm CLI.
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export PATH="$HOME/.cargo/bin:$PATH"

if ! command -v cargo >/dev/null 2>&1; then
  echo "ERROR: cargo not found. Install rustup: https://rustup.rs" >&2
  exit 1
fi

cargo_ver="$(cargo --version | awk '{print $2}')"
echo "using cargo $cargo_ver  ($(command -v cargo))"

# Need >= 1.85 for tauri 2.12.x. sort -V puts the lower of {ver, 1.85} first.
if [ "$(printf '%s\n1.85\n' "$cargo_ver" | sort -V | head -1)" != "1.85" ]; then
  echo "ERROR: cargo $cargo_ver is too old for Tauri v2 (need >= 1.85)." >&2
  echo "       Fix: ensure ~/.cargo/bin precedes /usr/bin on PATH (source ~/.cargo/env)." >&2
  exit 1
fi

cd src-tauri

if command -v cargo-tauri >/dev/null 2>&1; then
  exec cargo tauri build "$@"
fi

if [ -x ../node_modules/.bin/tauri ]; then
  exec ../node_modules/.bin/tauri build "$@"
fi

echo "tauri CLI not found locally; installing @tauri-apps/cli (pinned ^2)..."
( cd .. && npm install --no-audit --no-fund )
exec ../node_modules/.bin/tauri build "$@"
