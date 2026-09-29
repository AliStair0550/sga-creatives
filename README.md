# SGA creatives: hjemmeside

Statisk hjemmeside til SGA creatives (HTML, CSS og vanilla JavaScript). Alt offentligt indhold er på engelsk, mens denne vejledning er på dansk. Siden kræver ingen database, PHP eller applikationsserver og er forberedt til **Cloudflare Pages** med **DNS hos Simply** og **www som primær adresse**.

## Mappestruktur

```
SGAcreatives/                ← repo-roden (github.com/AliStair0550/sga-creatives)
├── CLAUDE.md                arbejdsregler, arkitektur og workflow
├── public/                  ← DET, DER PUBLICERES (build output directory)
│   ├── index.html           forside: Work · Services · About · Contact
│   ├── work/<slug>/         fem casesider med egne URL'er
│   ├── 404.html             fejlside (skal ligge i roden, ellers antager Pages en SPA)
│   ├── _headers             sikkerheds- og cache-headers til Cloudflare Pages
│   ├── robots.txt, site.webmanifest, favicon.svg/.ico, apple-touch-icon.png
│   └── assets/              css, js, fonte, optimerede billeder, video, logoer, delingsbillede
├── content/
│   ├── site.json            domæne, e-mail, telefon, sociale links
│   ├── cases.json           al tekst og alle billeder til de fem cases
│   └── media-manifest.json  billedstørrelser (genereres automatisk)
├── tools/
│   ├── build_site.py        bygger alle HTML-sider i public/ ud fra content/
│   ├── optimize_media.py    laver AVIF/WebP/JPEG i flere størrelser samt video og poster
│   ├── make_brand.py        genererer logoer, favicons og delingsbillede
│   ├── retouch_lookbook_hero.py  hero-udgave af lookbook-coveret uden coverteksten
│   ├── share/               delingsbilleder (Open Graph) til hver side: `cd tools/share && npm install && npm run build`
│   └── fonts-src/           originale fontfiler og OFL-licenser
│   └── check.py             kvalitetstjek før hver commit
├── brand/                   logofiler (SVG/PNG) og brandguide.html
├── assets/                  ORIGINALMEDIER: ændres aldrig og publiceres ikke
└── docs/intern/             brief, CV, kildemateriale og afklaringer (lokalt, IKKE i Git)
```

Siderne i `public/` er færdigbyggede. Cloudflare skal derfor ikke køre en build-kommando.

## Daglig arbejdsgang

Vi arbejder direkte i denne mappe og pusher til `main`. Når Cloudflare Pages er koblet på repoet, publiceres hvert push automatisk (typisk inden for et par minutter).

```bash
cd ~/Desktop/BUSINESS/SGAcreatives
# 1. ret i content/, tools/ eller public/assets/css|js
python3 tools/build_site.py     # byg siderne
python3 tools/check.py          # tjek: bygget er aktuelt, ingen tankestreger, ingen hemmeligheder, links virker
git add . && git commit -m "Kort beskrivelse på dansk" && git push
```

`check.py` skal være grønt før hvert push. Filerne i `docs/intern/` kommer aldrig med i Git.

## Se siden lokalt

Hurtigst (kræver kun Python):

```bash
cd ~/Desktop/BUSINESS/SGAcreatives
python3 -m http.server 8000 --directory public
# åbn http://localhost:8000
```

Åbn ikke filerne direkte med dobbeltklik (`file://`), da stierne starter med `/`.

Som på Cloudflare, med `_headers`, 404-side og trailing slash (kræver Node.js):

```bash
npx wrangler pages dev public --port 8788
# åbn http://localhost:8788
```

## Opdatér indhold

Rediger aldrig HTML-filerne i `public/` direkte. De overskrives ved næste build.

| Hvad | Hvor |
|---|---|
| Kontaktoplysninger, domæne | `content/site.json` |
| Casetekster, roller, credits, billedtekster, alt-tekster | `content/cases.json` |
| Hero, services, proces, about og erfaring | `tools/build_site.py` (listerne `SERVICES`, `PROCESS`, `EXPERIENCE` og funktionen `home()`) |
| Farver, typografi, afstande | `public/assets/css/main.css` (CSS-variabler øverst i `:root`) |

Byg derefter siden:

```bash
python3 tools/build_site.py
```

Scriptet bruger kun Pythons standardbibliotek. Det tilføjer automatisk en versionsnøgle til CSS og JS (`main.css?v=…`), så besøgende altid får den nyeste version, selvom filerne caches i et år.

## Billeder og pladsholdere

Galleriet i hver case (`gallery` i `content/cases.json`) kan indeholde billeder, der ikke findes endnu. De vises som elegante pladsholdere med SGA-mærket. Sådan udskifter du en pladsholder:

1. Gem billedet som `assets/images/<navn>.jpg`, fx `rezet-lookbook-03.jpg`. Navnet står i `cases.json`.
2. Skriv en engelsk alt-tekst i feltet `"alt"` for billedet i `cases.json`.
3. Kør:
   ```bash
   python3 tools/optimize_media.py
   python3 tools/build_site.py
   python3 tools/check.py
   ```
4. Commit og push.

`layout` styrer formatet: `wide` er fuld bredde (16:9), `half` er halv bredde og `third` er en tredjedel (begge 4:5). Portrættet i About hedder `sarah-al-farhan-01`. `check.py` viser, hvilke pladsholdere der stadig venter.

## Deling og SEO

- Hver side har sit eget delingsbillede i 1200 × 630 (`public/assets/og/`): forsiden, Portfolio og én pr. case i casens farve. Lav dem igen efter ændringer i cases eller billeder:
  ```bash
  cd tools/share && npm install && npm run build && cd ../.. && python3 tools/build_site.py
  ```
- Titler, beskrivelser, canonical, Open Graph og Twitter/X-kort genereres af `tools/build_site.py`. Beskrivelserne til cases står i `meta_description` i `content/cases.json` (hold dem under 160 tegn).
- Strukturerede data (JSON-LD) er usynlige for besøgende: organisation, person (Sarah), website, portfolio-liste, casene som `CreativeWork` og brødkrummer.
- Test en delt side med LinkedIns Post Inspector (https://www.linkedin.com/post-inspector/) og Facebooks Sharing Debugger. De tømmer også deres cache, hvis et gammelt billede hænger ved.

## Tilføj en ny case

1. Læg originalbillederne i `assets/images/` med navne som `<slug>-01.jpg`, `<slug>-02.jpg` (JPEG, gerne 1000 til 1400 px brede).
2. Optimér medierne (kræver Pillow og ffmpeg: `pip3 install pillow` og `brew install ffmpeg`):
   ```bash
   python3 tools/optimize_media.py
   ```
3. Kopiér en eksisterende case i `content/cases.json`, og udfyld felterne:
   - `slug` bliver URL'en (`/work/<slug>/`).
   - `card_image` og `card_image_2` er de to billeder på forsiden, og `tone` er casens farveunivers (`bg` og `mode`: `dark` eller `light`).
   - `provenance` fortæller, i hvilken rolle Sarah lavede projektet.
   - `intro`, `facts`, `done` (Sarahs arbejde som korte punkter) og `credits` er casesidens tekst. Hold den kort.
   - `gallery`: se "Billeder og pladsholdere" ovenfor.
   - Rækkefølgen i filen er rækkefølgen på siden. "Next project" linker automatisk videre.
4. Kør `python3 tools/build_site.py`, og tjek siden lokalt.
5. Tilføj den nye URL i sitemap. Det sker automatisk, når domænet er sat.

Beskriv kun roller og credits, der kan dokumenteres. Sarahs tidligere arbejde præsenteres som hendes arbejde med arbejdsgiver/rolle, ikke som SGA-opgaver.

## Deployment: Cloudflare Pages via Git

Anbefalet opsætning: Git-integration, så hver ændring på `main` publiceres automatisk.

1. Koden ligger allerede på GitHub: **https://github.com/AliStair0550/sga-creatives** (offentligt repo, branch `main`). Se "Daglig arbejdsgang" nedenfor.
2. I Cloudflare: **Workers & Pages → Create → Pages → Connect to Git**. Vælg repository.
3. Build-indstillinger:

   | Felt | Værdi |
   |---|---|
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | *(tomt)*, alternativt `exit 0` |
   | Build output directory | `public` |
   | Root directory | *(tomt)* |

4. Deploy. Siden kommer på `https://<projektnavn>.pages.dev`. Test alle sider og en forkert URL (skal vise 404) her, før domænet kobles på.

Alternativ uden Git (Direct Upload): `npx wrangler pages deploy public --project-name=sga-creatives`. Bemærk, at et Direct Upload-projekt ikke senere kan skiftes til Git-integration.

**Status pr. september 2026:** Cloudflare Pages er fortsat i drift, men Cloudflares dokumentation anbefaler nu Workers (Static Assets) til nye projekter. Pages opfylder alle behov her. Bekræft den aktuelle anbefaling ved lancering (se kilder nederst).

**Grænser:** Free-planen tillader 20.000 filer pr. site og 25 MiB pr. fil, `_headers` højst 100 regler. Sitet består af 163 filer på i alt ca. 12 MB, og den største fil er videoen på 1,1 MB.

## Domæne: www på Pages, DNS hos Simply

**Status 29. september 2026:**
- Domænet er **www.sgacreatives.com**. `www` har CNAME til `sga-creatives.pages.dev` hos Simply.
- `content/site.json` har domænet sat, så canonical-links og sitemap peger på det.
- Roddomænet `sgacreatives.com` mangler stadig viderestilling (trin 4).
- Domænet har ingen MX-records, så der er ingen mail at passe på.

Rækkefølgen er vigtig. Hvis CNAME oprettes, før domænet er tilføjet i Pages, giver det fejl 522.

**Før du starter:** Tag et skærmbillede eller en kopi af **alle** eksisterende DNS-records hos Simply, især MX, TXT (SPF, DKIM, DMARC), autodiscover og eventuelle CAA-records. De må ikke ændres, så e-mail fortsætter med at virke.

1. **Cloudflare:** Åbn projektet under Workers & Pages, gå til **Custom domains → Set up a domain**, og skriv `www.<domæne>.dk`. Cloudflare viser den CNAME, der skal oprettes.
2. **Simply:** Gå til kontrolpanelet, vælg domænet og derefter **DNS**.
   - Slet en eventuel eksisterende `www`-record (A, AAAA eller CNAME). En CNAME må ikke dele navn med andre records.
   - Opret: Type `CNAME`, Navn `www`, Værdi `<projektnavn>.pages.dev`.
   - Findes der CAA-records, skal de tillade Cloudflares certifikatudstedere.
3. **Vent** til domænet står som *Active* i Pages. SSL-certifikatet udstedes automatisk.
4. **Viderestilling af roddomænet (Simply):** Under domænets DNS-side finder du sektionen **URL viderestilling → Opsæt viderestilling**. Viderestil `<domæne>.dk` til `https://www.<domæne>.dk`. Simply har siden 26. marts 2026 udstedt SSL-certifikater til viderestillinger, så både `http://` og `https://` på roddomænet virker. Målet må ikke selv viderestille.
5. **Sæt domænet i sitet**, så canonical-links, `og:url`, absolutte delingsbilleder og `sitemap.xml` genereres:
   ```json
   "domain": "https://www.<domæne>.dk"
   ```
   i `content/site.json`. Kør derefter `python3 tools/build_site.py`, og commit og push.

### Test efter lancering

```bash
curl -I https://www.<domæne>.dk/                         # 200
curl -I https://www.<domæne>.dk/work/adidas-kiosk         # 308 → /work/adidas-kiosk/
curl -I https://www.<domæne>.dk/findes-ikke               # 404
curl -I http://www.<domæne>.dk/                          # → https
curl -I https://<domæne>.dk/                             # → https://www.<domæne>.dk/
curl -I "https://<domæne>.dk/work/timberland-rezet/?utm_source=test"   # bevares sti og query?
curl -sIL https://<domæne>.dk/ | grep -i location        # ingen redirect-loop
```

**Ikke bekræftet i Simplys dokumentation** (test ved lancering, eller spørg Simplys support):
- om viderestillingen bevarer sti og query-parametre (fx `/work/…?utm=…`),
- hvilken statuskode den bruger (301 eller 302),
- om den ændrer andre records.

Hvis stien ikke bevares, lander besøgende på forsiden. Det er acceptabelt, men bør noteres.

Kontrollér også MX og TXT bagefter, og send en testmail til og fra domænet.

### Hvis roddomænet skal hostes direkte på Pages

Det kræver, at domænets **nameservere flyttes til Cloudflare**. En CNAME hos Simply er ikke nok. Så skal alle records (inklusive mail) genskabes i Cloudflare DNS, før nameserverne skiftes. Det er et andet setup og aftales særskilt.

## Gendannelse

- **Fejl i en ny version:** Cloudflare, derefter projektet, **Deployments**, vælg en tidligere deployment og **Rollback to this deployment**. Det sker med det samme.
- **Via Git:** `git revert <commit>` og push. Så bygges og publiceres den forrige tilstand.
- **Lokalt:** Hele sitet kan genskabes ud fra `content/`, `tools/` og `assets/`:
  ```bash
  python3 tools/optimize_media.py   # billeder og video
  python3 tools/make_brand.py       # logoer, favicons, delingsbillede
  python3 tools/build_site.py       # HTML, sitemap, headers
  ```
  Kræver Python 3.10+ med Pillow (AVIF/WebP) og fontTools samt ffmpeg.
- **DNS:** Slet `www`-CNAME og viderestillingen hos Simply, og genskab de records, der var noteret før ændringen.

## Tekniske valg

- **Fonte:** Figtree (fed, geometrisk, til logo og overskrifter) og Archivo (brødtekst og labels). Begge er under SIL OFL 1.1 og hostes lokalt, uden kald til Google.
- **Billeder:** AVIF og WebP i 480/800/fuld bredde med `srcset`, JPEG-fallback, faste dimensioner (ingen layout-skift) og lazy loading under heroen.
- **Video:** Kun Nike-casen, med poster, kontroller og `preload="none"`. Ingen autoplay og ingen lyd uden klik.
- **Bevægelse:** Kort hero-indgang, reveals ved scroll, let billedskalering og glidende menu. Alt slås fra ved `prefers-reduced-motion`. Uden JavaScript er alt indhold synligt, og navigationen vises som almindelige links.
- **Sikkerhed:** `_headers` sætter Content-Security-Policy, X-Frame-Options, nosniff, Referrer-Policy og Permissions-Policy. CSP'en indeholder en hash af det lille inline-script i `<head>`, og `build_site.py` opdaterer den automatisk.
- **Ingen cookies og ingen tracking.** Tilføjes der analytics senere, skal behovet for cookiebanner og privatlivstekst vurderes.

## Udførte tests (seneste: mobilgennemgang 29. september 2026)

Testet mod `wrangler pages dev` med Chromium (Playwright) og Lighthouse 12 (mobilprofil, simuleret throttling):

- Alle 8 sider (forside, Portfolio, 5 cases, 404) ved 360, 390, 768, 1024 og 1440 px: ingen vandret scroll, ingen konsolfejl, ingen fejlede requests, alle billeder har alt-tekst, én `h1` pr. side.
- Mobilmenu med tastatur (fokusfælde, Escape), visning uden JavaScript og `prefers-reduced-motion`.
- Lighthouse mobil efter optimeringen:

  | Side | Performance | Accessibility | Best practices | SEO | LCP |
  |---|---|---|---|---|---|
  | Forside | 99 | 100 | 100 | 100 | 2,0 s |
  | Portfolio | 100 | 100 | 100 | 100 | 1,4 s |
  | Cases | 99-100 | 100 | 100 | 100 | 1,6-2,1 s |

Mobiloptimeringer i gennemgangen:
- Archivo-fonten er skåret til de vægte og bredder, der bruges (92 KB til 35 KB).
- Billeder findes i 320, 480, 640, 800 og 1200 px med præcise `sizes`.
- CSS minificeres ved build.
- Videoens poster er WebP.
- Entré-animationer skjuler ikke længere det første indhold (LCP).
- Scroll-effekter kører i ét samlet loop, der kun måler elementer nær skærmen.
- Hover-effekter er begrænset til enheder med mus, og alle labels er mindst 12 px.

**Ikke testet:** rigtige iOS- og Android-enheder, Safari og Firefox samt skærmlæser.

## Resterende afklaringer

Listen over åbne spørgsmål (roller, rettigheder, domæne, virksomhedsoplysninger) ligger i `docs/intern/AFKLARINGER.md`. Den er holdt uden for Git, fordi repoet er offentligt.

## Kilder til hosting og DNS (tjekket 29. september 2026)

- Cloudflare Pages, grænser: https://developers.cloudflare.com/pages/platform/limits/
- Build-konfiguration: https://developers.cloudflare.com/pages/configuration/build-configuration/
- Serving pages og 404: https://developers.cloudflare.com/pages/configuration/serving-pages/
- Headers: https://developers.cloudflare.com/pages/configuration/headers/
- Custom domains: https://developers.cloudflare.com/pages/configuration/custom-domains/
- Direct Upload: https://developers.cloudflare.com/pages/get-started/direct-upload/
- Simply, DNS-records: https://www.simply.com/en/support/faq/domain/339-about-dns-records/
- Simply, URL-viderestilling: https://www.simply.com/dk/support/faq/3/25/
- Simply, HTTPS på viderestilling (marts 2026): https://blog.simply.com/2026/url-viderestilling-med-https-understoettelse/

Publicering og aktive DNS-ændringer er ikke udført. De aftales særskilt.
