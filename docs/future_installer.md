### Installable Cross-Platform Distribution Plan (Windows + macOS, terminal app)

#### Summary
Build native executables per OS from the existing Python console app, then publish one-click installers via GitHub Releases.  
Recommended stack for this repo: **PyInstaller + GitHub Actions** (build on each OS, no cross-compiling), with unsigned distribution first.

#### Implementation Changes
- Add packaging foundation:
  - Add a minimal `pyproject.toml` (project metadata + pinned Python version).
  - Add PyInstaller config/spec for `app.py` entrypoint.
  - Add a stable app name and version source (single location used by builds/releases).
- Add platform packaging:
  - Windows: produce standalone `.exe` and wrap it in an installer (`.exe` installer) that creates Start Menu/Desktop shortcuts.
  - macOS: produce a bundled app + DMG for drag-and-drop install.
  - Keep console mode enabled so the current Rich TUI works unchanged.
- Add CI/CD release pipeline:
  - GitHub Actions matrix: `windows-latest` + `macos-latest`.
  - Trigger on version tag (for example `vX.Y.Z`).
  - Build, package, and upload release artifacts automatically.
- Add user-facing install docs:
  - `README` install section with “Download for Windows/macOS” steps.
  - Note expected first-run warnings for unsigned binaries and how to proceed safely.

#### Public Interface / Contract Changes
- No app behavior/API redesign.
- Add one distribution contract:
  - End users launch installed app from OS shortcut/app bundle (not Python command line).
- Optional convenience CLI contract (if included): `mtga-deck-downloader` command alias to same entrypoint.

#### Test Plan
- Build validation:
  - CI artifacts are generated on both Windows/macOS for a tagged release.
- Runtime smoke tests (on each OS artifact):
  - Launch installed app from shortcut/app icon.
  - Select site/format, fetch results, open a deck detail, quit cleanly.
- Packaging checks:
  - Uninstall/reinstall path works.
  - Installer creates expected shortcuts and app metadata.
- Regression checks:
  - Existing terminal navigation flows still work (site switch, format switch, detail view, variant drill-down).

#### Assumptions (Locked)
- **Install UX:** one-click installers.
- **Signing:** unsigned v1 is acceptable (warnings documented).
- **App style:** keep current terminal-based app (no GUI rewrite in this phase).
