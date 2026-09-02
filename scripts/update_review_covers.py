#!/usr/bin/env python3
"""
Uzi Network — Update review cover frontmatter
Maps the old SVG cover references to the new JPG images.
"""
import os
import re
from pathlib import Path

REVIEW_DIR = Path("/home/ubuntu/projects/uzi-network/src/content/reviews")
ASSET_DIR = Path("/home/ubuntu/projects/uzi-network/src/assets/reviews")
PUBLIC_DIR = Path("/home/ubuntu/projects/uzi-network/public/images/reviews")

# Map review file slug → image filename
# (review id, image file in src/assets/reviews/)
SLUG_MAP = {
    "macbook-m5": "macbook-pro-m5",
    "claude-sonnet": "claude-4-sonnet",
    "garmin-fenix-9": "garmin-fenix-9-solar",
    "mx-master-4": "logitech-mx-master-4",
    "sony-xm6": "sony-wh-1000xm6",
    "anker-543-usb-c-hub": "anker-543-usb-c-hub",
    "anker-727-charging-station": "anker-727-charging-station",
    "anker-737-power-bank": "anker-737-power-bank",
    "anker-nano-ii-65w": "anker-nano-ii-65w",
    "anker-powercore-10k": "anker-powercore-10k",
    "anker-soundcore-life-q35": "anker-soundcore-life-q35",
    "apple-airpods-pro-3": "apple-airpods-pro-3",
    "aqara-u200": "aqara-u200",
    "bose-quietcomfort-ultra": "bose-quietcomfort-ultra",
    "eero-max-7": "eero-max-7",
    "garmin-instinct-2-solar": "garmin-instinct-2-solar",
    "govee-glide-wall-light": "govee-glide-wall-light",
    "jackery-explorer-1000-v2": "jackery-explorer-1000-v2",
    "notion-calendar": "notion-calendar",
    "ring-battery-doorbell-plus": "ring-battery-doorbell-plus",
    "sennheiser-momentum-4": "sennheiser-momentum-4",
    "tp-link-kasa-smart-plug": "tp-link-kasa-smart-plug",
}


def update_review(md_path: Path, image_basename: str):
    text = md_path.read_text()
    # Replace any cover: line
    new_text = re.sub(
        r'^cover:\s*".*?"$',
        f'cover: "/_images/{image_basename}.jpg"',
        text,
        flags=re.MULTILINE,
    )
    if new_text == text:
        print(f"  ! No cover line found in {md_path.name}")
        return False
    md_path.write_text(new_text)
    print(f"  ✓ {md_path.name} → /_images/{image_basename}.jpg")
    return True


def main():
    # First, copy images from src/assets/reviews to public/_images
    PUBLIC_IMG = PUBLIC_DIR.parent / "_images"
    PUBLIC_IMG.mkdir(parents=True, exist_ok=True)
    print("=== Copying images to public/_images/ ===")
    for src in ASSET_DIR.glob("*.jpg"):
        dst = PUBLIC_IMG / src.name
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            dst.write_bytes(src.read_bytes())
            print(f"  ✓ {src.name} ({src.stat().st_size // 1024} KB)")

    # Map review id (from filename) to image slug
    print("\n=== Updating review frontmatter ===")
    updated = 0
    for md_path in REVIEW_DIR.glob("*.md"):
        # Skip blog and other content
        # Extract slug from filename (without .md)
        slug = md_path.stem
        if slug not in SLUG_MAP:
            print(f"  ! No mapping for {md_path.name}")
            continue
        img = SLUG_MAP[slug]
        if update_review(md_path, img):
            updated += 1

    # Also remove or replace existing SVGs (we're not deleting to keep git history)
    print(f"\nDone. {updated} reviews updated.")
    print(f"Images in public/_images/: {len(list(PUBLIC_IMG.glob('*.jpg')))}")


if __name__ == "__main__":
    main()
