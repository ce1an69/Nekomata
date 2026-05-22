"""Generate runtime card images from the retained origin PNG files."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CARDS_DIR = PROJECT_ROOT / "assets" / "cards"
DETAIL_SIZE = (256, 384)


def generate_detail_image(origin_path: Path) -> Path:
    detail_path = origin_path.with_name(origin_path.name.replace("_origin.png", "_detail.png"))
    with Image.open(origin_path) as img:
        img = img.convert("RGBA")
        img.thumbnail(DETAIL_SIZE, Image.Resampling.LANCZOS)
        img.save(detail_path, optimize=True)
    return detail_path


def main() -> None:
    origins = sorted(CARDS_DIR.glob("*/*_origin.png"))
    for origin_path in origins:
        generate_detail_image(origin_path)
    print(f"Generated {len(origins)} detail images at {DETAIL_SIZE[0]}x{DETAIL_SIZE[1]} max.")


if __name__ == "__main__":
    main()
