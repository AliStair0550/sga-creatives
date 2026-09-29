// Share images (Open Graph / X / LinkedIn / iMessage previews) for every page, 1200 x 630 JPEG.
//
//   cd tools/share && npm install        (once: installs playwright-core)
//   node make_share_images.mjs           (uses the installed Google Chrome, or CHROME_PATH)
//
// Writes public/assets/og/home.jpg, portfolio.jpg and <case-slug>.jpg from content/cases.json,
// using the site's own fonts, colours and original photos. Run tools/build_site.py afterwards.
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
const logo = readFileSync(join(ROOT, 'public/assets/brand/sga-creatives-logo-horizontal-light.svg'), 'utf8')
  .replace(/<title[^>]*>.*?<\/title>/, '');
const esc = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;');
// prefer a text-free hero version of a photo when one exists (e.g. the lookbook cover)
import { existsSync } from 'node:fs';
const clean = (name) => existsSync(join(ROOT, `assets/images/${name}-hero.jpg`)) ? `${name}-hero` : name;
// short linking words stay glued to both neighbours, so "Ways to Style" never splits
const title = (t) => esc(t).replace(/ (to|&amp;) /g, '&nbsp;$1&nbsp;');

const base = `
<style>
  @font-face { font-family: Figtree; src: url(${file('public/assets/fonts/Figtree-VF.woff2')}); font-weight: 400 800; }
  @font-face { font-family: Archivo; src: url(${file('public/assets/fonts/Archivo-VF.woff2')}); font-weight: 400 600; font-stretch: 100% 125%; }
  * { box-sizing: border-box; margin: 0; }
  html, body { width: 1200px; height: 630px; overflow: hidden; }
  body { background: #0E0F0F; color: #F3F0E9; font-family: Archivo, sans-serif; position: relative; }
  .logo { position: absolute; left: 56px; top: 50px; height: 34px; z-index: 3; }
  .logo svg { height: 34px; width: auto; display: block; }
  .label { font-family: Archivo; font-stretch: 125%; font-weight: 560; font-size: 17px; letter-spacing: .22em; text-transform: uppercase; color: rgba(243,240,233,.72); }
  .display { font-family: Figtree; font-weight: 800; letter-spacing: -0.045em; line-height: .95; }
  .display span { font-weight: 400; }
  .url { position: absolute; left: 56px; bottom: 48px; z-index: 3; font-family: Archivo; font-stretch: 118%; font-weight: 560; font-size: 16px; letter-spacing: .2em; text-transform: uppercase; color: rgba(243,240,233,.72); }
</style>`;

const pages = [];

// home: the hero triptych with the headline, like the site's first screen
pages.push(['home', `${base}
<style>
  .strip { position: absolute; inset: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 3px; }
  .strip div { background-size: cover; background-position: center; }
  .shade { position: absolute; inset: 0; background: linear-gradient(to top, rgba(10,10,10,.92) 0%, rgba(10,10,10,.5) 45%, rgba(10,10,10,.1) 75%), linear-gradient(to bottom, rgba(10,10,10,.55), rgba(10,10,10,0) 30%); }
  h1 { position: absolute; left: 56px; bottom: 96px; font-size: 104px; z-index: 3; }
</style>
<div class="strip">
  <div style="background-image:url(${img('rezet-lookbook-01-hero')});background-position:36% 40%"></div>
  <div style="background-image:url(${img('adidas-ways-to-style-01')});background-position:50% 35%"></div>
  <div style="background-image:url(${img('timberland-rezet-04')});background-position:74% 45%"></div>
</div>
<div class="shade"></div>
<div class="logo">${logo}</div>
<h1 class="display">Where brands<br><span>meet culture.</span></h1>
<p class="url">sgacreatives.com</p>`]);

// portfolio: the five projects as a tonal row
pages.push(['portfolio', `${base}
<style>
  h1 { position: absolute; left: 56px; top: 150px; font-size: 128px; }
  .row { position: absolute; left: 56px; right: 56px; bottom: 56px; display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
  .row div { height: 250px; background-size: cover; background-position: center; outline: 8px solid var(--t); outline-offset: -8px; }
  .url { top: 62px; bottom: auto; left: auto; right: 56px; }
</style>
<div class="logo">${logo}</div>
<p class="url">sgacreatives.com</p>
<h1 class="display">Portfolio</h1>
<div class="row">${cases.map(c => `<div style="--t:${c.tone.bg};background-image:url(${img(clean(c.card_image))})"></div>`).join('')}</div>`]);

// one per case: the case's own tone, title and cover photo
for (const c of cases) {
  const long = c.title.length > 16;
  pages.push([c.slug, `${base}
<style>
  body { background: ${c.tone.bg}; }
  .photo { position: absolute; right: 0; top: 0; width: 504px; height: 630px; background: url(${img(clean(c.lead.image))}) center / cover; }
  .photo::after { content: ""; position: absolute; inset: 0 auto 0 0; width: 120px; background: linear-gradient(to right, ${c.tone.bg}, transparent); }
  .text { position: absolute; left: 56px; bottom: 104px; width: 600px; }
  .text .label { margin-bottom: 22px; }
  h1 { font-size: ${long ? 84 : 104}px; }
  .sub { margin-top: 18px; font-family: Figtree; font-weight: 400; font-size: 34px; letter-spacing: -0.02em; color: rgba(243,240,233,.78); }
</style>
<div class="photo"></div>
<div class="logo">${logo}</div>
<div class="text">
  <p class="label">${esc(c.category)}</p>
  <h1 class="display">${title(c.title)}</h1>
  <p class="sub">${esc(c.subtitle)}</p>
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
