"""Generate a favicon set from a source PNG using Pillow.

Usage: python scripts/generate-favicons.py

Requires: favicon-source.png in the project root.
Outputs: frontend/public/favicon.ico, favicon-*.png, apple-touch-icon.png, site.webmanifest
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE = PROJECT_ROOT / "favicon-source.png"
PUBLIC = PROJECT_ROOT / "frontend" / "public"

SIZES = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "apple-touch-icon.png": 180,
    "android-chrome-192x192.png": 192,
    "android-chrome-512x512.png": 512,
}


def main():
    if not SOURCE.is_file():
        print(f"❌ Source file not found: {SOURCE}")
        print(f"   Place favicon-source.png in {PROJECT_ROOT} and re-run this script.")
        sys.exit(1)

    PUBLIC.mkdir(parents=True, exist_ok=True)

    img = Image.open(SOURCE).convert("RGBA")

    for filename, size in SIZES.items():
        resized = img.resize((size, size), Image.LANCZOS)
        out = PUBLIC / filename
        resized.save(out, format="PNG")
        print(f"  ✓ {filename} ({size}x{size})")

    # favicon.ico — Pillow can save ICO with multiple sizes
    ico_sizes = [16, 32, 48]
    ico_frames = [img.resize((s, s), Image.LANCZOS) for s in ico_sizes]
    ico_path = PUBLIC / "favicon.ico"
    ico_frames[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
        append_images=ico_frames[1:],
    )
    print(f"  ✓ favicon.ico ({', '.join(f'{s}x{s}' for s in ico_sizes)})")

    print(f"\n✅ All favicons generated in {PUBLIC}/")
    print("   Update frontend/index.html and site.webmanifest are ready.")


if __name__ == "__main__":
    main()
