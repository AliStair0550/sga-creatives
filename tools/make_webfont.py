#!/usr/bin/env python3
"""Cut the site font (Inter, SIL Open Font License) down to a small web file.

Usage (from the project root):
    python3 tools/make_webfont.py

Input:  tools/fonts-src/Inter-VF.ttf (axes opsz 14-32, wght 100-900)
Output: public/assets/fonts/Inter-VF.woff2 (opsz kept, wght 400-600, Latin only)

Requires fontTools and brotli.
"""
from io import BytesIO
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "tools" / "fonts-src" / "Inter-VF.ttf"
OUT = ROOT / "public" / "assets" / "fonts" / "Inter-VF.woff2"

# Basic Latin, Latin-1 (Danish letters, ×, ·), general punctuation (’ “ ” …), arrows (← →), €.
UNICODES = "U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+2013-2014,U+2018-201E,U+2022,U+2026,U+2032-2033,U+20AC,U+2190-2193,U+2212"


def main() -> None:
    buf = BytesIO()   # save and reload the limited font, so the subsetter sees plain tables
    instantiateVariableFont(TTFont(SRC), {"wght": (400, 600)}).save(buf)
    buf.seek(0)
    font = TTFont(buf)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk", "tnum", "case", "ss01", "cv11"]
    options.name_IDs = ["*"]
    options.notdef_outline = True
    sub = subset.Subsetter(options)
    sub.populate(unicodes=subset.parse_unicodes(UNICODES))
    sub.subset(font)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    font.flavor = "woff2"
    font.save(OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
