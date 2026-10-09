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


def inline_logo() -> str:
    """The wordmark sga.creatives (made by tools/make_brand.py), inline and in currentColor."""
    svg = (PUBLIC / "assets" / "brand" / "sga-creatives-wordmark-dark.svg").read_text()
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


# Top menu: plain words, the current page in red.
NAV = [("Home", "/"), ("Services", "/services/"), ("Projects", "/work/"), ("About me", "/about/"), ("Contact", "/contact/")]


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


def is_current(href: str, path: str) -> bool:
    return path == "/" if href == "/" else path.startswith(href)


def header(path: str = "/") -> str:
    def item(label, href):
        current = ' aria-current="page"' if is_current(href, path) else ""
        return f'<li><a href="{href}"{current}>{label}</a></li>'
    items = "".join(item(label, href) for label, href in NAV)
    return f"""
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-header>
  <div class="header-inner">
    <a class="brand" href="/" aria-label="SGA creatives, home">{inline_logo()}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" hidden>
      <span class="nav-toggle-label" data-label-closed="Menu" data-label-open="Close">Menu</span>
      <span class="nav-toggle-icon" aria-hidden="true"><span></span><span></span></span>
    </button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul class="nav-list">{items}</ul>
      <div class="nav-extra">
        <a href="mailto:{SITE['email']}">{SITE['email']}</a>
        <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a>
      </div>
    </nav>
  </div>
</header>"""


def footer() -> str:
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-top">
      <p class="footer-claim">Where brands meet culture.</p>
      <div class="footer-col footer-contact">
        <ul>
          <li><a href="mailto:{SITE['email']}">{SITE['email']}</a></li>
          <li><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></li>
          <li><a href="{SITE['linkedin']}" rel="noopener">LinkedIn</a></li>
          <li><a href="{SITE['instagram']}" rel="noopener">Instagram</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p class="footer-legal">© <span data-year>{YEAR}</span> SGA creatives</p>
    </div>
  </div>
</footer>"""


def page(*, title: str, description: str, path: str, body: str, body_class: str = "",
         og_type: str = "website", og_image: str = OG_IMAGE, og_image_alt: str = "SGA creatives: Where brands meet culture.",
         extra_head: str = "", indexable: bool = True, jsonld: list | None = None) -> str:
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
<meta name="theme-color" content="#FFFFFF">
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
<link rel="preload" href="/assets/fonts/Inter-VF.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<script>{HEAD_SCRIPT}</script>
<script src="{js}" defer></script>
{extra_head}
</head>
<body class="{body_class}">
{header(path)}
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


# ---------------------------------------------------------------- shared content

# Services: the name, the problem (grey), the solution and what it covers (from Sarah's brief).
# Placeholder copy until Sarah sends her own service texts.
SERVICES = [
    {"name": "Campaigns & creative production",
     "problem": "When your campaigns don’t connect with people.",
     "solution": "We turn cultural insight into campaigns that land.",
     "scope": ["Campaigns", "Editorials", "Content", "Creative partners"]},
    {"name": "Events & experiences",
     "problem": "When your events lack real connection.",
     "solution": "We create experiences that bring people together.",
     "scope": ["Events", "Launches", "Activations", "Brand experiences"]},
    {"name": "Connections & project management",
     "problem": "When your projects lose direction and momentum.",
     "solution": "We bring the right people in and keep it moving.",
     "scope": ["The right people", "Coordination", "Budgets", "Timelines", "Delivery"]},
]

# "My process": four giant words that fill in as you scroll, each with a line in Sarah's own voice.
PROCESS = [
    ("Understand", "I start by listening: the brand, the goal and the people it is for."),
    ("Connect", "I bring in the right creatives, partners and suppliers."),
    ("Create", "Together we shape the idea into a clear, bold concept."),
    ("Deliver", "I run it all the way, down to the last detail on the day."),
]

EXPERIENCE = [   # (company, role), most recent first; no years on the site
    ("Rezet Store", "Brand and Community Manager"),
    ("Envii", "Brand Manager"),
    ("NAKED Copenhagen", "Social Media and Community Manager"),
    ("Bestseller A/S · NAME IT", "Social Media and PR Manager"),
]

INTRO = "We connect brands with creative people across campaigns and cultural experiences."
ABOUT_LEAD = "I connect brands, people and culture through creative vision and practical experience. I bring the right partners together and manage teams, budgets and every detail from concept to execution."
CASE_BY_SLUG = {c["slug"]: c for c in CASES}
# the two hero images on the home page: (case, image). The first is in front, the second smaller behind it
HERO_FRONT = (CASE_BY_SLUG["timberland-rezet"], "timberland-rezet-04")
HERO_BACK = (CASE_BY_SLUG["adidas-ways-to-style"], "adidas-ways-to-style-01")
# the home page opens with Nike; the rest keep the order of content/cases.json
HOME_ORDER = [CASE_BY_SLUG["nike-event-consulting"]] + [c for c in CASES if c["slug"] != "nike-event-consulting"]


def alt_for(c: dict, name: str) -> str:
    if name == c["card_image"] and c.get("card_alt"):   # a card image that is not in the gallery
        return c["card_alt"]
    for g in c["gallery"]:
        if g.get("image") == name and g.get("alt"):
            return g["alt"]
    return c["lead"]["alt"] if c["lead"]["image"] == name else ""


def caption(c: dict, tag: str = "span") -> str:
    """Company on top (quiet), project title below: the caption under every project image."""
    return (f'<{tag} class="cap"><span class="cap-company">{e(c["partners"])}</span>'
            f'<span class="cap-title">{e(c["title"])}</span></{tag}>')


def contact_rows() -> str:
    rows = [
        ("mail", "Email", f"mailto:{SITE['email']}", SITE["email"], ""),
        ("phone", "Phone", f"tel:{SITE['phone_href']}", SITE["phone_display"], ""),
        ("linkedin", "LinkedIn", SITE["linkedin"], "Sarah Al-farhan", ' rel="noopener"'),
        ("instagram", "Instagram", SITE["instagram"], "@sarahalfarhan", ' rel="noopener"'),
    ]
    return "".join(f"""
        <li><a class="reach-row" href="{href}"{rel}><span class="reach-icon">{icon(ic)}</span><span class="reach-kind">{label}</span><span class="reach-value">{e(value)}</span></a></li>"""
                   for ic, label, href, value, rel in rows)


def about_block() -> str:
    """Sarah on the About me page: the portrait (revealed and drifting on scroll), role and experience."""
    experience = "".join(f"""
          <li><span class="xp-company">{e(co)}</span><span class="xp-role">{e(role)}</span></li>"""
                         for co, role in EXPERIENCE)
    photo = f'<div class="about-portrait" data-scroll="parallax">{media("sarah-al-farhan-01", "Sarah Al-farhan on set in a photo studio, working on a laptop.", "(min-width: 900px) 40vw, 100vw", label="Sarah")}</div>'
    return f"""
  <div class="container about-grid">
    {photo}
    <div class="about-body" data-reveal>
      <h2 id="about-title" class="about-name">Sarah Al-farhan</h2>
      <p class="about-role">Brand &amp; Creative Manager</p>
      <p class="about-stat"><span class="stat-figure">13+</span><span class="stat-text">years across fashion, footwear, branding, marketing, community and culture.</span></p>
      <p class="about-lead">{ABOUT_LEAD}</p>
      <ul class="xp-list">{experience}
      </ul>
    </div>
  </div>"""


# ---------------------------------------------------------------- home page

def home() -> str:
    """The headline with two images beside it, a little lower and right of the middle: Timberland × Rezet
    in front, adidas Ways to Style smaller, higher and behind it (it slides out on load and drifts on scroll).
    Then one project at a time in the middle of the page with a small caption under each
    (company, then project title); on phones they snap one per screen as you swipe (main.js
    turns the snapping on only while the feed is in view). Then the promise, on its own."""
    projects = "".join(f"""
    <li class="show-item" data-reveal>
      <a class="show-link" href="/work/{c['slug']}/">
        <div class="show-media">{media(c['card_image'], alt_for(c, c['card_image']), "(min-width: 900px) 34vw, 78vw")}</div>
        {caption(c)}
      </a>
    </li>""" for c in HOME_ORDER)

    website = {"@type": "WebSite", "@id": _id("website"), "url": DOMAIN + "/", "name": "SGA creatives",
               "inLanguage": "en", "publisher": {"@id": _id("org")}}

    body = f"""
<section class="hero container" aria-labelledby="hero-title">
  <h1 id="hero-title" class="hero-title">Where brands <br>meet culture.</h1>
  <div class="hero-stack">
    <div class="hero-back" data-scroll="parallax"><div class="hero-back-inner">{picture(HERO_BACK[1], alt_for(*HERO_BACK), "(min-width: 900px) 18vw, 44vw", eager=True)}</div></div>
    <div class="hero-media">{picture(HERO_FRONT[1], alt_for(*HERO_FRONT), "(min-width: 900px) 24vw, 62vw", eager=True, priority=True)}</div>
  </div>
</section>

<section class="showcase container" aria-labelledby="work-title">
  <h2 id="work-title" class="sr-only">Selected projects</h2>
  <ol class="show-list">{projects}
  </ol>
</section>

<section class="statement" aria-label="What SGA creatives does">
  <div class="container statement-inner">
    <p class="statement-text" data-reveal>{INTRO}</p>
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


# ---------------------------------------------------------------- about page

def about_page() -> str:
    """Sarah (portrait, role, experience) and My process."""
    process = "".join(f"""
        <li class="step" data-scroll="fill"><span class="step-word">{t}</span><span class="step-note">{e(d)}</span></li>"""
                      for t, d in PROCESS)
    body = f"""
<section class="page-head container" aria-labelledby="page-title">
  <h1 id="page-title" class="page-title">About me</h1>
</section>

<section class="about" aria-labelledby="about-title">{about_block()}
</section>

<section class="process container" aria-labelledby="process-title">
  <h2 id="process-title" class="process-title">My process</h2>
  <ol class="process-list">{process}
  </ol>
</section>
"""
    return page(
        title="About me | SGA creatives",
        description="Sarah Al-farhan, Brand & Creative Manager: 13+ years across fashion, footwear, branding, marketing, community and culture, and how she works.",
        path="/about/",
        body=body,
        body_class="page-about",
        jsonld=graph(
            {"@type": "AboutPage", "@id": f"{DOMAIN}/about/#page", "url": f"{DOMAIN}/about/", "name": "About me",
             "isPartOf": {"@id": _id("website")}, "about": {"@id": _id("sarah")}},
            person_ld(),
            breadcrumbs_ld([("Home", "/"), ("About me", "/about/")]),
        ),
    )


# ---------------------------------------------------------------- services page

def services_page() -> str:
    blocks = []
    for i, s in enumerate(SERVICES):
        scope = "".join(f"<li>{e(x)}</li>" for x in s["scope"])
        blocks.append(f"""
    <article class="svc-item" aria-labelledby="svc-{i}" data-reveal>
      <h2 id="svc-{i}" class="svc-name">{e(s['name'])}</h2>
      <div class="svc-body">
        <p class="svc-problem">{e(s['problem'])}</p>
        <p class="svc-solution">{e(s['solution'])}</p>
        <ul class="svc-scope" aria-label="What it covers">{scope}</ul>
      </div>
    </article>""")
    body = f"""
<section class="page-head container" aria-labelledby="page-title">
  <h1 id="page-title" class="page-title">Services</h1>
  <p class="page-lead">For fashion, footwear &amp; lifestyle.</p>
</section>

<section class="services container" aria-label="What SGA creatives does">{"".join(blocks)}
</section>

<section class="page-cta container" aria-labelledby="cta-title">
  <h2 id="cta-title" class="cta-title">Have a project in mind?</h2>
  <a class="text-link" href="/contact/">Get in touch</a>
</section>
"""
    return page(
        title="Services | SGA creatives",
        description="Campaigns and creative production, events and experiences, connections and project management for fashion, footwear and lifestyle brands.",
        path="/services/",
        body=body,
        body_class="page-services",
        jsonld=graph(
            {"@type": "WebPage", "@id": f"{DOMAIN}/services/#page", "url": f"{DOMAIN}/services/", "name": "Services",
             "isPartOf": {"@id": _id("website")}, "about": {"@id": _id("org")}},
            breadcrumbs_ld([("Home", "/"), ("Services", "/services/")]),
        ),
    )


# ---------------------------------------------------------------- contact page

def contact_page() -> str:
    body = f"""
<section class="contact container" aria-labelledby="page-title">
  <h1 id="page-title" class="contact-title">Let’s make something happen.</h1>
  <ul class="contact-topics" data-reveal>
    <li style="--i:0">Branding</li><li style="--i:1">Campaigns</li><li style="--i:2">Events</li><li style="--i:3">Collaborations</li>
  </ul>
  <ul class="reach-list" data-reveal>{contact_rows()}
  </ul>
</section>

<section class="contact-note container" aria-label="About Sarah">
  <p class="contact-note-text">{ABOUT_LEAD}</p>
  <a class="text-link" href="/about/">More about Sarah</a>
</section>
"""
    return page(
        title="Contact | SGA creatives",
        description="Get in touch with Sarah Al-farhan, Brand & Creative Manager at SGA creatives, about branding, campaigns, events and collaborations.",
        path="/contact/",
        body=body,
        body_class="page-contact",
        jsonld=graph(
            {"@type": "ContactPage", "@id": f"{DOMAIN}/contact/#page", "url": f"{DOMAIN}/contact/", "name": "Contact",
             "isPartOf": {"@id": _id("website")}, "about": {"@id": _id("sarah")}},
            person_ld(),
            breadcrumbs_ld([("Home", "/"), ("Contact", "/contact/")]),
        ),
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

    body = f"""
<article class="case">
  <header class="case-cover container">
    <nav class="case-crumbs" aria-label="Breadcrumb">
      <a href="/work/"><span aria-hidden="true">←</span> Projects</a>
    </nav>
    <div class="case-head">
      <p class="cap-company">{e(c['partners'])}</p>
      <h1 class="case-title">{e(c['title'])}</h1>
      <p class="case-subtitle">{e(c['subtitle'])}</p>
    </div>
    <figure class="case-cover-media">
      {media(c['lead']['image'], c['lead']['alt'], "(min-width: 900px) 40vw, 86vw", eager=True, priority=True)}
    </figure>
  </header>

  <section class="case-intro container" aria-label="About the project">
    <p class="case-lead" data-reveal>{e(c['intro'])}</p>
    <dl class="facts" data-reveal><div><dt>Category</dt><dd>{e(c['category'])}</dd></div>{facts}</dl>{programme}
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

  <nav class="next-case container" aria-label="Next project">
    <a class="next-inner" href="/work/{nxt['slug']}/">
      <span class="next-media">{media(nxt['card_image'], alt_for(nxt, nxt['card_image']), "(min-width: 900px) 14rem, 9rem")}</span>
      <span class="label">Next project</span>
      {caption(nxt)}
    </a>
  </nav>

  <section class="page-cta container" aria-labelledby="cta-title">
    <h2 id="cta-title" class="cta-title">Have a project in mind?</h2>
    <details class="reach">
      <summary class="btn reach-toggle"><span>Get in touch</span><span class="reach-plus" aria-hidden="true"></span></summary>
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
        body_class="page-case",
        og_type="article",
        og_image=f"/assets/og/{c['slug']}.jpg",
        og_image_alt=f"{c['title']}, {c['subtitle']}. A project in the SGA creatives portfolio.",
        jsonld=graph(case_ld(c), breadcrumbs_ld([("Home", "/"), ("Projects", "/work/"), (c["title"], f"/work/{c['slug']}/")])),
    )


# ---------------------------------------------------------------- projects (/work/)

def portfolio() -> str:
    """/work/: every project in a calm two-column grid, same caption as on the home page."""
    items = "".join(f"""
    <li class="pf-item" data-reveal>
      <a class="show-link" href="/work/{c['slug']}/">
        <div class="pf-media">{media(c['card_image'], alt_for(c, c['card_image']), "(min-width: 900px) 40vw, 92vw", eager=(i < 2))}</div>
        {caption(c)}
        <span class="pf-category">{e(c['category'])}</span>
      </a>
    </li>""" for i, c in enumerate(CASES))
    body = f"""
<section class="page-head container" aria-labelledby="page-title">
  <h1 id="page-title" class="page-title">Projects</h1>
</section>
<section class="pf container" aria-label="All projects">
  <ol class="pf-grid">{items}
  </ol>
</section>
"""
    return page(
        title="Projects | SGA creatives",
        description="Selected projects from Sarah Al-farhan’s work across brands, campaigns and cultural experiences: adidas, Rezet Store, Timberland and Nike.",
        path="/work/",
        body=body,
        body_class="page-portfolio",
        og_image="/assets/og/portfolio.jpg",
        og_image_alt="SGA creatives projects: adidas, Rezet Store, Timberland and Nike.",
        jsonld=graph(
            {"@type": "CollectionPage", "@id": f"{DOMAIN}/work/#page", "url": f"{DOMAIN}/work/", "name": "Projects",
             "isPartOf": {"@id": _id("website")}, "about": {"@id": _id("sarah")},
             "mainEntity": {"@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": i + 1, "url": f"{DOMAIN}/work/{c['slug']}/", "name": c["title"]}
                 for i, c in enumerate(CASES)]}},
            breadcrumbs_ld([("Home", "/"), ("Projects", "/work/")]),
        ),
    )


def not_found() -> str:
    links = "".join(f'<li><a href="/work/{c["slug"]}/">{e(c["title"])}</a></li>' for c in CASES)
    body = f"""
<section class="notfound container" aria-labelledby="nf-title">
  <p class="label">Error 404</p>
  <h1 id="nf-title" class="notfound-title">This page has moved on.</h1>
  <div class="nf-actions">
    <a class="btn" href="/">Home</a>
    <a class="btn btn--ghost" href="/contact/">Contact</a>
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
    write(PUBLIC / "services" / "index.html", services_page())
    write(PUBLIC / "about" / "index.html", about_page())
    write(PUBLIC / "contact" / "index.html", contact_page())
    write(PUBLIC / "404.html", not_found())

    robots = "User-agent: *\nAllow: /\n"
    sitemap = PUBLIC / "sitemap.xml"
    if DOMAIN:
        robots += f"\nSitemap: {DOMAIN}/sitemap.xml\n"
        urls = ["/", "/services/", "/work/", "/about/", "/contact/"] + [f"/work/{c['slug']}/" for c in CASES]
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
        "background_color": "#FFFFFF",
        "theme_color": "#FFFFFF",
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
