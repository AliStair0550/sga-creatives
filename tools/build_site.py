#!/usr/bin/env python3
"""Build the static SGA creatives website into public/.

Usage (from the project root):
    python3 tools/build_site.py

Inputs:  content/site.json, content/cases.json, content/media-manifest.json
Outputs: public/index.html, public/work/<slug>/index.html, public/404.html,
         public/robots.txt, public/site.webmanifest, public/_headers,
         public/sitemap.xml (only when a domain is set in content/site.json)

No third-party packages are needed. Run tools/optimize_media.py first when
images change, and tools/make_brand.py when the logo changes.
"""
import base64
import hashlib
import json
import re
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
SITE = json.loads((ROOT / "content" / "site.json").read_text())
CASES = json.loads((ROOT / "content" / "cases.json").read_text())
MANIFEST = json.loads((ROOT / "content" / "media-manifest.json").read_text())
DOMAIN = SITE.get("domain", "").rstrip("/")
YEAR = date.today().year
OG_IMAGE = "/assets/og/sga-creatives-share.jpg"

# Runs before first paint: flags JS support (for reveal animations) and removes
# the flag again if main.js never loads, so content can never stay hidden.
HEAD_SCRIPT = (
    "document.documentElement.classList.add('js');"
    "setTimeout(function(){if(!window.sgaReady)document.documentElement.classList.remove('js')},2500);"
)
HEAD_SCRIPT_HASH = base64.b64encode(hashlib.sha256(HEAD_SCRIPT.encode()).digest()).decode()


def e(text: str) -> str:
    return escape(text, quote=True)


def asset_version(path: str) -> str:
    digest = hashlib.sha256((PUBLIC / path.lstrip("/")).read_bytes()).hexdigest()[:10]
    return f"{path}?v={digest}"


def absolute(path: str) -> str:
    return f"{DOMAIN}{path}" if DOMAIN else path


def inline_logo(kind: str = "horizontal") -> str:
    name = "sga-creatives-logo-horizontal-dark.svg" if kind == "horizontal" else "sga-creatives-logo-dark.svg"
    svg = (PUBLIC / "assets" / "brand" / name).read_text()
    svg = re.sub(r'<title id="t">.*?</title>', "", svg)
    svg = svg.replace(' role="img" aria-labelledby="t"', ' aria-hidden="true" focusable="false"')
    svg = re.sub(r' width="\d+" height="\d+"', "", svg, count=1)
    return svg.replace('fill="#171918"', 'fill="currentColor"')


def picture(name: str, alt: str, sizes: str, cls: str = "", eager: bool = False,
            priority: bool = False) -> str:
    m = MANIFEST[name]
    def srcset(ext):
        return ", ".join(f"/assets/img/{name}-{w}.{ext} {w}w" for w in m["widths"])
    loading = 'loading="eager"' if eager else 'loading="lazy"'
    fetch = ' fetchpriority="high"' if priority else ""
    cls_attr = f' class="{cls}"' if cls else ""
    return (
        f'<picture{cls_attr}>'
        f'<source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
        f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
        f'<img src="/assets/img/{name}-{m["fallback"]}.jpg" width="{m["width"]}" height="{m["height"]}" '
        f'alt="{e(alt)}" {loading} decoding="async"{fetch}>'
        f'</picture>'
    )


NAV_LEFT = [("Work", "/#work"), ("Services", "/#services"), ("About", "/#about")]
NAV = NAV_LEFT + [("Contact", "/#contact")]


def media(name: str, alt: str, sizes: str, *, cls: str = "", eager: bool = False,
          priority: bool = False, label: str = "") -> str:
    """A picture when the image exists, otherwise an elegant placeholder frame.

    Placeholders are filled by dropping assets/images/<name>.jpg in place and running
    tools/optimize_media.py + tools/build_site.py (remember the alt text in content/).
    """
    if name in MANIFEST:
        return picture(name, alt, sizes, cls=cls, eager=eager, priority=priority)
    num = e(label or name.rsplit("-", 1)[-1])
    return (f'<div class="ph {cls}" aria-hidden="true" data-placeholder="{e(name)}">'
            f'<span class="ph-mark">S<i></i></span><span class="ph-num">{num}</span></div>')


def header(tone: str = "dark") -> str:
    left = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in NAV_LEFT)
    return f"""
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-header data-tone="{tone}">
  <div class="header-inner">
    <a class="brand" href="/" aria-label="SGA creatives, home">{inline_logo()}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" hidden>
      <span class="nav-toggle-label" data-label-closed="Menu" data-label-open="Close">Menu</span>
      <span class="nav-toggle-icon" aria-hidden="true"><span></span><span></span></span>
    </button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul class="nav-list nav-list--left">{left}</ul>
      <div class="nav-extra">
        <a href="mailto:{SITE['email']}">{SITE['email']}</a>
        <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a>
      </div>
    </nav>
  </div>
</header>"""


def footer() -> str:
    items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in NAV)
    work = "".join(f'<li><a href="/work/{c["slug"]}/">{e(c["title"])}</a></li>' for c in CASES)
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <a class="brand brand--footer" href="/" aria-label="SGA creatives, home">{inline_logo("stacked")}</a>
      <nav class="footer-col" aria-label="Footer"><ul>{items}</ul></nav>
      <div class="footer-col"><ul>{work}</ul></div>
      <div class="footer-col">
        <ul>
          <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
          <li><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></li>
          <li><a href="{SITE['linkedin']}" rel="noopener">Sarah on LinkedIn</a></li>
          <li><a href="{SITE['instagram']}" rel="noopener">Sarah on Instagram</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>© <span data-year>{YEAR}</span> SGA creatives</p>
      <a href="#top" class="back-to-top">Back to top <span aria-hidden="true">↑</span></a>
    </div>
  </div>
</footer>"""


def page(*, title: str, description: str, path: str, body: str, body_class: str = "",
         og_type: str = "website", og_image: str = OG_IMAGE, extra_head: str = "",
         indexable: bool = True, header_tone: str = "dark") -> str:
    canonical = f'<link rel="canonical" href="{DOMAIN}{path}">' if DOMAIN and indexable else ""
    og_url = f'<meta property="og:url" content="{DOMAIN}{path}">' if DOMAIN and indexable else ""
    robots = "" if indexable else '<meta name="robots" content="noindex">'
    css = asset_version("/assets/css/main.css")
    js = asset_version("/assets/js/main.js")
    return f"""<!doctype html>
<html lang="en" id="top">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{canonical}{robots}
<meta name="theme-color" content="#0E0F0F">
<meta property="og:site_name" content="SGA creatives">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{absolute(og_image)}">
<meta property="og:image:alt" content="SGA creatives: Where brands meet culture.">
<meta property="og:locale" content="en_GB">
{og_url}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/Figtree-VF.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Archivo-VF.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<script>{HEAD_SCRIPT}</script>
<script src="{js}" defer></script>
{extra_head}
</head>
<body class="{body_class}">
{header(header_tone)}
<main id="main" tabindex="-1">
{body}
</main>
{footer()}
</body>
</html>
"""


# ---------------------------------------------------------------- home page

# (problem, service, what it does). Each row is two boxes that slide together on scroll:
# the problem on the left, the solution on the right, locked together by the SGA key.
SERVICES = [
    ("The brand feels unclear or out of step.", "Brand strategy & creative direction", "Makes the brand clear, distinctive and relevant."),
    ("Great ideas never leave the deck.", "Campaigns & creative production", "Turns ideas into campaigns, editorials and content."),
    ("Launches no one remembers.", "Experiences & activations", "Creates events and launches people show up for."),
    ("Too many moving parts, not the right people.", "Creative connections & project management", "Brings the right people together and keeps it on track."),
]

PROCESS = [
    ("Understand", "Brief, goals, frame"),
    ("Connect", "The right team"),
    ("Create", "Concept and direction"),
    ("Deliver", "Production, on the day"),
]

EXPERIENCE = [
    ("Rezet Store", "Brand and Community Manager", "2025-2026"),
    ("Envii", "Brand Manager", "2024-2025"),
    ("NAKED Copenhagen", "Social Media and Community Manager", "2023-2024"),
    ("Bestseller A/S · NAME IT", "Social Media and PR Manager", "2021-2023"),
]


def tone_style(c: dict) -> str:
    return f'--tone:{c["tone"]["bg"]}'


def alt_for(c: dict, name: str) -> str:
    for g in c["gallery"]:
        if g.get("image") == name and g.get("alt"):
            return g["alt"]
    return c["lead"]["alt"] if c["lead"]["image"] == name else ""


def universe(i: int, c: dict) -> str:
    """One case on the home page: a full-width panel in the case's own tone."""
    flip = " is-flipped" if i % 2 else ""
    return f"""
  <article class="universe tone-{c['tone']['mode']}{flip}" style="{tone_style(c)}">
    <div class="universe-inner container">
      <div class="universe-main" data-reveal>{media(c['card_image'], alt_for(c, c['card_image']), "(min-width: 900px) 50vw, 100vw")}</div>
      <div class="universe-second" data-reveal>{media(c['card_image_2'], alt_for(c, c['card_image_2']), "(min-width: 900px) 22vw, 45vw")}</div>
      <div class="universe-text" data-reveal>
        <p class="label">{e(c['category'])}</p>
        <h3 class="universe-title"><a href="/work/{c['slug']}/">{e(c['title'])}</a></h3>
        <p class="universe-partners">{e(c['partners'])}</p>
        <p class="universe-link" aria-hidden="true">View case <span>→</span></p>
      </div>
    </div>
  </article>"""


def rise_words(html_text: str) -> str:
    """Wrap words in a headline so they can rise one by one when revealed."""
    parts = re.split(r"(<em>.*?</em>)", html_text)
    out, i = [], 0
    for part in parts:
        if not part:
            continue
        em = part.startswith("<em>")
        inner = part[4:-5] if em else part
        spans = []
        for w in inner.split():
            spans.append(f'<span class="rw"><span style="--i:{i}">{w}</span></span>')
            i += 1
        chunk = " ".join(spans)
        out.append(f"<em>{chunk}</em>" if em else chunk)
    return " ".join(out)


def home() -> str:
    universes = "".join(universe(i, c) for i, c in enumerate(CASES))
    services = "".join(f"""
      <li class="svc-row" style="--tilt:{1 if i % 2 == 0 else -1}">
        <div class="svc-box svc-problem">
          <p class="label">Problem</p>
          <p class="svc-problem-text">{e(prob)}</p>
        </div>
        <div class="svc-box svc-solution">
          <span class="svc-key" aria-hidden="true">S<i></i></span>
          <p class="label">Solution</p>
          <h3 class="svc-title">{e(t).replace(" &amp; ", ' <span class="amp">&amp;</span> ')}</h3>
          <p class="svc-answer">{e(d)}</p>
        </div>
      </li>""" for i, (prob, t, d) in enumerate(SERVICES))
    process = "".join(f"""
        <li><span class="step-word">{t}</span><span class="step-note">{e(d)}</span></li>"""
                      for t, d in PROCESS)
    experience = "".join(f"""
          <li><span class="xp-company">{e(co)}</span><span class="xp-role">{e(role)}</span><span class="xp-years">{yrs}</span></li>"""
                         for co, role, yrs in EXPERIENCE)

    ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "SGA creatives",
        "description": "SGA creatives connects brands with creative people and leads projects across branding, campaigns and cultural experiences.",
        "email": SITE["email"],
        "telephone": SITE["phone_display"],
        "founder": {
            "@type": "Person",
            "name": "Sarah Al-farhan",
            "jobTitle": "Brand and Creative Consultant",
            "sameAs": [SITE["linkedin"], SITE["instagram"]],
        },
    }
    if DOMAIN:
        ld["url"] = DOMAIN + "/"
        ld["logo"] = DOMAIN + "/assets/brand/icon-512.png"
    extra_head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'

    hero_imgs = [
        ("rezet-lookbook-01-hero", "A model from the Rezet Store Lookbook Autumn Winter 2025 in a black track jacket and a long grey pleated skirt.", "hero-img hero-img--side"),
        ("adidas-ways-to-style-01", "A man in a black puffer jacket and red trousers wearing silver Adistar Control 5 sneakers.", "hero-img hero-img--main"),
        ("timberland-rezet-04", "A guest holds up a Timberland boot at the counter during the Timberland × Rezet event.", "hero-img hero-img--side hero-img--right"),
    ]
    hero_media = "".join(
        f'<div class="{cls}">{picture(n, a, "(min-width: 900px) 34vw, 100vw", eager=(k == 1), priority=(k == 1))}</div>'
        for k, (n, a, cls) in enumerate(hero_imgs))

    body = f"""
<section class="hero" aria-labelledby="hero-title">
  <div class="hero-media">{hero_media}</div>
  <div class="hero-content container">
    <h1 id="hero-title" class="hero-title">
      <span class="line"><span>Where brands</span></span>
      <span class="line"><span>meet <em>culture.</em></span></span>
    </h1>
  </div>
</section>

<section id="services" class="section services tone-light" aria-labelledby="services-title">
  <div class="container">
    <header class="section-head" data-reveal>
      <h2 id="services-title" class="section-title rise">{rise_words("For fashion, footwear, lifestyle <em>and culture.</em>")}</h2>
    </header>
    <ol class="svc">{services}
    </ol>
  </div>
</section>

<section id="work" class="work" aria-labelledby="work-title">
  <h2 id="work-title" class="sr-only">Selected work</h2>
  {universes}
</section>

<section id="about" class="section about" aria-labelledby="about-title">
  <div class="container about-grid">
    <div class="about-portrait" data-reveal>{media("sarah-al-farhan-01", "Portrait of Sarah Al-farhan.", "(min-width: 900px) 40vw, 100vw", label="Sarah")}</div>
    <div class="about-body" data-reveal>
      <p class="label">About</p>
      <h2 id="about-title" class="about-name">Sarah <em>Al-farhan</em></h2>
      <p class="about-role">The person behind SGA. Brand and creative consultant.</p>
      <p class="about-stat"><span class="stat-figure">13+</span><span class="stat-text">years across fashion, footwear, branding, marketing, community and culture.</span></p>
      <p class="about-lead">Most recently Brand and Community Manager at Rezet Store. Sarah knows the brand side from the inside: partners, budgets, teams and every detail from the big idea to the smallest execution.</p>
      <ul class="xp-list">{experience}
      </ul>
    </div>
  </div>
  <div class="container">
    <div class="process about-process" data-reveal>
      <p class="label">Process</p>
      <ol class="process-list" aria-label="Process">{process}
      </ol>
    </div>
  </div>
</section>

<section id="contact" class="section contact tone-light" aria-labelledby="contact-title">
  <div class="container">
    <h2 id="contact-title" class="contact-title" data-reveal>Let’s make <em>something happen.</em></h2>
    <ul class="contact-topics" data-reveal>
      <li style="--i:0">Branding</li><li style="--i:1">Campaigns</li><li style="--i:2">Events</li><li style="--i:3">Collaborations</li>
    </ul>
    <a class="contact-email" href="mailto:{SITE['email']}">{SITE['email']}</a>
    <ul class="contact-links">
      <li><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></li>
      <li><a href="{SITE['linkedin']}" rel="noopener">LinkedIn <span aria-hidden="true">↗</span></a></li>
      <li><a href="{SITE['instagram']}" rel="noopener">Instagram <span aria-hidden="true">↗</span></a></li>
    </ul>
  </div>
</section>
"""
    return page(
        title="SGA creatives: Where brands meet culture",
        description="SGA creatives connects brands with creative people and leads projects across branding, campaigns and cultural experiences, with a focus on fashion, footwear, lifestyle and culture.",
        path="/",
        body=body,
        body_class="page-home",
        extra_head=extra_head,
    )


# ---------------------------------------------------------------- case pages

GALLERY_SIZES = {"wide": "100vw", "half": "(min-width: 700px) 50vw, 100vw", "third": "(min-width: 700px) 33vw, 100vw"}


def gallery_item(c: dict, g: dict) -> str:
    layout = g.get("layout", "half")
    if "video" in g:
        v = g["video"]
        m = MANIFEST[f"video:{v}"]
        inner = (
            f'<video controls preload="none" playsinline width="{m["width"]}" height="{m["height"]}" '
            f'poster="/assets/video/{v}-poster.jpg" aria-label="{e(g["label"])}">'
            f'<source src="/assets/video/{v}.mp4" type="video/mp4">'
            f'<p>Your browser cannot play this video. <a href="/assets/video/{v}.mp4">Download the video (MP4, 1.1 MB)</a>.</p>'
            f'</video>'
        )
    else:
        inner = media(g["image"], g.get("alt", ""), GALLERY_SIZES[layout])
    return f'\n      <figure class="g-item g-{layout}" data-reveal>{inner}</figure>'


def case_page(i: int, c: dict) -> str:
    n = len(CASES)
    nxt = CASES[(i + 1) % n]
    facts = "".join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in c["facts"])
    done = "".join(f"<li>{e(x)}</li>" for x in c["done"])
    credits = "".join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in c["credits"])
    gallery = "".join(gallery_item(c, g) for g in c["gallery"])
    programme = ""
    if c.get("programme"):
        rows = "".join(f"""
        <li><span class="label">{e(p['time'])}</span><span class="prog-place">{e(p['place'])}</span><span class="prog-text">{e(p['text'])}</span></li>"""
                       for p in c["programme"])
        programme = f'\n    <ol class="programme" data-reveal>{rows}\n    </ol>'
    provenance = e(c["provenance"]).replace("Sarah Al-farhan", '<span class="nowrap">Sarah Al-farhan</span>')
    mode = c["tone"]["mode"]

    body = f"""
<article class="case tone-{mode}" style="{tone_style(c)}">
  <header class="case-cover">
    <div class="case-cover-text">
      <nav class="case-crumbs" aria-label="Breadcrumb">
        <a href="/#work"><span aria-hidden="true">←</span> All work</a>
      </nav>
      <div>
        <p class="label">{e(c['category'])}</p>
        <h1 class="case-title">{e(c['title'])}</h1>
        <p class="case-subtitle">{e(c['subtitle'])}</p>
      </div>
    </div>
    <figure class="case-cover-media">
      {media(c['lead']['image'], c['lead']['alt'], "(min-width: 900px) 50vw, 100vw", eager=True, priority=True)}
    </figure>
  </header>

  <section class="case-intro container" aria-label="About the project">
    <p class="case-lead" data-reveal>{e(c['intro'])}</p>
    <dl class="facts" data-reveal>{facts}</dl>{programme}
  </section>

  <section class="case-gallery" aria-label="Images from the project">{gallery}
  </section>

  <section class="case-details container" aria-label="Credits">
    <div data-reveal>
      <h2 class="label">{e(c.get('done_heading', 'Sarah’s work'))}</h2>
      <ul class="done">{done}</ul>
    </div>
    <div data-reveal>
      <h2 class="label">Credits</h2>
      <dl class="credits">{credits}</dl>
      <p class="case-provenance">{provenance}</p>
    </div>
  </section>

  <nav class="next-case tone-{nxt['tone']['mode']}" style="{tone_style(nxt)}" aria-label="Next project">
    <a class="next-inner container" href="/work/{nxt['slug']}/">
      <span class="label">Next project</span>
      <span class="next-title">{e(nxt['title'])} <span class="next-arrow" aria-hidden="true">→</span></span>
      <span class="next-media">{media(nxt['card_image'], alt_for(nxt, nxt['card_image']), "(min-width: 900px) 24vw, 40vw")}</span>
    </a>
  </nav>

  <section class="case-cta container" aria-labelledby="cta-title">
    <h2 id="cta-title" class="cta-title">Have a project <em>in mind?</em></h2>
    <div class="hero-actions">
      <a class="btn btn--light" href="mailto:{SITE['email']}">Email Sarah</a>
      <a class="btn btn--ghost" href="/#contact">Contact</a>
    </div>
  </section>
</article>
"""
    lead = c["lead"]["image"]
    og = f"/assets/img/{lead}-{MANIFEST[lead]['fallback']}.jpg" if lead in MANIFEST else OG_IMAGE
    return page(
        title=f"{c['title']}: {c['subtitle']} | SGA creatives",
        description=c["meta_description"],
        path=f"/work/{c['slug']}/",
        body=body,
        body_class=f"page-case tone-page-{mode}",
        og_type="article",
        og_image=og,
        header_tone=mode,
    )


def not_found() -> str:
    links = "".join(f'<li><a href="/work/{c["slug"]}/">{e(c["title"])}</a></li>'
                    for i, c in enumerate(CASES))
    body = f"""
<section class="notfound container" aria-labelledby="nf-title">
  <p class="label">Error 404</p>
  <h1 id="nf-title" class="notfound-title">This page <em>has moved on.</em></h1>
  <div class="hero-actions">
    <a class="btn btn--light" href="/">Front page</a>
    <a class="btn btn--ghost" href="/#contact">Contact</a>
  </div>
  <ul class="nf-links">{links}</ul>
</section>
"""
    return page(title="Page not found | SGA creatives",
                description="The page you were looking for could not be found.",
                path="/404.html", body=body, body_class="page-404", indexable=False)


OUTPUTS: dict[Path, str] = {}  # everything the build produces, used by tools/check.py
DRY_RUN = False


def write(path: Path, text: str) -> None:
    OUTPUTS[path] = text
    if DRY_RUN:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    print("wrote", path.relative_to(ROOT))


def main(dry_run: bool = False) -> dict[Path, str]:
    """Build every generated file. With dry_run=True nothing is written; the outputs are returned."""
    global DRY_RUN
    DRY_RUN = dry_run
    OUTPUTS.clear()
    write(PUBLIC / "index.html", home())
    for i, c in enumerate(CASES):
        write(PUBLIC / "work" / c["slug"] / "index.html", case_page(i, c))
    write(PUBLIC / "404.html", not_found())

    robots = "User-agent: *\nAllow: /\n"
    sitemap = PUBLIC / "sitemap.xml"
    if DOMAIN:
        robots += f"\nSitemap: {DOMAIN}/sitemap.xml\n"
        urls = ["/"] + [f"/work/{c['slug']}/" for c in CASES]
        sitemap_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                       + "".join(f"  <url><loc>{DOMAIN}{u}</loc></url>\n" for u in urls)
                       + "</urlset>\n")
        write(sitemap, sitemap_xml)
    elif sitemap.exists() and not dry_run:
        sitemap.unlink()
    write(PUBLIC / "robots.txt", robots)

    write(PUBLIC / "site.webmanifest", json.dumps({
        "name": "SGA creatives",
        "short_name": "SGA",
        "start_url": "/",
        "display": "browser",
        "background_color": "#F3F0E9",
        "theme_color": "#171918",
        "icons": [
            {"src": "/assets/brand/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/brand/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }, indent=2))

    csp = ("default-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; "
           f"style-src 'self'; style-src-attr 'unsafe-inline'; script-src 'self' 'sha256-{HEAD_SCRIPT_HASH}'; "
           "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'none'; object-src 'none'")
    write(PUBLIC / "_headers", f"""# Cloudflare Pages headers. Generated by tools/build_site.py (do not edit by hand).
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: DENY
  Content-Security-Policy: {csp}

/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/assets/css/*
  Cache-Control: public, max-age=31536000, immutable

/assets/js/*
  Cache-Control: public, max-age=31536000, immutable

/assets/img/*
  Cache-Control: public, max-age=2592000

/assets/video/*
  Cache-Control: public, max-age=2592000

/assets/og/*
  Cache-Control: public, max-age=604800
""")
    return dict(OUTPUTS)


if __name__ == "__main__":
    main()
