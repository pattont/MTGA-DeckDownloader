# Public Installer and Release Plan

Last reviewed: 2026-07-16

## Outcome

Ship the existing Rich terminal application as signed, self-contained downloads
that do not require Python:

| Platform | First public artifact | Supported systems |
| --- | --- | --- |
| Windows | `MTGA-Deck-Downloader-<version>-windows-x64-setup.exe` | Windows 10 22H2 and Windows 11, x64 |
| macOS Apple Silicon | `MTGA-Deck-Downloader-<version>-macos-arm64.dmg` | macOS 13 or later |
| macOS Intel | `MTGA-Deck-Downloader-<version>-macos-x64.dmg` | macOS 13 or later |

GitHub Releases will be the initial download and update channel. The first
public candidate should be `v0.1.0-beta.1`; `v0.1.0` becomes the first general
release after the clean-machine acceptance tests pass.

## Decisions

- Keep the terminal UI. A GUI rewrite is not part of the installer project.
- Use Python 3.12 for release builds until a deliberate toolchain upgrade.
- Use PyInstaller in one-folder mode, built natively on each target
  architecture. One-folder mode avoids extracting the whole application on
  every launch and is easier to sign, inspect, and troubleshoot than one-file
  mode.
- Build Windows x64, macOS arm64, and macOS x64 separately. Do not advertise a
  universal macOS binary until all bundled dependencies have been verified as
  universal.
- Use Inno Setup for the Windows per-user installer.
- Use a signed `.app` inside a DMG for macOS. A small native launcher will open
  the bundled console executable in Terminal; simply wrapping the Python entry
  point as a windowed PyInstaller app would hide stdin/stdout and make the TUI
  unusable.
- Sign and notarize the stable public artifacts. Unsigned builds are acceptable
  only for private development or a clearly marked pre-release. This replaces
  the old assumption that unsigned distribution was good enough for v1.
- Do not add a self-updater in the first release. Upgrades replace the installed
  application while preserving per-user configuration.
- Do not require administrator privileges. Both installers are per-user or use
  the normal `/Applications` drag-and-drop flow.

## Current Repository Gaps

These are release blockers, not optional polish:

1. `app.py` modifies `sys.path` instead of using an installed package entry
   point. Packaging needs a normal `mtga_deck_downloader.__main__` entry point.
2. Providers are found with `pkgutil` and imported dynamically. PyInstaller
   cannot reliably infer those imports, so the spec must explicitly collect all
   `mtga_deck_downloader.providers` submodules.
3. `config.py` assumes `config.json` lives in a source checkout. Installed
   applications need immutable bundled defaults and an optional per-user config
   path.
4. The missing-dependency help in `ui.py` points at `requirements.txt` and a
   repository virtual environment. A frozen app must show packaged-app
   diagnostics instead of pip instructions.
5. There is no project metadata, version source, package lock, application
   icon, license, security policy, third-party notice, CI workflow, or release
   process.
6. macOS cannot launch this TUI correctly from Finder without a launcher that
   deliberately opens Terminal.

## Target Application Contract

Use the following stable identities throughout packaging:

- Display name: `MTGA Deck Downloader`
- Command/executable name: `mtga-deck-downloader`
- macOS bundle identifier: `io.github.pattont.mtga-deck-downloader`
- Windows installer `AppId`: one generated GUID, committed once and never
  changed
- Version: PEP 440/SemVer-compatible value in `pyproject.toml`
- Release tag: exactly `v<project-version>`

The signing publisher must be the verified individual or organization name,
not an invented product name. Record that value after the Apple and Microsoft
identity enrollments are complete.

Installed configuration will follow this lookup order:

1. An explicit path supplied for development/testing.
2. A per-user `config.json` in the platform application-data directory.
3. Read-only defaults bundled in the Python package.

Suggested user paths are `%APPDATA%\MTGA Deck Downloader\config.json` on
Windows and `~/Library/Application Support/MTGA Deck Downloader/config.json` on
macOS. Uninstalling or replacing the app must not silently delete this file.

The executable also needs non-interactive `--version` and `--diagnose` commands.
`--diagnose` should validate bundled resources, load every provider, report the
config path, and exit without making network requests. CI will use this as the
packaged-app smoke test.

## Implementation Phases

### Phase 0: Accounts, ownership, and release policy

Owner actions can run in parallel with code work, but signing cannot finish
without them.

- Choose the legal/publisher identity used for both platforms.
- Enroll in the Apple Developer Program and create a Developer ID Application
  certificate. Apple lists Developer ID and notarization as program benefits;
  enrollment is currently USD 99 per year.
- Apply for Microsoft Artifact Signing Public Trust and complete its identity
  validation. Use a conventional OV code-signing certificate only if Artifact
  Signing is unavailable for the publisher or region. Do not buy EV solely to
  bypass SmartScreen; Microsoft states that EV no longer receives automatic
  first-download reputation.
- Choose and add the repository license. The repository is already public but
  GitHub currently reports no license.
- Create original `.ico` and `.icns` assets that do not reuse protected Wizards
  of the Coast artwork or symbols. Retain the existing non-affiliation notice
  and review product naming/trademark language before publishing.
- Decide whether creator customization is a supported public feature. The plan
  preserves it through per-user config, but does not add a config editor.

Exit gate: publisher identity, signing-account path, license choice, and owned
icon source are recorded.

### Phase 1: Make the Python application packageable

Planned changes:

- Add `pyproject.toml` with project metadata, Python `>=3.10`, runtime
  dependencies, version, and the `mtga-deck-downloader` console script.
- Add `src/mtga_deck_downloader/__main__.py`; keep `app.py` as a compatibility
  shim for existing contributor commands.
- Read the installed version with `importlib.metadata` and implement
  `--version` and `--diagnose`.
- Move bundled defaults into package data and resolve user config through a
  small platform-path helper. Refactor `load_config()` to accept an explicit
  path so tests do not mutate module globals.
- Make missing-dependency messaging aware of frozen builds.
- Add a pinned release/build lock containing PyInstaller and build tools.
  Runtime ranges can remain in `pyproject.toml`; release builds must install the
  exact reviewed lock.
- Add focused tests for entry-point arguments, config lookup order, frozen-mode
  diagnostics, version reporting, and provider discovery.

Exit gate: source and editable-package execution behave identically, the full
unit suite passes, and `--diagnose` loads every provider offline.

### Phase 2: Reproducible PyInstaller payloads

Add `packaging/pyinstaller/mtga_deck_downloader.spec` and a single build command
used locally and in CI. The spec must:

- Produce a console-enabled one-folder payload.
- Collect every provider submodule because discovery is dynamic.
- Include package defaults, dependency metadata needed by
  `importlib.metadata`, CA certificates, and any Cloudscraper data discovered by
  analysis.
- Set product/version metadata and platform icons.
- Fail the build on missing imports or unexpected analysis warnings maintained
  in an allowlist.
- Avoid UPX so signatures and antivirus analysis see conventional binaries.

Run the payload directly on each build host, execute `--version`, execute
`--diagnose`, then pipe `q` to a normal launch and require exit code zero.

Exit gate: three unsigned payloads pass the offline smoke tests and provider
discovery includes Magic.gg, Untapped, Aetherhub, Moxfield, and TCGPlayer.

### Phase 3: Windows installer

Add `packaging/windows/installer.iss` with these behaviors:

- Install the one-folder payload under
  `%LOCALAPPDATA%\Programs\MTGA Deck Downloader` without elevation.
- Create a Start Menu shortcut; offer a desktop shortcut but leave it unchecked
  by default.
- Preserve the fixed Inno `AppId` so upgrades replace the previous version.
- Include Add/Remove Programs metadata, icon, version, project URL, publisher,
  and a working uninstaller.
- Launch the console-enabled executable normally so a terminal window opens.
- Never install Python, modify `PATH`, or write application data into the install
  directory.

Sign the inner application executable first, configure Inno Setup to sign its
uninstaller, and sign the final setup executable last. Use RFC 3161 timestamping
and verify signatures with `signtool verify /pa /all /v`.

Exit gate: install, upgrade, launch, uninstall, and reinstall pass from a clean
standard Windows account. Uninstall removes program files and shortcuts but
preserves user config.

### Phase 4: macOS app and DMG

Create a native launcher under `packaging/macos/` with this layout:

```text
MTGA Deck Downloader.app/
  Contents/
    Info.plist
    MacOS/MTGA Deck Downloader       # small native launcher
    Resources/
      app/                            # PyInstaller one-folder payload
      launch.command                 # resolves its own path and execs the TUI
      MTGADeckDownloader.icns
```

The launcher must use the system Terminal without Apple Events automation. A
feasibility spike is the first macOS task: double-click the app, confirm a new
Terminal window receives stdin, run the TUI, quit, and verify paths containing
spaces. If that experience is not acceptable, stop and make a product decision
about a GUI before building the DMG.

For each architecture:

1. Build the PyInstaller payload natively.
2. Compile the launcher and assemble the `.app`.
3. Sign nested Mach-O files and the outer app with Developer ID Application,
   hardened runtime, secure timestamp, and only the entitlements proven
   necessary.
4. Verify with `codesign --verify --deep --strict --verbose=2` and
   `spctl --assess --type execute --verbose=4`.
5. Submit the app for notarization with `xcrun notarytool`, inspect the log even
   on success, and staple the ticket.
6. Create a simple DMG with the app and an `/Applications` link, sign it, submit
   it for notarization, staple it, and validate it.

Exit gate: a quarantined download mounts, drags to Applications, opens by normal
double-click without a Gatekeeper workaround, accepts keyboard input, accesses
the clipboard through `pbcopy`, and runs on both Apple Silicon and Intel test
machines.

### Phase 5: CI and release automation

Add three workflows:

1. `ci.yml` runs the unit suite on pull requests and main, including Windows and
   macOS jobs for packaging-sensitive changes.
2. `package.yml` supports manual unsigned release-candidate builds and uploads
   short-lived workflow artifacts. It never receives signing credentials.
3. `release.yml` runs only for protected `v*` tags after a manual
   `release-signing` environment approval. It checks that the tag matches
   `pyproject.toml`, builds on `windows-latest`, an arm64 macOS runner, and an
   Intel macOS runner, signs, notarizes, and creates a draft GitHub Release.

Release-workflow requirements:

- Use least-privilege `GITHUB_TOKEN` permissions and OIDC for Microsoft Artifact
  Signing where available.
- Store Apple certificate material and notarization credentials only in the
  protected GitHub environment; import the certificate into an ephemeral
  keychain and delete the keychain at job end.
- Pin third-party GitHub Actions to reviewed commit SHAs.
- Pass signed artifacts between jobs with GitHub workflow artifacts, then have
  one final job assemble the release.
- Generate `SHA256SUMS.txt`, an SPDX or CycloneDX SBOM, and GitHub artifact
  attestations for each installer.
- Create the GitHub Release as a draft, attach every asset and generated release
  notes, and publish only after manual acceptance. Enable immutable releases and
  publish only after all assets are present.
- Never overwrite an installer for an existing version or move a published tag.

Expected release assets:

```text
MTGA-Deck-Downloader-0.1.0-windows-x64-setup.exe
MTGA-Deck-Downloader-0.1.0-macos-arm64.dmg
MTGA-Deck-Downloader-0.1.0-macos-x64.dmg
MTGA-Deck-Downloader-0.1.0-sbom.spdx.json
SHA256SUMS.txt
```

Exit gate: a beta tag produces a complete draft release without any local build
steps, and all signatures, notarization tickets, hashes, and attestations verify.

### Phase 6: Release documentation and public beta

- Add platform-specific installation, upgrade, uninstall, config, and
  troubleshooting instructions to the README or `docs/install.md`.
- Explain that a newly signed Windows build can still receive a SmartScreen
  reputation warning; show users how to verify the publisher and SHA-256 hash.
  Do not normalize bypassing an unsigned or unknown-publisher warning.
- Add `SECURITY.md`, `THIRD_PARTY_NOTICES.md`, release notes, and a concise
  privacy/network note explaining that the app contacts the selected third-party
  deck sites and does not intentionally collect telemetry.
- Review each provider's public-access terms and document that source contracts
  may change. Remove or disable any integration that cannot be distributed
  responsibly.
- Publish `v0.1.0-beta.1` as a GitHub pre-release to a small set of testers.
- Triage installer failures separately from provider/scraper failures.

Exit gate: at least one clean-machine test passes for every artifact and no
release-blocking issue remains.

## Acceptance Matrix

Automated checks run for every release candidate:

- Full unit test suite passes.
- `--version` exactly matches the release tag.
- `--diagnose` reports all five providers and no missing packaged resources.
- A normal console launch accepts `q` and exits zero.
- Windows Authenticode signatures and macOS code signatures verify.
- Apple notarization and stapling validate.
- Installer SHA-256 values match `SHA256SUMS.txt`.
- SBOM and GitHub provenance attestations are present.
- No signing credential or temporary keychain is included in an artifact.

Manual clean-machine checks are required on:

- Windows 10 22H2 x64 standard account.
- Current Windows 11 x64 standard account with SmartScreen enabled.
- macOS 13+ Apple Silicon with the DMG carrying download quarantine.
- macOS 13+ Intel with the DMG carrying download quarantine.

For each machine, test install, first launch, all provider menus, at least one
successful live deck fetch, deck hydration, clipboard copy, quit, upgrade over
the previous beta, uninstall, and preservation of user config. Also test paths
and usernames containing spaces and non-ASCII characters.

## Public Release Gate

Publish `v0.1.0` only when all of the following are true:

- [ ] License, original icon source, trademark disclaimer, privacy/network note,
      security policy, and third-party notices are committed.
- [ ] The version and tag match and the release commit is reviewed.
- [ ] Windows installer and both macOS DMGs are signed by the expected publisher.
- [ ] Both macOS DMGs are notarized and stapled.
- [ ] Every automated and clean-machine acceptance check passes.
- [ ] A draft GitHub Release contains all installers, checksums, SBOM, release
      notes, and attestations.
- [ ] Install, upgrade, uninstall, config, and warning documentation is live.
- [ ] Known provider failures are documented and none prevents basic use.
- [ ] The draft release is approved, then published without replacing assets.

## Explicitly Deferred

- Microsoft Store and Mac App Store submission.
- Automatic/background updates.
- A graphical UI or embedded terminal emulator.
- Windows arm64 and Linux installers.
- Machine-wide installation and managed-enterprise deployment.
- Crash reporting or analytics.

## Estimate and Critical Path

The engineering work is approximately 6-9 focused developer days:

- Package/runtime refactor and tests: 1-2 days.
- PyInstaller spec and three payloads: 1-1.5 days.
- Windows installer and signing: 1 day.
- macOS launcher, DMGs, signing, and notarization: 1.5-2.5 days.
- CI, release security, docs, and clean-machine QA: 1.5-2 days.

Identity verification, certificate issuance, access to clean Intel/Apple Silicon
test machines, and provider-policy review are external lead-time risks. Start
the Apple and Microsoft enrollments before implementation. The macOS launcher
feasibility spike is the technical critical path because the product is an
interactive terminal app launched from Finder.

## Reference Documentation

- [PyInstaller usage and platform builds](https://pyinstaller.org/en/stable/usage.html)
- [PyInstaller run-time resources](https://pyinstaller.org/en/stable/runtime-information.html)
- [Apple notarization requirements](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution)
- [Apple custom notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow)
- [Apple Developer Program membership](https://developer.apple.com/support/compare-memberships/)
- [Microsoft SmartScreen reputation guidance](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [Microsoft Artifact Signing](https://learn.microsoft.com/en-us/azure/artifact-signing/)
- [Microsoft SignTool](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/signtool)
- [Inno Setup command-line and signing documentation](https://jrsoftware.org/ishelp/)
- [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
