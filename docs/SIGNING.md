# Signing & release artifacts (P12)

Goal: a double-clickable installer per OS with no "unknown publisher" scare.

## Current state (honest)

The build works and produces real artifacts **today**, unsigned:

```
bash scripts/build_app.sh          # -> src-tauri/target/release/bundle/deb/*.deb
```

`src-tauri/tauri.conf.json` now carries the signing block (P12.1):

```json
"windows": { "certificateThumbprint": null, "digestAlgorithm": "sha256", "timestampUrl": "" },
"macOS": { "signingIdentity": null }
```

`null` = "not configured yet". Signing is therefore **configured but not
activated** until certificates exist. That is the honest G9 state.

## Activate Windows signing

1. Buy an OV/EV code-signing certificate; install it in the Windows cert store.
2. Put its thumbprint into `bundle.windows.certificateThumbprint`.
3. Set `timestampUrl` (e.g. a DigiCert RFC-3161 endpoint).

EV certs sign via a hardware token / cloud HSM — the thumbprint is the only
secret that lives in the repo.

## Activate macOS signing + notarization

```
export APPLE_SIGNING_IDENTITY="Developer ID Application: <you> (TEAMID)"
export APPLE_CERTIFICATE="<base64 .p12>"
export APPLE_ID="you@example.com"
export APPLE_PASSWORD="<app-specific password>"
export APPLE_TEAM_ID="TEAMID"
```

Tauri notarizes automatically when these are present.

## Updater signature (optional)

`createUpdaterArtifacts` is `false`. To enable signed updates:

```
npm run tauri signer generate -- -w ~/.tauri/storm.key
```

then set `createUpdaterArtifacts: true` and export
`TAURI_SIGNING_PRIVATE_KEY` (+ `_PASSWORD`).

## CI

`.github/workflows/release.yml` runs the test suite + live audit, then builds
per-OS on a `v*` tag and attaches artifacts to a **draft** release. Add these
repo secrets to turn signing on:

| Secret | Purpose |
|---|---|
| `TAURI_SIGNING_PRIVATE_KEY` / `_PASSWORD` | updater signature |
| `APPLE_CERTIFICATE` / `APPLE_SIGNING_IDENTITY` | macOS signing/notarization |

No secrets ⇒ the workflow still succeeds; artifacts are simply unsigned.

## Verifying an artifact

```
dpkg-deb -I src-tauri/target/release/bundle/deb/*.deb | head   # metadata sane
ldd --version >/dev/null && sha256sum src-tauri/target/release/bundle/deb/*.deb
```
