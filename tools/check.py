#!/usr/bin/env python3
"""Quality gate for SGA creatives. Run before every commit and push:

    python3 tools/check.py

Checks, and exits with an error if any fail:
  1. public/ matches the current build (python3 tools/build_site.py has been run)
  2. no long dashes (em/en dash) anywhere in the published site or content
  3. every internal link and asset reference in the HTML points to a file that exists
  4. every page has exactly one <h1>, and every <img> has an alt attribute
  5. no secrets or private material is tracked by Git (docs/intern/ stays out)
  6. no file exceeds the Cloudflare Pages limit of 25 MiB, and the file count is within 20,000
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_site  # noqa: E402

ROOT = build_site.ROOT
PUBLIC = build_site.PUBLIC
TEXT_SUFFIXES = {".html", ".css", ".js", ".json", ".xml", ".webmanifest", ".svg"}
DASHES = re.compile("[‒–—―]")
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|pk|rk)_live_[A-Za-z0-9]{10,}"),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bre_[A-Za-z0-9]{20,}"),
    re.compile(r"\bnpg_[A-Za-z0-9]{10,}"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
]

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


# 1. build is current -------------------------------------------------------
outputs = build_site.main(dry_run=True)
for path, text in outputs.items():
    if not path.exists():
        fail(f"build: {rel(path)} is missing. Run python3 tools/build_site.py")
    elif path.read_text() != text:
        fail(f"build: {rel(path)} is out of date. Run python3 tools/build_site.py")
sitemap = PUBLIC / "sitemap.xml"
if sitemap.exists() and sitemap not in outputs:
    fail("build: public/sitemap.xml exists but no domain is set. Run python3 tools/build_site.py")
generated_pages = {p for p in outputs if p.suffix == ".html"}
for page in PUBLIC.rglob("*.html"):
    if page not in generated_pages:
        fail(f"build: {rel(page)} is not produced by the build (a removed case?). Delete it")

# 2. no long dashes -----------------------------------------------------------
dash_files = [p for p in PUBLIC.rglob("*") if p.is_file() and (p.suffix in TEXT_SUFFIXES or p.name in {"_headers", "robots.txt"})]
dash_files += list((ROOT / "content").glob("*.json"))
for p in dash_files:
    for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
        if DASHES.search(line):
            fail(f"dash: {rel(p)}:{n} contains a long dash: {line.strip()[:80]}")

# 3 + 4. links, headings, alt text --------------------------------------------
REF = re.compile(r'''(?:href|src|poster)="(/[^"#?]*)''')
SRCSET = re.compile(r'srcset="([^"]+)"')
for page in sorted(PUBLIC.rglob("*.html")):
    html = page.read_text()
    refs = set(REF.findall(html))
    for srcset in SRCSET.findall(html):
        refs.update(part.strip().split(" ")[0] for part in srcset.split(","))
    for ref in refs:
        target = PUBLIC / ref.lstrip("/")
        if ref.endswith("/"):
            target = target / "index.html"
        if not target.exists():
            fail(f"link: {rel(page)} points to {ref}, which does not exist")
    if len(re.findall(r"<h1[\s>]", html)) != 1:
        fail(f"a11y: {rel(page)} must have exactly one <h1>")
    for img in re.findall(r"<img\b[^>]*>", html):
        if " alt=" not in img:
            fail(f"a11y: {rel(page)} has an <img> without alt: {img[:80]}")

# 4b. images that have arrived must have alt text; count remaining placeholders
placeholders = []
for c in build_site.CASES:
    for g in c["gallery"]:
        name = g.get("image")
        if not name:
            continue
        if name in build_site.MANIFEST and not g.get("alt"):
            fail(f"a11y: {name} now exists but has no alt text in content/cases.json ({c['slug']})")
        if name not in build_site.MANIFEST:
            placeholders.append(name)
if "sarah-al-farhan-01" not in build_site.MANIFEST:
    placeholders.append("sarah-al-farhan-01")

# 5. secrets and private files --------------------------------------------------
try:
    tracked = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split("\n")
except (OSError, subprocess.CalledProcessError) as exc:
    fail(f"git: could not list the files Git would commit ({exc}); secret scan not run")
    tracked = []
for name in filter(None, tracked):
    if name.startswith("docs/intern/") or Path(name).name in {".env", "CV.txt", "BRIEF.md"}:
        fail(f"private: {name} would be committed. It must stay out of the public repo")
    p = ROOT / name
    if p.suffix.lower() in {".jpg", ".png", ".avif", ".webp", ".mp4", ".woff2", ".ico", ".ttf"}:
        continue
    try:
        text = p.read_text(errors="ignore")
    except OSError:
        continue
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            fail(f"secret: {name} matches {pat.pattern[:40]}")

# 6. Cloudflare Pages limits ------------------------------------------------------
files = [p for p in PUBLIC.rglob("*") if p.is_file()]
if len(files) > 20000:
    fail(f"limit: public/ has {len(files)} files; Cloudflare Pages allows 20,000")
for p in files:
    if p.stat().st_size > 25 * 1024 * 1024:
        fail(f"limit: {rel(p)} is larger than 25 MiB")

# report -------------------------------------------------------------------------
if failures:
    print(f"check.py: {len(failures)} problem(s)\n")
    for f in failures:
        print("  x", f)
    sys.exit(1)
size_mb = sum(p.stat().st_size for p in files) / 1e6
print(f"check.py: all checks passed ({len(outputs)} generated files current, {len(files)} files / {size_mb:.1f} MB in public/)")
if placeholders:
    print(f"          {len(placeholders)} image placeholders waiting for photos: {', '.join(placeholders)}")
