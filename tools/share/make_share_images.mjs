// Share images (Open Graph / X / LinkedIn / iMessage previews) for every page, 1200 x 630 JPEG.
//
//   cd tools/share && npm install        (once: installs playwright-core)
//   node make_share_images.mjs           (uses the installed Google Chrome, or CHROME_PATH)
//
// Writes public/assets/og/home.jpg, portfolio.jpg and <case-slug>.jpg from content/cases.json,
// in the white site style (Inter, the sga.creatives wordmark) with the original photos.
// Run tools/build_site.py afterwards.
import { chromium } from 'playwright-core';
import { readFileSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(here, '..', '..');
const OUT = join(ROOT, 'public', 'assets', 'og');
const TMP = join(here, '.tmp');
const cases = JSON.parse(readFileSync(join(ROOT, 'content', 'cases.json'), 'utf8'));
const file = (p) => 'file://' + join(ROOT, p);
const img = (name) => file(`assets/images/${name}.jpg`);
const logo = readFileSync(join(ROOT, 'public/assets/brand/sga-creatives-wordmark-dark.svg'), 'utf8')
  .replace(/<title[^>]*>.*?<\/title>/, '');
const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
// prefer a text-free hero version of a photo when one exists (e.g. the lookbook cover)
import { existsSync } from 'node:fs';
const clean = (name) => existsSync(join(ROOT, `assets/images/${name}-hero.jpg`)) ? `${name}-hero` : name;
// short linking words stay glued to both neighbours, so "Ways to Style" never splits
const title = (t) => esc(t).replace(/ (to|&amp;) /g, '&nbsp;$1&nbsp;');

// The white site: Inter in medium weight, ink on white, quiet grey for secondary text.
const base = `
<style>
  @font-face { font-family: Inter; src: url(${file('public/assets/fonts/Inter-VF.woff2')}); font-weight: 400 600; }
  * { box-sizing: border-box; margin: 0; }
  html, body { width: 1200px; height: 630px; overflow: hidden; }
  body { background: #FFFFFF; color: #111111; font-family: Inter, sans-serif; font-weight: 500; font-feature-settings: "cv11", "ss01"; position: relative; }
  .logo { position: absolute; left: 56px; top: 48px; z-index: 3; }
  .logo svg { height: 34px; width: auto; display: block; }
  .muted { color: #737373; }
  .big { letter-spacing: -0.035em; line-height: 1; }
  .url { position: absolute; left: 56px; bottom: 48px; z-index: 3; font-size: 20px; color: #737373; }
  .ph { background-size: cover; background-position: center; }
</style>`;

const pages = [];

// home: the site's first screen: the headline, and two photos in layers beside it
pages.push(['home', `${base}
<style>
  h1 { position: absolute; left: 56px; top: 200px; font-size: 80px; }
  .back { position: absolute; right: 72px; top: 56px; width: 236px; height: 295px; }
  .front { position: absolute; right: 236px; top: 150px; width: 316px; height: 395px; z-index: 2; }
</style>
<div class="logo">${logo}</div>
<h1 class="big">Where brands<br>meet culture.</h1>
<div class="ph back" style="background-image:url(${img('adidas-ways-to-style-01')});background-position:50% 30%"></div>
<div class="ph front" style="background-image:url(${img('timberland-rezet-04')})"></div>
<p class="url">sgacreatives.com</p>`]);

// projects: the title and the five projects in a row, each with its caption
pages.push(['portfolio', `${base}
<style>
  h1 { position: absolute; left: 56px; top: 118px; font-size: 64px; }
  .row { position: absolute; left: 56px; right: 56px; bottom: 56px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; }
  .row figure { margin: 0; }
  .row .ph { height: 270px; }
  .row figcaption { margin-top: 12px; font-size: 16px; line-height: 1.25; text-align: center; }
  .url { top: 56px; bottom: auto; left: auto; right: 56px; }
</style>
<div class="logo">${logo}</div>
<p class="url">sgacreatives.com</p>
<h1 class="big">Projects</h1>
<div class="row">${cases.map(c => `<figure><div class="ph" style="background-image:url(${img(clean(c.card_image))})"></div><figcaption><span class="muted">${esc(c.partners.split(',')[0])}</span><br>${esc(c.title)}</figcaption></figure>`).join('')}</div>`]);

// one per case: like the case page: company, title and subtitle, the cover photo on white
for (const c of cases) {
  const long = c.title.length > 16;
  pages.push([c.slug, `${base}
<style>
  .photo { position: absolute; right: 96px; top: 56px; width: 415px; height: 518px; }
  .text { position: absolute; left: 56px; bottom: 112px; width: 560px; }
  .company { font-size: 24px; margin-bottom: 18px; }
  h1 { font-size: ${long ? 68 : 80}px; }
  .sub { margin-top: 16px; font-size: 32px; letter-spacing: -0.02em; }
</style>
<div class="ph photo" style="background-image:url(${img(clean(c.lead.image))})"></div>
<div class="logo">${logo}</div>
<div class="text">
  <p class="company muted">${esc(c.partners)}</p>
  <h1 class="big">${title(c.title)}</h1>
  <p class="sub muted">${esc(c.subtitle)}</p>
</div>
<p class="url">sgacreatives.com</p>`]);
}

mkdirSync(OUT, { recursive: true });
mkdirSync(TMP, { recursive: true });
const browser = await chromium.launch(process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' });
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
for (const [name, html] of pages) {
  const tmp = join(TMP, `${name}.html`);
  writeFileSync(tmp, `<!doctype html><html><head><meta charset="utf-8"></head><body>${html}</body></html>`);
  await page.goto('file://' + tmp);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(150);
  await page.screenshot({ path: join(OUT, `${name}.jpg`), type: 'jpeg', quality: 86 });
  console.log('wrote public/assets/og/' + name + '.jpg');
}
await browser.close();
rmSync(TMP, { recursive: true, force: true });
