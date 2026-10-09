#!/usr/bin/env python3
"""Generate the SGA creatives logo files and favicons (share images: tools/share/).

Usage (from the project root):
    python3 tools/make_brand.py

Glyph outlines are converted to SVG paths, so the logos never depend on
installed fonts. Requires fontTools and Pillow.
Fonts (SIL Open Font License): Figtree, Archivo and Oswald (wordmark only), in tools/fonts-src/.
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

PAPER = "#F3F0E9"
INK = "#171918"
ACID = "#D8F267"
MARK_RED = "#D2202A"   # the lower hook: a clear red that still reads at 16 px on ink (the site red #5E0B10 is too dark there)

FIGTREE = FONTS / "Figtree-VF.ttf"
# Logo and mark: Figtree ExtraBold, a geometric grotesk in the spirit of Spotify's Circular.
LOGO_AXES = {"wght": 800}
MARK_AXES = {"wght": 800}
SERIF = instantiateVariableFont(TTFont(FIGTREE), LOGO_AXES)       # name kept: the display face
SERIF_MARK = instantiateVariableFont(TTFont(FIGTREE), MARK_AXES)
_TMP = Path(tempfile.mkdtemp())


def static_font(src: Path, axes: dict, size: int) -> ImageFont.FreeTypeFont:
    """Pillow font from a pinned instance (Pillow mis-spaces variable fonts)."""
    out = _TMP / (src.stem + "".join(f"-{k}{v}" for k, v in sorted(axes.items())) + ".ttf")
    if not out.exists():
        instantiateVariableFont(TTFont(src), axes).save(out)
    return ImageFont.truetype(str(out), size)
_vf = TTFont(FONTS / "Archivo-VF.ttf")
# The wordmark "sga.creatives": Oswald Regular, a condensed grotesk. Only its outlines ship (as SVG
# paths), so the site still loads just two font families.
WORDMARK = instantiateVariableFont(TTFont(FONTS / "Oswald-VF.ttf"), {"wght": 400})
# The app icon / favicon: "sga" from the wordmark, a touch bolder so it holds at 16 px, white on ink.
ICON_AXES = {"wght": 500}
ICON_FONT = instantiateVariableFont(TTFont(FONTS / "Oswald-VF.ttf"), ICON_AXES)
ICON_BG = "#111111"
ICON_FG = "#FFFFFF"
GROTESK = instantiateVariableFont(_vf, {"wght": 560, "wdth": 125})


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


def cap_height(font: TTFont, size: float) -> float:
    return font["OS/2"].sCapHeight * size / font["head"].unitsPerEm


def logo_svg(fg: str, title: str) -> tuple[str, float, float]:
    """Primary lockup: large serif SGA, small expanded 'creatives' tucked under the A."""
    size = 100
    # Tight, confident spacing.
    sga = Text(SERIF, "SGA", size, tracking=-0.04)
    lsb, rsb = sga.ink_bounds()
    x0 = -lsb
    baseline = cap_height(SERIF, size) + 2
    sga_w = sga.width() - lsb - rsb

    small = 15.5
    cr = Text(GROTESK, "creatives", small, tracking=0.04)
    c_lsb, c_rsb = cr.ink_bounds()
    cr_w = cr.width() - c_lsb - c_rsb
    gap = 12
    cr_base = baseline + gap + cap_height(GROTESK, small) * 0.74  # x-height-ish line
    cr_x = sga_w - cr_w - c_lsb  # right-aligned with the A
    rule_y = baseline + gap * 0.5 + 4
    rule_end = cr_x + c_lsb - 8

    width = sga_w
    height = cr_base + 4
    body = (
        f'<path d="{sga.path(x0, baseline)}"/>'
        f'<path d="{cr.path(cr_x, cr_base)}"/>'
        f'<rect x="0" y="{rule_y - 0.75:.2f}" width="{rule_end:.2f}" height="1.5"/>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-labelledby="t">'
        f'<title id="t">{title}</title><g fill="{fg}">{body}</g></svg>'
    )
    return svg, width, height


def logo_horizontal_svg(fg: str, title: str) -> tuple[str, float, float]:
    """Horizontal lockup for headers and small spaces: SGA | creatives on one baseline."""
    size = 100
    sga = Text(SERIF, "SGA", size, tracking=-0.04)
    lsb, rsb = sga.ink_bounds()
    baseline = cap_height(SERIF, size) + 2
    sga_w = sga.width() - lsb - rsb
    small = 30
    cr = Text(GROTESK, "creatives", small, tracking=0.03)
    c_lsb, c_rsb = cr.ink_bounds()
    cr_w = cr.width() - c_lsb - c_rsb
    gap = 18
    rule_x = sga_w + gap
    cr_x = rule_x + 1.5 + gap - c_lsb
    width = rule_x + 1.5 + gap + cr_w
    height = baseline + 2
    body = (
        f'<path d="{sga.path(-lsb, baseline)}"/>'
        f'<rect x="{rule_x:.2f}" y="{baseline - cap_height(SERIF, size) * 0.62:.2f}" width="1.5" '
        f'height="{cap_height(SERIF, size) * 0.62:.2f}"/>'
        f'<path d="{cr.path(cr_x, baseline)}"/>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.2f} {height:.2f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-labelledby="t">'
        f'<title id="t">{title}</title><g fill="{fg}">{body}</g></svg>'
    )
    return svg, width, height


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
    font = static_font(FONTS / "Oswald-VF.ttf", ICON_AXES, int(n * 40 / 64))
    l, t, r, b = d.textbbox((0, 0), "sga", font=font)
    d.text(((n - (r - l)) / 2 - l, (n - (b - t)) / 2 - t), "sga", font=font, fill=ICON_FG)
    return im.resize((px, px), Image.LANCZOS)


# ---------------------------------------------------------------- the mark: a creative S (brand guide only)
# Two hooks that lock into each other (the same idea as the services boxes): the upper hook in
# paper, the lower in red, slanted forward. Drawn on a 64-unit grid, stroke 10.
MARK_SKEW = 0.2126          # tan(12deg), forward slant
MARK_SHIFT = 7              # re-centres the slanted S
UPPER = "M46 16H26a8.5 8.5 0 0 0 0 17h8"
LOWER = "M30 31h8a8.5 8.5 0 0 1 0 17H18"


def mark_svg(bg: str = INK, radius: float = 0) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-labelledby="t"><title id="t">SGA creatives</title>'
        f'<rect width="64" height="64" rx="{radius}" fill="{bg}"/>'
        f'<g transform="skewX(-12) translate({MARK_SHIFT} 0)" fill="none" stroke-width="10">'
        f'<path d="{UPPER}" stroke="{PAPER}"/><path d="{LOWER}" stroke="{MARK_RED}"/></g>'
        "</svg>"
    )


def _hook_mask(n: int, unit: float, upper: bool) -> Image.Image:
    """Unslanted hook as a mask: two bars plus a half ring (outer r 13.5, inner r 3.5)."""
    m = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(m)
    u = lambda v: v * unit
    if upper:
        bars = [(26, 11, 46, 21), (26, 28, 34, 38)]
        cx, cy, start, end = 26, 24.5, 90, 270        # left half
    else:
        bars = [(30, 26, 38, 36), (18, 43, 38, 53)]
        cx, cy, start, end = 38, 39.5, 270, 450       # right half
    for x0, y0, x1, y1 in bars:
        d.rectangle([u(x0), u(y0), u(x1), u(y1)], fill=255)
    d.pieslice([u(cx - 13.5), u(cy - 13.5), u(cx + 13.5), u(cy + 13.5)], start, end, fill=255)
    d.ellipse([u(cx - 3.5), u(cy - 3.5), u(cx + 3.5), u(cy + 3.5)], fill=0)
    # keep the bars that pass through the inner circle
    for x0, y0, x1, y1 in bars:
        d.rectangle([u(x0), u(y0), u(x1), u(y1)], fill=255)
    return m


def raster_mark(px: int, radius_ratio: float = 0.0) -> Image.Image:
    """Pixel version of the mark, drawn at 8x, slanted with an affine transform, then downsampled."""
    ss = 8
    n = px * ss
    unit = n / 64
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * radius_ratio), fill=INK)
    # output (x, y) samples input (x - shift + skew*y, y): the inverse of skewX(-12) translate(7 0)
    affine = (1, MARK_SKEW, -MARK_SHIFT * unit, 0, 1, 0)
    for upper, colour in ((True, PAPER), (False, MARK_RED)):
        mask = _hook_mask(n, unit, upper).transform((n, n), Image.AFFINE, affine, resample=Image.BICUBIC)
        im.paste(Image.new("RGBA", (n, n), colour), (0, 0), mask)
    return im.resize((px, px), Image.LANCZOS)


def main() -> None:
    BRAND.mkdir(exist_ok=True)
    (PUBLIC / "assets" / "brand").mkdir(parents=True, exist_ok=True)

    dark, w, h = logo_svg(INK, "SGA creatives")
    light, _, _ = logo_svg(PAPER, "SGA creatives")
    hdark, _, _ = logo_horizontal_svg(INK, "SGA creatives")
    hlight, _, _ = logo_horizontal_svg(PAPER, "SGA creatives")
    wdark, _, _ = wordmark_svg(INK, "SGA creatives")
    wlight, _, _ = wordmark_svg(PAPER, "SGA creatives")
    mark = mark_svg()

    files = {
        "sga-creatives-logo-dark.svg": dark,    # ink logo for light backgrounds
        "sga-creatives-logo-light.svg": light,  # paper logo for dark backgrounds
        "sga-creatives-logo-horizontal-dark.svg": hdark,
        "sga-creatives-logo-horizontal-light.svg": hlight,
        "sga-creatives-wordmark-dark.svg": wdark,    # the header wordmark: sga.creatives
        "sga-creatives-wordmark-light.svg": wlight,
        "sga-creatives-mark.svg": mark,
    }
    for name, svg in files.items():
        (BRAND / name).write_text(svg)
        (PUBLIC / "assets" / "brand" / name).write_text(svg)
    (PUBLIC / "favicon.svg").write_text(icon_svg())
    (BRAND / "sga-creatives-icon.svg").write_text(icon_svg())

    # the site's icons: sga on ink (apple-touch-icon is square; iOS rounds the corners itself)
    raster_icon(180, 0).convert("RGB").save(PUBLIC / "apple-touch-icon.png")
    raster_mark(512).save(BRAND / "sga-creatives-mark-512.png")
    raster_icon(192).save(PUBLIC / "assets" / "brand" / "icon-192.png")
    raster_icon(512).save(PUBLIC / "assets" / "brand" / "icon-512.png")
    ico_sizes = [16, 32, 48]
    base = raster_icon(48)
    base.save(PUBLIC / "favicon.ico", sizes=[(s, s) for s in ico_sizes],
              append_images=[raster_icon(s) for s in ico_sizes[:-1]])
    print(f"logo viewBox {w:.1f} x {h:.1f}")


if __name__ == "__main__":
    main()
