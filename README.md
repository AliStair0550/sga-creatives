# SGA creatives: hjemmeside

Statisk hjemmeside til SGA creatives (HTML, CSS og vanilla JavaScript). Alt offentligt indhold er på engelsk, mens denne vejledning er på dansk. Siden kræver ingen database, PHP eller applikationsserver og er forberedt til **Cloudflare Pages** med **DNS hos Simply** og **www som primær adresse**.

## Mappestruktur

```
SGAcreatives/                ← repo-roden (github.com/AliStair0550/sga-creatives)
├── CLAUDE.md                arbejdsregler, arkitektur og workflow
├── public/                  ← DET, DER PUBLICERES (build output directory)
│   ├── index.html           forside: hero, projekterne ét ad gangen, løftet
│   ├── services/ about/ contact/   Services, About me og Contact
│   ├── work/                Projects (oversigt) og fem casesider i work/<slug>/
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
│   ├── make_brand.py        genererer wordmark (sga.creatives), favicons og app-ikoner
│   ├── make_webfont.py      skærer Inter til en lille webfil (public/assets/fonts/Inter-VF.woff2)
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

## Billeder, der mangler

Galleriet i hver case (`gallery` i `content/cases.json`) kan indeholde billeder, der ikke findes endnu. De vises ikke på sitet, og galleriets rækker udjævnes, så intet står halvtomt. Sådan tilføjer du et af dem:

1. Gem billedet som `assets/images/<navn>.jpg`, fx `rezet-lookbook-03.jpg`. Navnet står i `cases.json`.
2. Skriv en engelsk alt-tekst i feltet `"alt"` for billedet i `cases.json`.
3. Kør:
   ```bash
   python3 tools/optimize_media.py
   python3 tools/build_site.py
   python3 tools/check.py
   ```
4. Commit og push.

`layout` styrer formatet: `wide` er fuld bredde (16:9), `half` er halv bredde og `third` er en tredjedel (begge 4:5). Portrættet på About me hedder `sarah-al-farhan-01`. `check.py` viser, hvilke billeder der stadig mangler.

## Deling og SEO

- Hver side har sit eget delingsbillede i 1200 × 630 (`public/assets/og/`) i sitets hvide stil: forsiden, Projects og én pr. case. Services, About me og Contact bruger forsidens. Lav dem igen efter ændringer i cases eller billeder:
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
   - `card_image` er casens billede på forsiden og på Projects. Ligger det ikke i galleriet, skrives alt-teksten i `card_alt`. (`card_image_2` og `tone` stammer fra det tidligere mørke design og bruges ikke.)
   - `provenance` fortæller, i hvilken rolle Sarah lavede projektet.
   - `intro`, `facts`, `done` (Sarahs arbejde som korte punkter) og `credits` er casesidens tekst. Hold den kort.
   - `gallery`: se "Billeder, der mangler" ovenfor.
   - Rækkefølgen i filen er rækkefølgen på Projects og i "Next project". Forsiden viser Nike først (`HOME_ORDER` i `build_site.py`).
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

## Beslutning: domæne og DNS bliver hos Simply (29.9.2026)

Det anbefalede setup er det nuværende:
- **Domæne og DNS hos Simply.** Simply viderestiller også roddomænet til www.
- **Hjemmesiden på Cloudflare Pages.**
- Sarah bruger sin Gmail. Besparelsen ved at flytte til Cloudflare er kun ca. 65-85 kr./år (se nedenfor).

### Hvis Sarah senere vil have egen mail (fx hello@sgacreatives.com)

1. Køb **Simply Basic Mail** til sgacreatives.com i Simplys kontrolpanel (tjekket 29.9.2026: 2,95 kr./md. første år, derefter 45,95 kr./md. inkl. moms; 5 postkasser, ubegrænsede aliasser).
2. Opret postkassen, fx `hello@`. Simply opretter selv MX, SPF, DKIM og DMARC. Lad `www`-CNAME og URL-viderestillingen stå uændret, for de påvirkes ikke af mail.
3. Sæt mailen op i Gmail-appen, Apple Mail eller Outlook med Simplys IMAP/SMTP (`smtp.simply.com`, port 587). Brug ikke Gmails "Send mail as", som Google fjerner i januar 2027.
4. Skift adressen på sitet: `"email"` i `content/site.json`, kør `python3 tools/build_site.py` og `python3 tools/check.py`, og push. Adressen opdateres så i kontaktknappen, "Get in touch", footeren og de strukturerede data.
5. Send en testmail til og fra en ekstern adresse, og tjek, at den ikke lander i spam.

### Alternativ, ikke planlagt: flyt domænet helt til Cloudflare

> Ikke valgt. Guiden gemmes til reference, hvis det skulle blive aktuelt. Den forudsætter, at der ikke er mail på domænet. Er Simply Mail købt, skal MX-, SPF-, DKIM- og DMARC-records fra Simply oprettes i Cloudflare i stedet for "null MX"- og `-all`-records nedenfor.

**Status 29.9.2026:**
- sgacreatives.com (.com, altså ikke Punktum dk) er registreret 18.8.2026 via Simply, med Key-Systems som registrator.
- Domænet er betalt til 18.8.2027.
- Nyregistrerede .com-domæner har 60 dages transferlås, så **registreringen kan tidligst flyttes omkring 17.10.2026**.
- DNS-records i dag:

| Type | Navn | Værdi | Formål |
|---|---|---|---|
| A | `@` | 94.231.103.100 (dnsforward.simply.com) | Simplys viderestilling til www. Skal **ikke** genskabes. |
| CNAME | `www` | sga-creatives.pages.dev | Hjemmesiden |

Der er ingen MX-, TXT- eller CAA-records.

**Pris (tjekket 29.9.2026):**
- Simply fornyer .com til 154,69 kr./år inkl. moms ([simply.com/dk/com-domain](https://www.simply.com/dk/com-domain/)).
- Cloudflare Registrar tager kostpris, ca. 10,5 USD/år ekskl. moms, dvs. ca. 70-90 kr. afhængigt af kurs og moms.
- Besparelsen er altså ca. 65-85 kr./år.

### Trin A: DNS til Cloudflare (kan gøres når som helst)

1. **Cloudflare → Add a domain →** `sgacreatives.com`, Free-plan. Slet eventuelle records, Cloudflare selv har fundet.
2. **Opret records** i Cloudflare DNS, *før* nameserverne skiftes:

   | Type | Navn | Værdi | Proxy | Formål |
   |---|---|---|---|---|
   | CNAME | `www` | `sga-creatives.pages.dev` | Proxied | Hjemmesiden. Pages overtager den automatisk. |
   | AAAA | `@` | `100::` | Proxied | Pladsholder, så roddomænet kan viderestilles af Cloudflare |
   | MX | `@` | `.` (prioritet 0) | – | "Null MX": domænet modtager ikke mail |
   | TXT | `@` | `v=spf1 -all` | – | Domænet sender aldrig mail |
   | TXT | `_dmarc` | `v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s` | – | Afvis falske mails i SGA's navn |

3. **Viderestilling af roddomænet:** Rules → Redirect Rules → Create rule:
   - *Hostname equals* `sgacreatives.com`
   - Dynamic redirect: `concat("https://www.sgacreatives.com", http.request.uri.path)`
   - 301, **Preserve query string** slået til.
4. **Hos Simply:** Domænet → **Navneservere** → skift til de to nameservere, Cloudflare viser (fx `xxx.ns.cloudflare.com`). Skiftet slår igennem inden for minutter til et døgn. Cloudflare sender en mail, når zonen er aktiv.
5. **Kontrollér** med testene under "Test efter lancering" ovenfor:
   - `https://sgacreatives.com/work/?x=1` skal give 301 til `https://www.sgacreatives.com/work/?x=1`.
   - www skal give 200 med gyldigt certifikat.
6. Simplys URL-viderestilling bruges ikke længere og kan slettes.

**Fortryd:** Sæt nameserverne tilbage til `ns1/ns2/ns3.simply.com` hos Simply. Records og viderestilling hos Simply ligger der stadig.

### Trin B: Registreringen til Cloudflare (fra ca. 17.10.2026)

1. Hos Simply: slå **transferlåsen fra** for domænet og hent **overførselskoden** (EPP/auth-kode).
2. Cloudflare → **Domain Registration → Transfer Domains** → vælg sgacreatives.com → indtast koden → betal ét års fornyelse. Domænet forlænges til august 2028.
3. Godkend overførslen i den mail, der kommer. Overførslen tager op til 5 dage. Hjemmesiden kører uændret imens.
4. Når Cloudflare viser domænet som overført: **opsig Simply** og slå automatisk fornyelse fra dér.

Cloudflare Registrar kræver, at domænet bruger Cloudflare DNS (trin A), og betales med kort i USD.

## Gendannelse

- **Fejl i en ny version:** Cloudflare, derefter projektet, **Deployments**, vælg en tidligere deployment og **Rollback to this deployment**. Det sker med det samme.
- **Via Git:** `git revert <commit>` og push. Så bygges og publiceres den forrige tilstand.
- **Lokalt:** Hele sitet kan genskabes ud fra `content/`, `tools/` og `assets/`:
  ```bash
  python3 tools/optimize_media.py   # billeder og video
  python3 tools/make_brand.py       # wordmark, favicons, app-ikoner
  python3 tools/make_webfont.py     # Inter-webfonten
  python3 tools/build_site.py       # HTML, sitemap, headers
  ```
  Kræver Python 3.10+ med Pillow (AVIF/WebP) og fontTools samt ffmpeg.
- **DNS:** Slet `www`-CNAME og viderestillingen hos Simply, og genskab de records, der var noteret før ændringen.

## Tekniske valg

- **Fonte:** Inter (medium 500, tre størrelser) til al tekst, skåret til latin og vægt 400 til 600 (40 KB). Wordmarket er Oswald, men ligger som SVG-stier, så Oswald ikke indlæses. Begge er under SIL OFL 1.1 og hostes lokalt, uden kald til Google.
- **Billeder:** AVIF og WebP i 480/800/fuld bredde med `srcset`, JPEG-fallback, faste dimensioner (ingen layout-skift) og lazy loading under heroen.
- **Video:** Kun Nike-casen, med poster, kontroller og `preload="none"`. Ingen autoplay og ingen lyd uden klik.
- **Bevægelse:** Kort hero-indgang, reveals ved scroll, let billedskalering og glidende menu. Alt slås fra ved `prefers-reduced-motion`. Uden JavaScript er alt indhold synligt, og navigationen vises som almindelige links.
- **Sikkerhed:** `_headers` sætter Content-Security-Policy, X-Frame-Options, nosniff, Referrer-Policy og Permissions-Policy. CSP'en indeholder en hash af det lille inline-script i `<head>`, og `build_site.py` opdaterer den automatisk.
- **Ingen cookies og ingen tracking.** Tilføjes der analytics senere, skal behovet for cookiebanner og privatlivstekst vurderes.

## Udførte tests (seneste: kvalitetsgennemgang af det hvide redesign 9. oktober 2026)

Testet mod `python3 -m http.server` med Chrome (Playwright) og Lighthouse:

- Alle 12 sider (forside, Services, Projects, About me, Contact, 5 cases, 404) ved 390 og 1440 px: ingen konsolfejl, ingen fejlede requests, ingen billeder, der ikke loader, én `h1` pr. side. Vandret scroll tjekket ved 360, 390, 768, 1024 og 1440 px.
- Lighthouse (forside og About me på mobil, en caseside på desktop): 100 i accessibility, best practices og SEO.
- Simuleret 4G og 4x langsommere CPU: første indhold på 0,4 til 0,6 s, LCP 0,57 til 0,67 s på forside, Projects og About me, og ingen layout-skift.
- Mobilmenu (fokus, Escape), tastaturrækkefølge, swipe-feeden på mobil ned og op, logoet til toppen fra alle positioner og visning uden JavaScript.

**Ikke testet:** rigtige iOS- og Android-enheder, Safari og Firefox samt skærmlæser.

### Tidligere: mobilgennemgang 29. september 2026 (det mørke design)

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
