#!/usr/bin/env python3
"""Optimise source media into public/assets for the SGA creatives website.

Usage (from the project root):
    python3 tools/optimize_media.py

Reads originals from assets/images/ and assets/video/ (never modified) and writes:
    public/assets/img/<name>-<width>.avif|webp  (responsive sizes)
    public/assets/img/<name>-800.jpg             (fallback for old browsers)
    content/media-manifest.json                  (sizes used by build_site.py)
    public/assets/video/*.mp4 + poster images

Requires Pillow (with AVIF/WebP support) and ffmpeg for video.
"""
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC_IMG = ROOT / "assets" / "images"
SRC_VID = ROOT / "assets" / "video"
OUT_IMG = ROOT / "public" / "assets" / "img"
OUT_VID = ROOT / "public" / "assets" / "video"

WIDTHS = [480, 800, 1200]


def save_variants(im: Image.Image, name: str, manifest: dict) -> None:
    w, h = im.size
    widths = sorted({min(x, w) for x in WIDTHS})
    for tw in widths:
        th = round(h * tw / w)
        rs = im if tw == w else im.resize((tw, th), Image.LANCZOS)
        rs.save(OUT_IMG / f"{name}-{tw}.avif", quality=58, speed=4)
        rs.save(OUT_IMG / f"{name}-{tw}.webp", quality=78, method=6)
    fb_w = min(800, w)
    fb = im.resize((fb_w, round(h * fb_w / w)), Image.LANCZOS) if fb_w != w else im
    fb.save(OUT_IMG / f"{name}-{fb_w}.jpg", quality=80, optimize=True, progressive=True)
    manifest[name] = {"width": w, "height": h, "widths": widths, "fallback": fb_w}


def main() -> None:
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    OUT_VID.mkdir(parents=True, exist_ok=True)
    manifest: dict = {}

    for src in sorted(SRC_IMG.glob("*.jpg")):
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        save_variants(im, src.stem, manifest)
        print("image", src.name, im.size)

    for src in sorted(SRC_VID.glob("*.mp4")):
        dest = OUT_VID / src.name
        # Same streams, moov atom moved to the front so playback can start early.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-c", "copy",
                        "-movflags", "+faststart", str(dest)], check=True)
        poster_tmp = OUT_VID / f"{src.stem}-poster.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1", "-i", str(src),
                        "-frames:v", "1", str(poster_tmp)], check=True)
        im = Image.open(poster_tmp).convert("RGB")
        im.save(OUT_VID / f"{src.stem}-poster.jpg", quality=80, optimize=True, progressive=True)
        manifest[f"video:{src.stem}"] = {"width": im.width, "height": im.height}
        poster_tmp.unlink()
        print("video", src.name, im.size)

    (ROOT / "content" / "media-manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required for the video step")
    main()
