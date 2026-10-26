#!/usr/bin/env bash
# P9.2/P9.6 build: PyInstaller onedir sidecar -> src-tauri/sidecar/
# (the Tauri bundle ships this directory as a resource; the Rust shell
#  spawns resources/sidecar/storm-breaker-backend/storm-breaker-backend).
set -eu
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "[1/2] pyinstaller build"
pyinstaller --noconfirm --clean storm-backend.spec

echo "[2/2] staging into src-tauri/sidecar/"
rm -rf src-tauri/sidecar/storm-breaker-backend
mkdir -p src-tauri/sidecar
cp -r dist/storm-breaker-backend src-tauri/sidecar/storm-breaker-backend

echo "sidecar staged: src-tauri/sidecar/storm-breaker-backend/"
echo "next: cd src-tauri && cargo tauri build   (or cargo build)"
