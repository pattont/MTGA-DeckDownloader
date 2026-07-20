# Building and Releasing Installers

The repository builds three self-contained artifacts:

- Windows x64 Inno Setup installer.
- macOS Apple Silicon DMG.
- macOS Intel DMG.

End users do not need Python. Installer builds run in
`.github/workflows/build-installers.yml` either manually or when a `v*` tag is
pushed.

## Local macOS Build

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[release]"
python packaging/build_payload.py --version 0.1.0
packaging/macos/build_dmg.sh 0.1.0
```

The DMG is written to `dist/release/`. Local Windows builds use the same
`build_payload.py` command followed by:

```powershell
./packaging/windows/build_installer.ps1 -Version 0.1.0
```

Inno Setup 6 must be installed for a local Windows build.

## Unsigned GitHub Build

Open the `Build installers` workflow in GitHub Actions, choose `Run workflow`,
and enter the version currently declared in `pyproject.toml`. The workflow
uploads all three installers as workflow artifacts. No signing secrets are
required.

## Optional Windows Signing

Add these GitHub Actions secrets:

- `WINDOWS_CERTIFICATE_BASE64`: base64-encoded PFX certificate.
- `WINDOWS_CERTIFICATE_PASSWORD`: PFX password.

Optionally set the `WINDOWS_TIMESTAMP_URL` repository variable. The workflow
signs and verifies both the application executable and final installer when the
certificate secret is present.

## Optional Apple Signing and Notarization

Add these GitHub Actions secrets:

- `APPLE_CERTIFICATE_BASE64`: base64-encoded Developer ID Application P12.
- `APPLE_CERTIFICATE_PASSWORD`: P12 password.
- `MACOS_SIGNING_IDENTITY`: full Developer ID Application identity.
- `APPLE_ID`: Apple ID used for notarization.
- `APPLE_APP_PASSWORD`: app-specific password.
- `APPLE_TEAM_ID`: Apple Developer team identifier.

The macOS jobs import the certificate into a temporary keychain, sign the app
and DMG, submit the DMG to Apple's notary service, staple the ticket, validate
it, and delete the keychain.

## Draft Release

Before tagging, update the version in `pyproject.toml` and run the test suite.
Then create and push the matching tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow validates that the tag and project version match. After all three
jobs succeed, it creates a draft GitHub Release containing the installers and
`SHA256SUMS.txt`. Inspect the draft and test the downloads before publishing it.
