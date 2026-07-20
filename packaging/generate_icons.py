from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


ICON_SIZES = (16, 32, 64, 128, 256, 512, 1024)


def render_icon(size: int = 1024) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    scale = size / 1024

    def box(values: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return tuple(round(value * scale) for value in values)  # type: ignore[return-value]

    draw.rounded_rectangle(
        box((44, 44, 980, 980)),
        radius=round(190 * scale),
        fill=(22, 31, 51, 255),
    )
    draw.rounded_rectangle(
        box((234, 178, 682, 760)),
        radius=round(54 * scale),
        fill=(49, 65, 91, 255),
        outline=(222, 231, 242, 255),
        width=max(1, round(34 * scale)),
    )
    draw.rounded_rectangle(
        box((354, 262, 800, 842)),
        radius=round(54 * scale),
        fill=(34, 48, 73, 255),
        outline=(255, 255, 255, 255),
        width=max(1, round(34 * scale)),
    )
    draw.polygon(
        [
            (round(512 * scale), round(558 * scale)),
            (round(650 * scale), round(558 * scale)),
            (round(650 * scale), round(452 * scale)),
            (round(824 * scale), round(626 * scale)),
            (round(650 * scale), round(800 * scale)),
            (round(650 * scale), round(694 * scale)),
            (round(512 * scale), round(694 * scale)),
        ],
        fill=(69, 211, 255, 255),
    )
    return image


def generate_icons(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    source = render_icon()
    source.save(output_dir / "app.png")
    source.save(
        output_dir / "app.ico",
        format="ICO",
        sizes=[(size, size) for size in ICON_SIZES if size <= 256],
    )
    source.save(
        output_dir / "app.icns",
        format="ICNS",
        sizes=[(size, size) for size in ICON_SIZES],
    )

    iconset = output_dir / "MTGADeckDownloader.iconset"
    iconset.mkdir(exist_ok=True)
    iconset_files = {
        "icon_16x16.png": 16,
        "icon_16x16@2x.png": 32,
        "icon_32x32.png": 32,
        "icon_32x32@2x.png": 64,
        "icon_128x128.png": 128,
        "icon_128x128@2x.png": 256,
        "icon_256x256.png": 256,
        "icon_256x256@2x.png": 512,
        "icon_512x512.png": 512,
        "icon_512x512@2x.png": 1024,
    }
    for name, size in iconset_files.items():
        source.resize((size, size), Image.Resampling.LANCZOS).save(iconset / name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/icons"))
    args = parser.parse_args()
    generate_icons(args.output.resolve())


if __name__ == "__main__":
    main()
