#!/usr/bin/env python3
"""Generate the SGA creatives logo files, favicons and share image.

Usage (from the project root):
    python3 tools/make_brand.py

Glyph outlines are converted to SVG paths, so the logos never depend on
installed fonts. Requires fontTools and Pillow.
Fonts (SIL Open Font License): Instrument Serif and Archivo, in tools/fonts-src/.
"""
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
OXBLOOD = "#542536"
ACID = "#D8F267"

SERIF = TTFont(FONTS / "InstrumentSerif-Regular.ttf")
_vf = TTFont(FONTS / "Archivo-VF.ttf")
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
    # Tight, masthead-like spacing; the G–A pair closes up a little further.
    sga = Text(SERIF, "SGA", size, tracking=-0.02, kern={1: -0.015})
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
    sga = Text(SERIF, "SGA", size, tracking=-0.02, kern={1: -0.015})
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


MARK_SIZE = 74      # serif S, in units of a 64-unit square
MARK_STROKE = 2.4   # thickens the hairlines so the S survives 16 px
MARK_DOT = 11


def mark_geometry():
    s = Text(SERIF, "S", MARK_SIZE)
    lsb, rsb = s.ink_bounds()
    glyph_w = s.width() - lsb - rsb
    ch = cap_height(SERIF, MARK_SIZE)
    total = glyph_w + 2 + MARK_DOT
    x = (64 - total) / 2 - lsb
    baseline = (64 + ch) / 2 + 0.5
    return x, baseline, x + lsb + glyph_w + 2, MARK_DOT


def mark_svg(bg: str = INK, fg: str = PAPER, accent: str = ACID, radius: float = 0) -> str:
    """Compact mark: serif S with an acid full stop on an ink square (64-unit grid)."""
    x, baseline, dot_x, dot = mark_geometry()
    s = Text(SERIF, "S", MARK_SIZE)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-labelledby="t"><title id="t">SGA creatives</title>'
        f'<rect width="64" height="64" rx="{radius}" fill="{bg}"/>'
        f'<path fill="{fg}" stroke="{fg}" stroke-width="{MARK_STROKE}" stroke-linejoin="round" d="{s.path(x, baseline)}"/>'
        f'<rect x="{dot_x:.2f}" y="{baseline - dot:.2f}" width="{dot}" height="{dot}" fill="{accent}"/>'
        "</svg>"
    )


def raster_mark(px: int, radius_ratio: float = 0.0) -> Image.Image:
    """Pixel version of the compact mark, drawn from the same font at 8x and downsampled."""
    ss = 8
    n = px * ss
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, n - 1, n - 1], radius=int(n * radius_ratio), fill=INK)
    unit = n / 64
    font = ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), round(MARK_SIZE * unit))
    x, baseline, dx, dot = mark_geometry()
    d.text((x * unit, baseline * unit), "S", font=font, fill=PAPER, anchor="ls",
           stroke_width=round(MARK_STROKE / 2 * unit), stroke_fill=PAPER)
    d.rectangle([dx * unit, (baseline - dot) * unit, (dx + dot) * unit, baseline * unit], fill=ACID)
    return im.resize((px, px), Image.LANCZOS)


def og_image(path: Path) -> None:
    """1200x630 share image: project photo + ink panel with the wordmark."""
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), INK)
    photo = Image.open(ROOT / "assets/images/adidas-kiosk-04.jpg").convert("RGB")
    pw = 520
    ph = round(photo.height * pw / photo.width)
    photo = photo.resize((pw, ph), Image.LANCZOS)
    top = int((ph - H) * 0.42)
    im.paste(photo.crop((0, top, pw, top + H)), (W - pw, 0))
    d = ImageDraw.Draw(im)
    serif = ImageFont.truetype(str(FONTS / "InstrumentSerif-Regular.ttf"), 190)
    serif_i = ImageFont.truetype(str(FONTS / "InstrumentSerif-Italic.ttf"), 64)
    grot = ImageFont.truetype(str(FONTS / "Archivo-VF.ttf"), 26)
    grot.set_variation_by_axes([560, 125])  # wght, wdth
    d.text((68, 236), "SGA", font=serif, fill=PAPER, anchor="ls")
    d.rectangle([72, 262, 72 + 150, 263], fill=PAPER)
    d.text((240, 272), "creatives", font=grot, fill=PAPER, anchor="lm")
    d.text((72, 500), "Where brands", font=serif_i, fill=PAPER, anchor="ls")
    d.text((72, 560), "meet culture", font=serif_i, fill=PAPER, anchor="ls")
    end = d.textlength("meet culture", font=serif_i)
    d.rectangle([72 + end + 6, 548, 72 + end + 18, 560], fill=ACID)
    im.save(path, quality=86, optimize=True, progressive=True)


def main() -> None:
    BRAND.mkdir(exist_ok=True)
    (PUBLIC / "assets" / "brand").mkdir(parents=True, exist_ok=True)
    (PUBLIC / "assets" / "og").mkdir(parents=True, exist_ok=True)

    dark, w, h = logo_svg(INK, "SGA creatives")
    light, _, _ = logo_svg(PAPER, "SGA creatives")
    hdark, _, _ = logo_horizontal_svg(INK, "SGA creatives")
    hlight, _, _ = logo_horizontal_svg(PAPER, "SGA creatives")
    mark = mark_svg()
    mark_round = mark_svg(radius=12)

    files = {
        "sga-creatives-logo-dark.svg": dark,    # ink logo for light backgrounds
        "sga-creatives-logo-light.svg": light,  # paper logo for dark backgrounds
        "sga-creatives-logo-horizontal-dark.svg": hdark,
        "sga-creatives-logo-horizontal-light.svg": hlight,
        "sga-creatives-mark.svg": mark,
    }
    for name, svg in files.items():
        (BRAND / name).write_text(svg)
        (PUBLIC / "assets" / "brand" / name).write_text(svg)
    (PUBLIC / "favicon.svg").write_text(mark_round)

    raster_mark(180).convert("RGB").save(PUBLIC / "apple-touch-icon.png")
    raster_mark(512).save(BRAND / "sga-creatives-mark-512.png")
    raster_mark(192, 0.19).save(PUBLIC / "assets" / "brand" / "icon-192.png")
    raster_mark(512, 0.19).save(PUBLIC / "assets" / "brand" / "icon-512.png")
    ico_sizes = [16, 32, 48]
    base = raster_mark(48, 0.19)
    base.save(PUBLIC / "favicon.ico", sizes=[(s, s) for s in ico_sizes],
              append_images=[raster_mark(s, 0.19) for s in ico_sizes[:-1]])
    og_image(PUBLIC / "assets" / "og" / "sga-creatives-share.jpg")
    print(f"logo viewBox {w:.1f} x {h:.1f}")


if __name__ == "__main__":
    main()
