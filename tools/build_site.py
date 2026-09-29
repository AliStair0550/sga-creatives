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


NAV = [("Work", "/#work"), ("Services", "/#services"), ("About", "/#about")]


def header() -> str:
    items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in NAV)
    return f"""
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header" data-header>
  <div class="container header-inner">
    <a class="brand" href="/" aria-label="SGA creatives, home">{inline_logo()}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" hidden>
      <span class="nav-toggle-label" data-label-closed="Menu" data-label-open="Close">Menu</span>
      <span class="nav-toggle-icon" aria-hidden="true"><span></span><span></span></span>
    </button>
    <nav id="site-nav" class="site-nav" aria-label="Main">
      <ul class="nav-list">
        {items}
        <li><a class="nav-cta" href="/#contact">Contact</a></li>
      </ul>
      <div class="nav-extra">
        <p class="label">Get in touch</p>
        <a href="mailto:{SITE['email']}">{SITE['email']}</a>
        <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a>
      </div>
    </nav>
  </div>
</header>"""


def footer() -> str:
    items = "".join(f'<li><a href="{href}">{label}</a></li>' for label, href in NAV + [("Contact", "/#contact")])
    work = "".join(f'<li><a href="/work/{c["slug"]}/">{e(c["title"])}</a></li>' for c in CASES)
    return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a class="brand brand--footer" href="/" aria-label="SGA creatives, home">{inline_logo("stacked")}</a>
        <p>Connecting brands with creative people, across branding, campaigns and cultural experiences.</p>
      </div>
      <nav class="footer-col" aria-label="Footer">
        <p class="label">Navigate</p>
        <ul>{items}</ul>
      </nav>
      <div class="footer-col">
        <p class="label">Work</p>
        <ul>{work}</ul>
      </div>
      <div class="footer-col">
        <p class="label">Contact</p>
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
         indexable: bool = True) -> str:
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
<meta name="theme-color" content="#F3F0E9">
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
<link rel="preload" href="/assets/fonts/InstrumentSerif-Regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/Archivo-VF.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{css}">
<script>{HEAD_SCRIPT}</script>
<script src="{js}" defer></script>
{extra_head}
</head>
<body class="{body_class}">
{header()}
<main id="main" tabindex="-1">
{body}
</main>
{footer()}
</body>
</html>
"""


# ---------------------------------------------------------------- home page

SERVICES = [
    ("Brand strategy & creative direction",
     "Positioning, concepts, storytelling and visual direction that make a brand clear, distinctive and relevant to the culture it wants to be part of.",
     ["Positioning", "Concepts", "Storytelling", "Visual direction"]),
    ("Campaigns & creative production",
     "Campaigns, editorials and content, from the first idea to the finished material, with the right creative partners on board.",
     ["Campaigns", "Editorials", "Content", "Creative partners"]),
    ("Experiences & activations",
     "Events, launches and brand experiences that give people a reason to show up, take part and remember the brand afterwards.",
     ["Events", "Launches", "Brand experiences"]),
    ("Creative connections & project management",
     "The right people for the job, and the coordination to match: budgets, timelines, partners and delivery handled from start to finish.",
     ["The right people", "Coordination", "Budgets", "Timelines", "Delivery"]),
]

PROCESS = [
    ("Understand", "Clarifying the brand, the goal and the audience, along with the practical frame: budget, timeline and what a good result looks like."),
    ("Connect", "Putting the right team together: creatives, partners and suppliers who fit the brief and the culture around it."),
    ("Create", "Developing the concept and turning it into a clear plan, with creative direction from the first sketch to the final detail."),
    ("Deliver", "Producing and running the project: coordination, follow-up and care in the execution, right through to the day itself."),
]

EXPERIENCE = [
    ("Rezet Store", "Brand and Community Manager", "2025-2026"),
    ("Envii", "Brand Manager", "2024-2025"),
    ("NAKED Copenhagen", "Social Media and Community Manager", "2023-2024"),
    ("Bestseller A/S · NAME IT", "Social Media and PR Manager", "2021-2023"),
]

# Grid placements for the cards on the home page; they repeat for a sixth case onwards.
CARD_LAYOUT = ["card--a", "card--b", "card--c", "card--d", "card--e"]


def work_card(i: int, c: dict) -> str:
    num = f"{i + 1:02d}"
    img_name = c["card_image"]
    alt = next((g["alt"] for g in c["gallery"] if g.get("image") == img_name), None) or c["lead"]["alt"]
    sizes = "(min-width: 900px) 55vw, (min-width: 600px) 50vw, 100vw" if i % 5 in (0, 4) else \
            "(min-width: 900px) 40vw, (min-width: 600px) 50vw, 90vw"
    return f"""
    <article class="card {CARD_LAYOUT[i % len(CARD_LAYOUT)]}" data-reveal>
      <div class="card-media">
        {picture(img_name, alt, sizes)}
      </div>
      <div class="card-body">
        <p class="card-meta"><span class="num">{num}</span><span class="label">{e(c['category'])}</span></p>
        <h3 class="card-title"><a href="/work/{c['slug']}/">{e(c['title'])}</a></h3>
        <p class="card-partners">{e(c['partners'])}</p>
        <p class="card-intro">{e(c['card_intro'])}</p>
        <p class="card-link" aria-hidden="true">View case <span>→</span></p>
      </div>
    </article>"""


def home() -> str:
    cards = "".join(work_card(i, c) for i, c in enumerate(CASES))
    services = "".join(f"""
      <li class="service" data-reveal>
        <span class="num">{i + 1:02d}</span>
        <h3>{e(t)}</h3>
        <p>{e(d)}</p>
        <p class="service-tags">{' · '.join(e(x) for x in tags)}</p>
      </li>""" for i, (t, d, tags) in enumerate(SERVICES))
    process = "".join(f"""
      <li class="step" data-reveal>
        <span class="num">{i + 1:02d}</span>
        <h3>{t}{'<span class="step-arrow" aria-hidden="true">→</span>' if i < len(PROCESS) - 1 else ''}</h3>
        <p>{e(d)}</p>
      </li>""" for i, (t, d) in enumerate(PROCESS))
    experience = "".join(f"""
          <li><span class="xp-company">{e(co)}</span><span class="xp-role">{e(role)}</span><span class="xp-years">{yrs}</span></li>"""
                         for co, role, yrs in EXPERIENCE)
    ticker_words = ["Fashion", "Footwear", "Lifestyle", "Culture", "Branding", "Campaigns", "Experiences", "Creative connections"]
    ticker_run = "".join(f'<span>{w}</span><i aria-hidden="true"></i>' for w in ticker_words)

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

    body = f"""
<section class="hero container" aria-labelledby="hero-title">
  <div class="hero-text">
    <p class="label hero-eyebrow">Branding · Campaigns · Experiences</p>
    <h1 id="hero-title" class="hero-title">
      <span class="line"><span>Where brands</span></span>
      <span class="line"><span>meet <em>culture.</em></span></span>
    </h1>
    <p class="hero-lead">SGA creatives connects brands with creative people and leads projects across branding, campaigns and cultural experiences.</p>
    <div class="hero-actions">
      <a class="btn btn--solid" href="#work">Explore the work <span aria-hidden="true">↓</span></a>
      <a class="btn btn--line" href="#contact">Let’s talk</a>
    </div>
  </div>
  <div class="hero-media">
    <figure class="hero-main">
      {picture("adidas-kiosk-04", "Three people seen from behind on a city street, wearing Rezet Store × adidas Originals Kiosk T-shirts.", "(min-width: 900px) 42vw, 92vw", eager=True, priority=True)}
      <figcaption><a href="/work/adidas-kiosk/"><span class="num">01</span> adidas Kiosk <span class="muted">Rezet Store × adidas Originals</span></a></figcaption>
    </figure>
    <figure class="hero-inset" aria-hidden="true">
      {picture("timberland-rezet-03", "", "(min-width: 900px) 16vw, 36vw", eager=True)}
    </figure>
  </div>
</section>

<div class="ticker" aria-hidden="true">
  <div class="ticker-track"><div class="ticker-run">{ticker_run}</div><div class="ticker-run">{ticker_run}</div></div>
</div>

<section id="work" class="section work container" aria-labelledby="work-title">
  <header class="section-head" data-reveal>
    <p class="label"><span class="num">({len(CASES):02d})</span> Projects</p>
    <h2 id="work-title" class="section-title">Selected work</h2>
    <div class="section-intro">
      <p>Selected projects from <span class="nowrap">Sarah Al-farhan’s</span> work across brands, campaigns and cultural experiences.</p>
      <p class="muted">The projects were created in Sarah’s previous roles, including at Rezet Store and as a consultant for Nike. Each case lists her documented role.</p>
    </div>
  </header>
  <div class="work-grid">
    {cards}
  </div>
</section>

<section id="services" class="section services" aria-labelledby="services-title">
  <div class="container">
    <header class="section-head" data-reveal>
      <p class="label"><span class="num">(04)</span> Services</p>
      <h2 id="services-title" class="section-title">From the first idea <em>to the final detail.</em></h2>
      <div class="section-intro">
        <p>For fashion, footwear, lifestyle and culture brands that want to be part of the conversation, not just advertise in it.</p>
      </div>
    </header>
    <ol class="service-list">
      {services}
    </ol>
  </div>
</section>

<section id="about" class="section about container" aria-labelledby="about-title">
  <header class="section-head" data-reveal>
    <p class="label">About</p>
    <h2 id="about-title" class="section-title">The person <em>behind SGA.</em></h2>
  </header>
  <div class="about-grid">
    <div class="about-stat" data-reveal>
      <p class="stat-figure">13<span>+</span></p>
      <p class="stat-text">years of experience across fashion, footwear, branding, marketing, community and culture.</p>
    </div>
    <div class="about-body" data-reveal>
      <p class="about-lead">SGA creatives is led by <span class="nowrap">Sarah Al-farhan</span>, a brand and creative consultant with more than thirteen years of experience across fashion, footwear, branding, marketing, community and culture.</p>
      <p>Most recently, Sarah was Brand and Community Manager at Rezet Store, where she owned the visual identity, creative direction and brand strategy, managed relationships with brand partners and led campaigns and activations from concept to execution. Before that, she was Brand Manager at Envii, Social Media and Community Manager at NAKED Copenhagen, and Social Media and PR Manager for NAME IT at Bestseller.</p>
      <p>For clients, that means a partner who knows the brand side from the inside: pitching concepts, negotiating budgets, working with internal and external teams, and caring about every part of the experience, from the bigger idea to the smallest execution.</p>
      <blockquote class="about-quote">
        <p>“I enjoy combining strategy, creativity, and culture to create meaningful brand experiences that connect with people.”</p>
        <footer>Sarah Al-farhan</footer>
      </blockquote>
      <h3 class="label xp-title">Selected experience</h3>
      <ul class="xp-list">{experience}
      </ul>
      <p class="muted small">Education: Bachelor in Digital Concept Development and Multimedia Designer, Aarhus Business Academy.</p>
    </div>
  </div>
</section>

<section class="section process" aria-labelledby="process-title">
  <div class="container">
    <header class="section-head" data-reveal>
      <p class="label">Process</p>
      <h2 id="process-title" class="section-title">How a project <em>comes together.</em></h2>
    </header>
    <ol class="process-list">
      {process}
    </ol>
  </div>
</section>

<section id="contact" class="section contact" aria-labelledby="contact-title">
  <div class="container">
    <p class="label">Contact</p>
    <h2 id="contact-title" class="contact-title" data-reveal>Let’s make <em>something happen.</em></h2>
    <div class="contact-grid" data-reveal>
      <p class="contact-intro">Planning a brand project, a campaign, an event or a collaboration? Get in touch for a conversation about what you want to create.</p>
      <div class="contact-main">
        <a class="contact-email" href="mailto:{SITE['email']}">{SITE['email']}</a>
        <dl class="contact-list">
          <div><dt>Phone</dt><dd><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></dd></div>
          <div><dt>LinkedIn</dt><dd><a href="{SITE['linkedin']}" rel="noopener">Sarah Al-farhan <span aria-hidden="true">↗</span></a></dd></div>
          <div><dt>Instagram</dt><dd><a href="{SITE['instagram']}" rel="noopener">@sarahalfarhan <span aria-hidden="true">↗</span></a></dd></div>
        </dl>
      </div>
    </div>
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

def gallery_item(c: dict, g: dict) -> str:
    style = f'--span:{g.get("span", 6)};--start:{g.get("start", "auto")}'
    shift = " is-shifted" if g.get("shift") else ""
    if "video" in g:
        v = g["video"]
        m = MANIFEST[f"video:{v}"]
        media = (
            f'<video controls preload="none" playsinline width="{m["width"]}" height="{m["height"]}" '
            f'poster="/assets/video/{v}-poster.jpg" aria-label="{e(g["label"])}">'
            f'<source src="/assets/video/{v}.mp4" type="video/mp4">'
            f'<p>Your browser cannot play this video. <a href="/assets/video/{v}.mp4">Download the video (MP4, 1.1 MB)</a>.</p>'
            f'</video>'
        )
    else:
        span = g.get("span", 6)
        sizes = f"(min-width: 900px) {round(span / 12 * 100)}vw, (min-width: 600px) 50vw, 100vw"
        media = picture(g["image"], g["alt"], sizes)
    return f"""
      <figure class="g-item{shift}" style="{style}" data-reveal>
        {media}
        <figcaption>{e(g['caption'])}</figcaption>
      </figure>"""


def case_page(i: int, c: dict) -> str:
    n = len(CASES)
    num = f"{i + 1:02d}"
    nxt = CASES[(i + 1) % n]
    facts = "".join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in c["facts"])
    context = "".join(f"<p>{e(p)}</p>" for p in c["context"])
    role = "".join(f"<p>{e(p)}</p>" for p in c["role"])
    execution = "".join(f"<li>{e(x)}</li>" for x in c["execution"])
    credits = "".join(f'<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in c["credits"])
    gallery = "".join(gallery_item(c, g) for g in c["gallery"])
    programme = ""
    if c.get("programme"):
        rows = "".join(f"""
          <li><p class="prog-time"><span class="label">{e(p['time'])}</span><span class="prog-place">{e(p['place'])}</span></p><p>{e(p['text'])}</p></li>"""
                       for p in c["programme"])
        programme = f"""
    <div class="case-row" data-reveal>
      <h2 class="case-row-title label">Programme</h2>
      <ol class="programme">{rows}
      </ol>
    </div>"""
    quote = c.get("quote")
    quote_html = f"""
  <blockquote class="case-quote container" data-reveal>
    <p>“{e(quote['text'])}”</p>
    <footer>{e(quote['by'])}</footer>
  </blockquote>""" if quote else ""
    nxt_img = next((g["alt"] for g in nxt["gallery"] if g.get("image") == nxt["card_image"]), nxt["lead"]["alt"])

    body = f"""
<article class="case">
  <header class="case-hero container">
    <nav class="case-crumbs" aria-label="Breadcrumb">
      <a href="/#work"><span aria-hidden="true">←</span> All work</a>
      <span class="num" aria-label="Case {i + 1} of {n}">{num} / {n:02d}</span>
    </nav>
    <div class="case-hero-grid">
      <div class="case-hero-text">
        <p class="label">{e(c['category'])}</p>
        <h1 class="case-title">{e(c['title'])}</h1>
        <p class="case-subtitle">{e(c['subtitle'])}</p>
        <p class="case-intro">{e(c['intro'])}</p>
        <p class="case-provenance">{e(c['provenance']).replace('Sarah Al-farhan', '<span class="nowrap">Sarah Al-farhan</span>')}</p>
      </div>
      <figure class="case-lead">
        {picture(c['lead']['image'], c['lead']['alt'], "(min-width: 900px) 45vw, 100vw", eager=True, priority=True)}
      </figure>
    </div>
    <dl class="facts">{facts}</dl>
  </header>
{quote_html}
  <div class="case-body container">
    <div class="case-row" data-reveal>
      <h2 class="case-row-title label">Context</h2>
      <div class="case-row-text">{context}</div>
    </div>{programme}
    <div class="case-row" data-reveal>
      <h2 class="case-row-title label">{e(c.get('role_heading', 'Sarah’s role'))}</h2>
      <div class="case-row-text">{role}</div>
    </div>
    <div class="case-row" data-reveal>
      <h2 class="case-row-title label">{e(c.get('execution_heading', 'Execution'))}</h2>
      <ul class="exec-list">{execution}</ul>
    </div>
  </div>

  <section class="case-gallery container" aria-label="Images from the project">
    {gallery}
  </section>

  <div class="case-body container">
    <div class="case-row" data-reveal>
      <h2 class="case-row-title label">Credits</h2>
      <dl class="credits">{credits}</dl>
    </div>
  </div>

  <nav class="next-case" aria-label="Next project">
    <a class="container next-inner" href="/work/{nxt['slug']}/">
      <span class="label">Next project <span class="num">{(i + 1) % n + 1:02d}</span></span>
      <span class="next-title">{e(nxt['title'])} <span class="next-arrow" aria-hidden="true">→</span></span>
      <span class="next-media">{picture(nxt['card_image'], nxt_img, "(min-width: 900px) 20vw, 40vw")}</span>
    </a>
  </nav>

  <section class="case-cta container" aria-labelledby="cta-title">
    <h2 id="cta-title" class="cta-title">Have a project in mind?</h2>
    <p>Branding, campaigns, events or a collaboration: let’s talk about what you want to create.</p>
    <div class="hero-actions">
      <a class="btn btn--solid" href="mailto:{SITE['email']}">Email Sarah</a>
      <a class="btn btn--line" href="/#contact">Contact details</a>
    </div>
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
        og_image=f"/assets/img/{c['lead']['image']}-{MANIFEST[c['lead']['image']]['fallback']}.jpg",
    )


def not_found() -> str:
    links = "".join(f'<li><a href="/work/{c["slug"]}/"><span class="num">{i + 1:02d}</span> {e(c["title"])}</a></li>'
                    for i, c in enumerate(CASES))
    body = f"""
<section class="notfound container" aria-labelledby="nf-title">
  <p class="label">Error 404</p>
  <h1 id="nf-title" class="notfound-title">This page <em>has moved on.</em></h1>
  <p class="case-intro">The page you were looking for does not exist or is no longer here. Try one of these instead.</p>
  <div class="hero-actions">
    <a class="btn btn--solid" href="/">Go to the front page</a>
    <a class="btn btn--line" href="/#contact">Contact</a>
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
