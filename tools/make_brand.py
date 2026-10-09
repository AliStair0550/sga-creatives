#!/usr/bin/env python3
"""Generate the SGA creatives wordmark, favicons and app icons (share images: tools/share/).

Usage (from the project root):
    python3 tools/make_brand.py

Glyph outlines are converted to SVG paths, so the logo never depends on installed fonts.
Requires fontTools and Pillow. Font (SIL Open Font License): Oswald, in tools/fonts-src/.

Outputs:
  brand/ and public/assets/brand/   sga-creatives-wordmark-dark.svg, -light.svg
  brand/sga-creatives-icon.svg      the app icon as SVG
  public/                           favicon.svg, favicon.ico, apple-touch-icon.png
  public/assets/brand/              icon-192.png, icon-512.png (web manifest)
"""
import tempfile
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "tools" / "fonts-src"
BRAND = ROOT / "brand"
PUBLIC = ROOT / "public"

INK = "#111111"
WHITE = "#FFFFFF"
OSWALD = FONTS / "Oswald-VF.ttf"
_TMP = Path(tempfile.mkdtemp())

# The wordmark "sga.creatives": Oswald Regular, a condensed grotesk. Only its outlines ship (as SVG
# paths), so the site loads no extra font.
WORDMARK = instantiateVariableFont(TTFont(OSWALD), {"wght": 400})
# The app icon / favicon: "sga" from the wordmark, a touch bolder so it holds at 16 px, white on ink.
ICON_AXES = {"wght": 500}
ICON_FONT = instantiateVariableFont(TTFont(OSWALD), ICON_AXES)
ICON_BG = INK
ICON_FG = WHITE


def static_font(src: Path, axes: dict, size: int) -> ImageFont.FreeTypeFont:
    """Pillow font from a pinned instance (Pillow mis-spaces variable fonts)."""
    out = _TMP / (src.stem + "".join(f"-{k}{v}" for k, v in sorted(axes.items())) + ".ttf")
    if not out.exists():
        instantiateVariableFont(TTFont(src), axes).save(out)
    return ImageFont.truetype(str(out), size)


class Text:
    """Lay out a string as SVG path data (y axis pointing down)."""

    def __init__(self, font: TTFont, text: str, size: float, tracking: float = 0.0,
                 kern: dict | None = None):
        self.font, self.text, self.size = font, text, size
        self.upm = font["head"].unitsPerEm
        self.scale = size / self.upm
        self.tracking = tracking  # in em
        self.kern = kern or {}
        cmap = font.getBestCmap()
        self.glyphs = [cmap[ord(c)] for c in text]
        gs = font.getGlyphSet()
        self.gs = gs
        self.advances = [font["hmtx"][g][0] for g in self.glyphs]

    def width(self) -> float:
        w = 0.0
        for i, adv in enumerate(self.advances):
            w += adv * self.scale
            if i < len(self.advances) - 1:
                w += self.tracking * self.size + self.kern.get(i, 0) * self.size
        return w

    def path(self, x: float, baseline: float) -> str:
        pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cx = x
        for i, g in enumerate(self.glyphs):
            tp = TransformPen(pen, (self.scale, 0, 0, -self.scale, cx, baseline))
            self.gs[g].draw(tp)
            cx += self.advances[i] * self.scale + self.tracking * self.size + self.kern.get(i, 0) * self.size
        return pen.getCommands()

    def ink_bounds(self):
        """Tight horizontal ink bounds of the first and last glyph (for optical alignment)."""
        bp = BoundsPen(self.gs)
        self.gs[self.glyphs[0]].draw(bp)
        left = bp.bounds[0] * self.scale if bp.bounds else 0
        bp = BoundsPen(self.gs)
        self.gs[self.glyphs[-1]].draw(bp)
        right_side = (self.advances[-1] - bp.bounds[2]) * self.scale if bp.bounds else 0
        return left, right_side


# ---------------------------------------------------------------- the wordmark

def wordmark_svg(fg: str, title: str) -> tuple[str, float, float]:
    """The wordmark used in the site header: sga.creatives, lowercase, on one line."""
    size = 100
    wm = Text(WORDMARK, "sga.creatives", size)
    lsb, rsb = wm.ink_bounds()
    bp = BoundsPen(wm.gs)
    for g in set(wm.glyphs):
        wm.gs[g].draw(bp)
    _, y_min, _, y_max = bp.bounds   # font units, y up: descender of the g to the top of the t
    pad = 4   # breathing room, so the outer s and the g are never clipped by antialiasing at the edge
    baseline = y_max * wm.scale + pad
    width = wm.width() - lsb - rsb + 2 * pad
    height = (y_max - y_min) * wm.scale + 2 * pad
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-labelledby="t">'
        f'<title id="t">{title}</title><g fill="{fg}"><path d="{wm.path(pad - lsb, baseline)}"/></g></svg>'
    )
    return svg, width, height


# ---------------------------------------------------------------- the app icon: sga on ink

def icon_svg(radius: float = 12) -> str:
    """Favicon (SVG): the letters sga from the wordmark, centred on an ink square (64-unit grid)."""
    t = Text(ICON_FONT, "sga", 40)
    lsb, rsb = t.ink_bounds()
    bp = BoundsPen(t.gs)
    for g in set(t.glyphs):
        t.gs[g].draw(bp)
    _, y_min, _, y_max = bp.bounds
    ink_w = t.width() - lsb - rsb
    ink_h = (y_max - y_min) * t.scale
    x = (64 - ink_w) / 2 - lsb
    baseline = (64 - ink_h) / 2 + y_max * t.scale
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-labelledby="t"><title id="t">SGA creatives</title>'
        f'<rect width="64" height="64" rx="{radius}" fill="{ICON_BG}"/>'
        f'<path fill="{ICON_FG}" d="{t.path(x, baseline)}"/></svg>'
    )


def raster_icon(px: int, radius_ratio: float = 0.19) -> Image.Image:
    """Pixel version of the app icon, drawn at 8x and downsampled."""
    ss = 8
    n = px * ss
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * radius_ratio), fill=ICON_BG)
    font = static_font(OSWALD, ICON_AXES, int(n * 40 / 64))
    l, t, r, b = d.textbbox((0, 0), "sga", font=font)
    d.text(((n - (r - l)) / 2 - l, (n - (b - t)) / 2 - t), "sga", font=font, fill=ICON_FG)
    return im.resize((px, px), Image.LANCZOS)


def main() -> None:
    BRAND.mkdir(exist_ok=True)
    (PUBLIC / "assets" / "brand").mkdir(parents=True, exist_ok=True)

    dark, w, h = wordmark_svg(INK, "SGA creatives")
    light, _, _ = wordmark_svg(WHITE, "SGA creatives")
    for name, svg in {
        "sga-creatives-wordmark-dark.svg": dark,     # ink, for the white site
        "sga-creatives-wordmark-light.svg": light,   # white, for dark backgrounds
    }.items():
        (BRAND / name).write_text(svg)
        (PUBLIC / "assets" / "brand" / name).write_text(svg)
    (PUBLIC / "favicon.svg").write_text(icon_svg())
    (BRAND / "sga-creatives-icon.svg").write_text(icon_svg())

    # apple-touch-icon is square: iOS rounds the corners itself
    raster_icon(180, 0).convert("RGB").save(PUBLIC / "apple-touch-icon.png")
    raster_icon(192).save(PUBLIC / "assets" / "brand" / "icon-192.png")
    raster_icon(512).save(PUBLIC / "assets" / "brand" / "icon-512.png")
    raster_icon(512).save(BRAND / "sga-creatives-icon-512.png")
    ico_sizes = [16, 32, 48]
    raster_icon(48).save(PUBLIC / "favicon.ico", sizes=[(s, s) for s in ico_sizes],
                         append_images=[raster_icon(s) for s in ico_sizes[:-1]])
    print(f"wordmark viewBox {w:.1f} x {h:.1f}")


if __name__ == "__main__":
    main()
