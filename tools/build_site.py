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
OG_IMAGE = "/assets/og/home.jpg"   # share images are made by tools/make_share_images.mjs

# Runs before first paint: flags JS support (for reveal animations) and removes
# the flag again if main.js never loads, so content can never stay hidden.
HEAD_SCRIPT = (
    "document.documentElement.classList.add('js');"
    "setTimeout(function(){if(!window.sgaReady)document.documentElement.classList.remove('js')},2500);"
)
HEAD_SCRIPT_HASH = base64.b64encode(hashlib.sha256(HEAD_SCRIPT.encode()).digest()).decode()


def e(text: str) -> str:
    return escape(text, quote=True)


def minify_css(css: str) -> str:
    """Conservative minifier: drops comments and collapses whitespace around { } ; , and >.
    It never touches spaces inside selectors like `.a :focus` or inside media queries."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,])\s*", r"\1", css)
    css = css.replace(";}", "}")
    return css.strip() + "\n"


CSS_MIN = minify_css((PUBLIC / "assets" / "css" / "main.css").read_text())


def asset_version(path: str) -> str:
    if path == "/assets/css/main.min.css":   # hash what will be written, not what is on disk
        data = CSS_MIN.encode()
    else:
        data = (PUBLIC / path.lstrip("/")).read_bytes()
    return f"{path}?v={hashlib.sha256(data).hexdigest()[:10]}"


def absolute(path: str) -> str:
    return f"{DOMAIN}{path}" if DOMAIN else path


def inline_mark() -> str:
    """The S mark (paper + acid on ink), inline and decorative."""
    svg = (PUBLIC / "assets" / "brand" / "sga-creatives-mark.svg").read_text()
    svg = re.sub(r'<title id="t">.*?</title>', "", svg)
    svg = svg.replace(' role="img" aria-labelledby="t"', ' aria-hidden="true" focusable="false"')
    return re.sub(r' width="\d+" height="\d+"', "", svg, count=1)


# 24px line icons for the contact buttons (stroke = currentColor)
ICONS = {
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "phone": '<path d="M5.5 3.5h3l1.8 4.6-2.3 1.4a11.5 11.5 0 0 0 6.5 6.5l1.4-2.3 4.6 1.8v3a2 2 0 0 1-2 2A17 17 0 0 1 3.5 5.5a2 2 0 0 1 2-2z"/>',
    "linkedin": '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 10.5V17M8 7.5v.01M12 17v-6.5M12 13.2c0-1.6 1.1-2.7 2.5-2.7s2.5 1 2.5 2.7V17"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5.5"/><circle cx="12" cy="12" r="4"/><path d="M17.3 6.7v.01"/>',
}


def icon(name: str) -> str:
    return (f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


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


NAV_LEFT = [("Portfolio", "/work/"), ("About", "/#about")]                 # top menu
NAV = [("Portfolio", "/work/"), ("Services", "/#services"), ("About", "/#about"), ("Contact", "/#contact")]  # footer


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


def header(tone: str = "dark", path: str = "/") -> str:
    def item(label, href):
        current = ' aria-current="page"' if href == "/work/" and path.startswith("/work/") else ""
        return f'<li><a href="{href}"{current}>{label}</a></li>'
    left = "".join(item(label, href) for label, href in NAV_LEFT)
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
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-top">
      <p class="footer-claim">Where brands <em>meet culture.</em></p>
      <nav class="footer-col" aria-label="Footer"><ul>{items}</ul></nav>
      <div class="footer-col footer-contact">
        <ul>
          <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
          <li><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></li>
          <li><a href="{SITE['linkedin']}" rel="noopener">LinkedIn</a></li>
          <li><a href="{SITE['instagram']}" rel="noopener">Instagram</a></li>
        </ul>
      </div>
    </div>
    <a class="footer-wordmark" href="/" aria-label="SGA creatives, home" data-reveal>{inline_logo()}</a>
    <div class="footer-bottom">
      <p class="footer-legal"><span class="footer-mark">{inline_mark()}</span>© <span data-year>{YEAR}</span> SGA creatives</p>
      <a href="#top" class="back-to-top">Back to top</a>
    </div>
  </div>
</footer>"""


def page(*, title: str, description: str, path: str, body: str, body_class: str = "",
         og_type: str = "website", og_image: str = OG_IMAGE, og_image_alt: str = "SGA creatives: Where brands meet culture.",
         extra_head: str = "", indexable: bool = True, header_tone: str = "dark", jsonld: list | None = None) -> str:
    canonical = f'<link rel="canonical" href="{DOMAIN}{path}">' if DOMAIN and indexable else ""
    og_url = f'<meta property="og:url" content="{DOMAIN}{path}">' if DOMAIN and indexable else ""
    robots = "" if indexable else '<meta name="robots" content="noindex">'
    css = asset_version("/assets/css/main.min.css")
    js = asset_version("/assets/js/main.js")
    return f"""<!doctype html>
<html lang="en" id="top">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
{canonical}{robots}
<meta name="theme-color" content="#0E0F0F">
<meta property="og:site_name" content="SGA creatives">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta name="author" content="SGA creatives">
<meta property="og:image" content="{absolute(og_image)}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(og_image_alt)}">
<meta property="og:locale" content="en_GB">
{og_url}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<meta name="twitter:image" content="{absolute(og_image)}">
<meta name="twitter:image:alt" content="{e(og_image_alt)}">
{"".join(f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>' for block in (jsonld or []))}
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
{header(header_tone, path)}
<main id="main" tabindex="-1">
{body}
</main>
{footer()}
</body>
</html>
"""


# ---------------------------------------------------------------- structured data (search engines only)

def _id(frag: str) -> str:
    return f"{DOMAIN}/#{frag}"


def org_ld() -> dict:
    return {
        "@type": "Organization", "@id": _id("org"), "name": "SGA creatives", "url": DOMAIN + "/",
        "logo": DOMAIN + "/assets/brand/icon-512.png",
        "description": "SGA creatives connects brands with creative people and leads projects across branding, campaigns and cultural experiences.",
        "email": SITE["email"], "telephone": SITE["phone_display"],
        "founder": {"@id": _id("sarah")},
        "knowsAbout": ["Brand strategy", "Creative direction", "Campaigns", "Creative production", "Events", "Brand experiences", "Project management"],
    }


def person_ld() -> dict:
    ld = {
        "@type": "Person", "@id": _id("sarah"), "name": "Sarah Al-farhan", "jobTitle": "Brand & Creative Manager",
        "sameAs": [SITE["linkedin"], SITE["instagram"]], "worksFor": {"@id": _id("org")},
    }
    if "sarah-al-farhan-01" in MANIFEST:
        ld["image"] = f"{DOMAIN}/assets/img/sarah-al-farhan-01-800.jpg"
    return ld


def breadcrumbs_ld(trail: list[tuple[str, str]]) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": name, "item": DOMAIN + path} for i, (name, path) in enumerate(trail)]}


def graph(*nodes: dict) -> list[dict]:
    return [{"@context": "https://schema.org", "@graph": list(nodes)}] if DOMAIN else []


def case_ld(c: dict) -> dict:
    ld = {
        "@type": "CreativeWork", "@id": f"{DOMAIN}/work/{c['slug']}/#work",
        "name": f"{c['title']}: {c['subtitle']}", "headline": c["title"], "description": c["meta_description"],
        "url": f"{DOMAIN}/work/{c['slug']}/", "inLanguage": "en", "genre": c["category"],
        "isPartOf": {"@id": f"{DOMAIN}/work/#page"}, "publisher": {"@id": _id("org")},
    }
    lead = c["lead"]["image"]
    if lead in MANIFEST:
        ld["image"] = f"{DOMAIN}/assets/img/{lead}-{MANIFEST[lead]['fallback']}.jpg"
    # credit Sarah only where her role is documented on the page itself
    if any(k.startswith("Sarah") for k, _ in c["facts"]):
        ld["creator"] = {"@id": _id("sarah")}
    return ld


# ---------------------------------------------------------------- home page

# (service, problem, solution). Each row is two boxes that slide together on scroll and lock:
# the problem on the left, the solution on the right. The service name is a hidden heading
# for screen readers and search engines. Keep the lines short and roughly equal in length.
SERVICES = [
    ("Campaigns & creative production", "Your campaigns don’t connect with people.", "We turn cultural insight into campaigns that land."),
    ("Events & experiences", "Your events lack real connection.", "We create experiences that bring people together."),
    ("Connections & project management", "Your projects lose direction and momentum.", "We bring the right people in and keep it moving."),
]

# "My process": four giant words that fill in as you scroll, each with a line in Sarah's own voice.
PROCESS = [
    ("Understand", "I start by listening: the brand, the goal and the people it is for."),
    ("Connect", "I bring in the right creatives, partners and suppliers."),
    ("Create", "Together we shape the idea into a clear, bold concept."),
    ("Deliver", "I run it all the way, down to the last detail on the day."),
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
    parts = re.split(r"(<(?:em|strong)>.*?</(?:em|strong)>)", html_text)
    out, i = [], 0
    for part in parts:
        if not part.strip():
            continue
        m = re.match(r"<(em|strong)>(.*)</\1>$", part)
        tag, inner = (m.group(1), m.group(2)) if m else (None, part)
        spans = []
        for w in inner.split():
            spans.append(f'<span class="rw"><span style="--i:{i}">{w}</span></span>')
            i += 1
        chunk = " ".join(spans)
        out.append(f"<{tag}>{chunk}</{tag}>" if tag else chunk)
    return " ".join(out)


def home() -> str:
    universes = "".join(universe(i, c) for i, c in enumerate(CASES))
    services = "".join(f"""
      <li class="svc-row" style="--tilt:{1 if i % 2 == 0 else -1}">
        <h3 class="sr-only">{e(t)}</h3>
        <div class="svc-box svc-problem"><p class="svc-line">{e(prob)}</p></div>
        <div class="svc-box svc-solution">
          <span class="svc-key" aria-hidden="true"></span>
          <p class="svc-line">{e(sol)}</p>
        </div>
      </li>""" for i, (t, prob, sol) in enumerate(SERVICES))
    process = "".join(f"""
        <li class="step" data-scroll="fill"><span class="step-word">{t}</span><span class="step-note">{e(d)}</span></li>"""
                      for t, d in PROCESS)
    experience = "".join(f"""
          <li><span class="xp-company">{e(co)}</span><span class="xp-role">{e(role)}</span><span class="xp-years">{yrs}</span></li>"""
                         for co, role, yrs in EXPERIENCE)

    website = {"@type": "WebSite", "@id": _id("website"), "url": DOMAIN + "/", "name": "SGA creatives",
               "inLanguage": "en", "publisher": {"@id": _id("org")}}

    hero_imgs = [
        ("rezet-lookbook-01-hero", "A model from the Rezet Store Lookbook Autumn Winter 2025 in a black track jacket and a long grey pleated skirt.", "hero-img hero-img--side"),
        ("adidas-ways-to-style-01", "A man in a black puffer jacket and red trousers wearing silver Adistar Control 5 sneakers.", "hero-img hero-img--main"),
        ("timberland-rezet-04", "A guest holds up a Timberland boot at the counter during the Timberland × Rezet event.", "hero-img hero-img--side hero-img--right"),
    ]
    # Only the right image (Timberland) shows on phones, so it is the one fetched first; the other two
    # are lazy, which also means phones never download them (they are display:none there).
    hero_media = "".join(
        f'<div class="{cls}">{picture(n, a, "(min-width: 900px) 34vw, 100vw", eager=(k == 2), priority=(k == 2))}</div>'
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
      <h2 id="services-title" class="section-title rise is-light">{rise_words("For fashion, footwear &amp; <strong>lifestyle.</strong>")}</h2>
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
    <div class="about-portrait" data-scroll="parallax">{media("sarah-al-farhan-01", "Sarah Al-farhan on set in a photo studio, working on a laptop.", "(min-width: 900px) 40vw, 100vw", label="Sarah")}</div>
    <div class="about-body" data-reveal>
      <h2 id="about-title" class="about-name">Sarah <em>Al-farhan</em></h2>
      <p class="about-role">Brand &amp; Creative Manager</p>
      <p class="about-stat"><span class="stat-figure">13+</span><span class="stat-text">years across fashion, footwear, branding, marketing, community and culture.</span></p>
      <p class="about-lead">Sarah connects brands, people and culture through creative vision and practical experience. She brings the right partners together and manages teams, budgets and every detail from concept to execution.</p>
      <ul class="xp-list">{experience}
      </ul>
    </div>
  </div>
  <div class="container">
    <div class="process about-process">
      <h3 class="process-title">My <em>process</em></h3>
      <ol class="process-list">{process}
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
    <ul class="contact-icons" data-reveal>
      <li style="--i:0"><a class="icon-btn" href="mailto:{SITE['email']}">{icon("mail")}<span class="icon-label">Email</span><span class="sr-only"> Sarah at {SITE['email']}</span></a></li>
      <li style="--i:1"><a class="icon-btn" href="tel:{SITE['phone_href']}">{icon("phone")}<span class="icon-label">Call</span><span class="sr-only"> Sarah on {SITE['phone_display']}</span></a></li>
      <li style="--i:2"><a class="icon-btn" href="{SITE['linkedin']}" rel="noopener">{icon("linkedin")}<span class="icon-label">LinkedIn</span><span class="sr-only">: Sarah Al-farhan</span></a></li>
      <li style="--i:3"><a class="icon-btn" href="{SITE['instagram']}" rel="noopener">{icon("instagram")}<span class="icon-label">Instagram</span><span class="sr-only">: @sarahalfarhan</span></a></li>
    </ul>
  </div>
</section>
"""
    return page(
        title="SGA creatives: Where brands meet culture",
        description="SGA creatives connects brands with creative people and leads projects in branding, campaigns and cultural experiences for fashion, footwear and lifestyle.",
        path="/",
        body=body,
        body_class="page-home",
        og_image_alt="SGA creatives: Where brands meet culture. Portraits from the Rezet Lookbook, adidas Ways to Style and Timberland × Rezet.",
        jsonld=graph(org_ld(), person_ld(), website),
    )


# ---------------------------------------------------------------- case pages

GALLERY_SIZES = {"wide": "100vw", "half": "(min-width: 700px) 50vw, 100vw", "third": "(min-width: 700px) 33vw, 50vw"}


def gallery_item(c: dict, g: dict) -> str:
    layout = g.get("layout", "half")
    if "video" in g:
        v = g["video"]
        m = MANIFEST[f"video:{v}"]
        inner = (
            f'<video controls preload="none" playsinline width="{m["width"]}" height="{m["height"]}" '
            f'poster="/assets/video/{v}-poster.webp" aria-label="{e(g["label"])}">'
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
        <a href="/work/"><span aria-hidden="true">←</span> Portfolio</a>
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
      <span class="next-media">{media(nxt['card_image'], alt_for(nxt, nxt['card_image']), "(min-width: 900px) 17rem, 6rem")}</span>
    </a>
  </nav>

  <section class="case-cta container" aria-labelledby="cta-title">
    <h2 id="cta-title" class="cta-title">Have a project <em>in mind?</em></h2>
    <details class="reach">
      <summary class="btn btn--light reach-toggle"><span>Get in touch</span><span class="reach-plus" aria-hidden="true"></span></summary>
      <div class="reach-options">
        <a class="reach-option" href="mailto:{SITE['email']}">{icon("mail")}<span>Email</span><span class="sr-only"> Sarah at {SITE['email']}</span></a>
        <a class="reach-option" href="tel:{SITE['phone_href']}">{icon("phone")}<span>Call</span><span class="sr-only"> Sarah on {SITE['phone_display']}</span></a>
      </div>
    </details>
  </section>
</article>
"""
    return page(
        title=f"{c['title']}: {c['subtitle']} | SGA creatives",
        description=c["meta_description"],
        path=f"/work/{c['slug']}/",
        body=body,
        body_class=f"page-case tone-page-{mode}",
        og_type="article",
        og_image=f"/assets/og/{c['slug']}.jpg",
        og_image_alt=f"{c['title']}, {c['subtitle']}. A project in the SGA creatives portfolio.",
        jsonld=graph(case_ld(c), breadcrumbs_ld([("Home", "/"), ("Portfolio", "/work/"), (c["title"], f"/work/{c['slug']}/")])),
        header_tone=mode,
    )


def portfolio() -> str:
    """/work/: a bold index of all projects. Hovering a row fills it with the case tone and
    lets the project image follow the cursor (main.js); on touch screens a thumbnail shows."""
    rows = "".join(f"""
      <li class="pf-item" style="{tone_style(c)}">
        <a class="pf-link" href="/work/{c['slug']}/">
          <span class="pf-name">{e(c['title'])}</span>
          <span class="pf-meta"><span>{e(c['category'])}</span><span>{e(c['partners'])}</span></span>
          <span class="pf-thumb">{media(c['card_image'], alt_for(c, c['card_image']), "(min-width: 900px) 22rem, 7rem")}</span>
        </a>
      </li>""" for c in CASES)
    body = f"""
<section class="pf container" aria-labelledby="pf-title">
  <h1 id="pf-title" class="pf-heading rise"><span class="rw"><span style="--i:0">Portfolio</span></span></h1>
  <ol class="pf-list" data-pf>{rows}
  </ol>
</section>
"""
    return page(
        title="Portfolio | SGA creatives",
        description="Selected projects from Sarah Al-farhan’s work across brands, campaigns and cultural experiences: adidas, Rezet Store, Timberland and Nike.",
        path="/work/",
        body=body,
        body_class="page-portfolio",
        og_image="/assets/og/portfolio.jpg",
        og_image_alt="SGA creatives portfolio: adidas, Rezet Store, Timberland and Nike.",
        jsonld=graph(
            {"@type": "CollectionPage", "@id": f"{DOMAIN}/work/#page", "url": f"{DOMAIN}/work/", "name": "Portfolio",
             "isPartOf": {"@id": _id("website")}, "about": {"@id": _id("sarah")},
             "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "url": f"{DOMAIN}/work/{c['slug']}/", "name": c["title"]}
                 for i, c in enumerate(CASES)]}},
            breadcrumbs_ld([("Home", "/"), ("Portfolio", "/work/")]),
        ),
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
    write(PUBLIC / "assets" / "css" / "main.min.css", CSS_MIN)
    write(PUBLIC / "index.html", home())
    for i, c in enumerate(CASES):
        write(PUBLIC / "work" / c["slug"] / "index.html", case_page(i, c))
    write(PUBLIC / "work" / "index.html", portfolio())
    write(PUBLIC / "404.html", not_found())

    robots = "User-agent: *\nAllow: /\n"
    sitemap = PUBLIC / "sitemap.xml"
    if DOMAIN:
        robots += f"\nSitemap: {DOMAIN}/sitemap.xml\n"
        urls = ["/", "/work/"] + [f"/work/{c['slug']}/" for c in CASES]
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
