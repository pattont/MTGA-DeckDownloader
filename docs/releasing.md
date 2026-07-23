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
uploads all three installers as workflow artifacts. Each artifact contains its
installer and a `SHA256SUMS-<platform>.txt` file. No signing secrets are
required.

Unsigned installers are the current public-release default:

- Windows may display a SmartScreen unknown-publisher warning.
- macOS Gatekeeper may initially block the application because Apple cannot
  verify its developer.
- After trying to open the macOS application, users who have verified the
  download can use **System Settings > Privacy & Security > Open Anyway**.
  Apple's current instructions are at
  <https://support.apple.com/guide/mac-help/open-a-mac-app-from-an-unknown-developer-mh40616/mac>.

Keep this limitation prominent in release notes. Open source availability does
not cause Gatekeeper to trust an unsigned binary.

To verify a macOS download, place the DMG beside its platform checksum file and
run:

```bash
shasum -a 256 -c SHA256SUMS-macos-arm64.txt
```

On Windows, compare the displayed hash with
`SHA256SUMS-windows-x64.txt`:

```powershell
Get-FileHash -Algorithm SHA256 .\MTGA-Deck-Downloader-*-setup.exe
```

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
jobs succeed, it creates a draft GitHub Release containing the installers and a
canonical `SHA256SUMS.txt`. The draft release is marked as unsigned. Inspect the
draft, verify the checksums, and test the downloads before publishing it.
