#!/bin/bash

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 2
fi

VERSION="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PAYLOAD_DIR="$PROJECT_ROOT/dist/pyinstaller/mtga-deck-downloader"
RELEASE_DIR="$PROJECT_ROOT/dist/release"

case "$(uname -m)" in
  arm64) ARCH="arm64" ;;
  x86_64) ARCH="x64" ;;
  *) echo "Unsupported macOS architecture: $(uname -m)" >&2; exit 1 ;;
esac

if [[ ! -x "$PAYLOAD_DIR/mtga-deck-downloader" ]]; then
  echo "PyInstaller payload not found: $PAYLOAD_DIR" >&2
  exit 1
fi

BUILD_DIR="$PROJECT_ROOT/build/macos-$ARCH"
APP_PATH="$BUILD_DIR/dmg/MTGA Deck Downloader.app"
CONTENTS="$APP_PATH/Contents"
DMG_PATH="$RELEASE_DIR/MTGA-Deck-Downloader-$VERSION-macos-$ARCH.dmg"

rm -rf "$BUILD_DIR"
mkdir -p "$CONTENTS/MacOS" "$CONTENTS/Resources" "$RELEASE_DIR"
ditto "$PAYLOAD_DIR" "$CONTENTS/Resources/app"
cp "$SCRIPT_DIR/Info.plist" "$CONTENTS/Info.plist"
cp "$SCRIPT_DIR/launch.command" "$CONTENTS/Resources/launch.command"
cp "$PROJECT_ROOT/build/icons/app.icns" "$CONTENTS/Resources/MTGADeckDownloader.icns"
chmod +x "$CONTENTS/Resources/launch.command"

swiftc "$SCRIPT_DIR/Launcher.swift" -o "$CONTENTS/MacOS/MTGA Deck Downloader"
plutil -replace CFBundleShortVersionString -string "$VERSION" "$CONTENTS/Info.plist"
plutil -replace CFBundleVersion -string "${GITHUB_RUN_NUMBER:-1}" "$CONTENTS/Info.plist"

if [[ -n "${MACOS_SIGNING_IDENTITY:-}" ]]; then
  codesign --force --deep --options runtime --timestamp \
    --sign "$MACOS_SIGNING_IDENTITY" "$APP_PATH"
  codesign --verify --deep --strict --verbose=2 "$APP_PATH"
else
  echo "MACOS_SIGNING_IDENTITY is not set; creating an unsigned app."
fi

ln -s /Applications "$BUILD_DIR/dmg/Applications"
rm -f "$DMG_PATH"

MAX_DMG_ATTEMPTS=3
for ((attempt = 1; attempt <= MAX_DMG_ATTEMPTS; attempt++)); do
  attempt_path="${DMG_PATH%.dmg}.attempt-$attempt.dmg"
  rm -f "$attempt_path"

  if hdiutil create \
    -volname "MTGA Deck Downloader" \
    -srcfolder "$BUILD_DIR/dmg" \
    -ov \
    -format UDZO \
    "$attempt_path"; then
    mv "$attempt_path" "$DMG_PATH"
    break
  fi

  rm -f "$attempt_path"
  if ((attempt == MAX_DMG_ATTEMPTS)); then
    echo "DMG creation failed after $MAX_DMG_ATTEMPTS attempts." >&2
    exit 1
  fi

  retry_delay=$((attempt * 5))
  echo "DMG creation attempt $attempt failed; retrying in $retry_delay seconds." >&2
  sleep "$retry_delay"
done

if [[ -n "${MACOS_SIGNING_IDENTITY:-}" ]]; then
  codesign --force --timestamp --sign "$MACOS_SIGNING_IDENTITY" "$DMG_PATH"
  codesign --verify --verbose=2 "$DMG_PATH"
fi

echo "DMG ready: $DMG_PATH"
