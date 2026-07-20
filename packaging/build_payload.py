from __future__ import annotations

import argparse
from importlib import metadata
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist" / "pyinstaller"
WORK_DIR = ROOT / "build" / "pyinstaller"


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def project_version() -> str:
    try:
        return metadata.version("mtga-deck-downloader")
    except metadata.PackageNotFoundError as exc:
        raise SystemExit("Install the project first: pip install -e '.[release]'") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default=project_version())
    args = parser.parse_args()

    actual_version = project_version()
    if args.version != actual_version:
        raise SystemExit(
            f"Requested version {args.version!r} does not match pyproject version "
            f"{actual_version!r}."
        )

    icon_dir = ROOT / "build" / "icons"
    run([sys.executable, str(ROOT / "packaging" / "generate_icons.py"), "--output", str(icon_dir)])

    env = os.environ.copy()
    env["MTGA_PROJECT_ROOT"] = str(ROOT)
    env["MTGA_APP_VERSION"] = actual_version
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(ROOT / "packaging" / "pyinstaller" / "mtga_deck_downloader.spec"),
            "--noconfirm",
            "--clean",
            "--distpath",
            str(DIST_DIR),
            "--workpath",
            str(WORK_DIR),
        ],
        env=env,
    )

    executable_name = "mtga-deck-downloader.exe" if sys.platform.startswith("win") else "mtga-deck-downloader"
    executable = DIST_DIR / "mtga-deck-downloader" / executable_name
    if not executable.exists():
        raise SystemExit(f"PyInstaller executable was not created: {executable}")

    run([str(executable), "--version"])
    run([str(executable), "--diagnose"])
    print(f"Payload ready: {executable.parent}")


if __name__ == "__main__":
    main()
