# SGA creatives: hjemmeside

Statisk hjemmeside for SGA creatives (Sarah Al-farhan). Den forbinder brands med kreative mennesker og leder projekter inden for branding, kampagner og kulturelle oplevelser. Målgruppen er fashion-, footwear-, lifestyle- og kulturbrands.

- Repo: https://github.com/AliStair0550/sga-creatives (offentligt, branch `main`)
- Hosting: Cloudflare Pages, build output `public/`, ingen build-kommando
- Domæne: **https://www.sgacreatives.com** (primær). DNS hos Simply: `www` er CNAME til `sga-creatives.pages.dev`. Roddomænet `sgacreatives.com` skal viderestilles via Simplys "URL viderestilling".
- Pages-adresse: https://sga-creatives.pages.dev
- Beslutning 29.9.2026: domæne og DNS bliver hos Simply. Egen mail købes senere som Simply Basic Mail (se README "Hvis Sarah senere vil have egen mail"). Flytning til Cloudflare er ikke planlagt.
- Fuld vejledning til drift, DNS og gendannelse: `README.md`

## Redesign på branch `redesign-hvid` (oktober 2026)

Denne branch erstatter det mørke udtryk. Hvor reglerne nedenfor strider mod dette afsnit, gælder dette afsnit.

- **Hvidt først:** baggrund #FFFFFF, Ink #171918 til tekst, `--red` til små markeringer. Cases har ingen egne toner længere (`tone` i `cases.json` bruges ikke).
- **Logo:** wordmark `sga.creatives` i Oswald Regular, genereret som SVG-stier af `tools/make_brand.py` (`sga-creatives-wordmark-*.svg`). Oswald indlæses ikke på sitet, så der stadig kun er to fontfamilier. Favicon er uændret indtil videre.
- **Typografi som renellmedrano.com:** én skrift, **Inter** (OFL) i medium 500, kun tre størrelser: `--t-s` 13 px (menu, billedtekster, detaljer), `--t-m` 20 til 26 px (tekst) og `--t-l` 32 til 56 px (hero, sidetitler, procesord). Stram linjeafstand, ingen spærrede versaler og ingen vægtkontrast. Hierarkiet skabes af luft og placering. Webfilen laves af `tools/make_webfont.py` fra `tools/fonts-src/Inter-VF.ttf`. Figtree og Archivo bruges ikke længere på sitet (kun som kilder i `make_brand.py`).
- **Topmenu:** wordmark til venstre, Home, Services, Projects, About me og Contact som ren tekst til højre. Den aktive side og hover er røde. Ingen knap og ingen kant. Footeren har ingen logo eller S-mærke.
- **Hero (forsiden):** kun "Where brands / meet culture." i rødt (`--red`) øverst til venstre og lookbook-billedet uden tekst (`rezet-lookbook-01-hero`) ved siden af, lidt nede og lidt til højre for midten. På mobil og tablet fylder heroen præcis én skærm.
- **Forsidens rækkefølge:** hero, projekterne ét ad gangen (firma over titel), derefter løftet "We connect brands with creative people and lead projects ..." som en lille sektion for sig med links til Projects og Services.
- **Projekt-feed på mobil (under 900 px):** projekterne snapper ét pr. skærm som en TikTok-feed (`scroll-snap`, `scroll-snap-stop: always`). `main.js` sætter `html.is-feed` kun mens heroen eller et projekt er midt på skærmen. Løftet efter projekterne er udgangen af feeden. Desktop scroller normalt.
- **Sider:** `/` forside, `/services/` (problem/løsning-par med "What it covers" og relaterede projekter; midlertidig tekst), `/work/` (Projects: to forskudte kolonner), `/about/` (About me: portræt, rolle, erfaring og My process, hvor ordene fyldes fra grå til sort ved scroll), `/contact/` (kontaktord, alle kontaktoplysninger skrevet ud og en kort tekst med link til About me), casesider i `/work/<slug>/`.

## Brand

- Retning: **Luxury meets urban culture**. Redaktionelt, premium og magasinagtigt. Færre ord, flere billeder.
- Farver (CSS-variabler i `public/assets/css/main.css`). **Mørkt først, lyst bagefter:**
  - Night `#0E0F0F` er grundbaggrunden (hero, work, about, footer).
  - Warm Paper `#F3F0E9` er den lyse verden (services, contact) og tekstfarven på mørkt.
  - Ink `#171918` er tekst på lyst.
  - Acid Note `#D8F267` bruges kun til små accenter (mærkets punktum, fokusring).
  - Deep red `#5E0B10` (`--red`) bruges til markering (::selection), kontaktordenes understregning og hover på ikon-knapper.
  - Bordeaux/Oxblood er udgået.
  - **Hver case har sin egen tone** (`tone` i `content/cases.json`): Kiosk og Ways to Style sort (#0C0C0C), Lookbook og Timberland dyb petrol (#0F2926), Nike dyb rød (#5E0B10). På forsiden skifter de sort, petrol, sort, petrol, rød. Nye cases får deres egen dybe tone med mindst AA-kontrast.
- Fonte:
  - **Figtree** (fed 700 til 800, stram spatiering) til logo og overskrifter. Det er en geometrisk grotesk i stil med Spotifys Circular. Vægtkontrast (700 mod 400) bruges i stedet for kursiv.
  - **Archivo** til brødtekst og spærrede versaler til labels.
  - Begge er under OFL og hostes lokalt. Der må højst være to familier.
- Logo: SVG-stier genereret af `tools/make_brand.py`. Mærket (favicon, app-ikon) er et skråt S af to kroge, der griber ind i hinanden: lys foroven, klar rød (#D2202A) forneden, på mørk flade. Den klare røde bruges kun i mærket, fordi #5E0B10 ikke kan ses i 16 px på mørkt. Se `brand/brandguide.html`.
- Ingen rullende tekst eller karuseller. Bevægelse er rolig: hero-indgang, reveals og let billedzoom.
- Minimal tekst: heroen har kun overskriften, ingen knapper og ingen ydelseslinje. Ingen numre på cases og ingen intro over casene.
- Forsidens rækkefølge: hero, services (problem → løsning), work (case-universer), about med process, contact.
- Services er par af kasser: **problem** (lys, venstre) og **løsning** (mørk, højre), som glider sammen ved scroll (`main.js` sætter `--p` pr. række) og låses med en ren mørk tap i et hak (intet logo i tappen). Hver kasse har kun én kort linje, uden labels, og linjerne holdes omtrent lige lange (to linjer ved alle bredder). Når de mødes, får rækken `.is-locked`, og der kommer et "klik". Teksterne står i `SERVICES` i `tools/build_site.py`. Scroll-styringen gælder kun desktop (fra 960 px). På mobil og tablet afspilles hvert par én gang, når det kommer ind (`.is-met`): en kort lodret bevægelse, tappen popper, et lille klik. Det er ren CSS-transition, fordi scroll-styring ryster på touch. Uden JS eller ved reduced motion står parrene låst fra start.
- Kontakt: Branding, Campaigns, Events og Collaborations springer ind ét ord ad gangen med en dyb rød understregning (samme rød som Nike, `--red`). Den ligger under ordene, ikke bag dem, af hensyn til kontrasten.
- About: portrættet afdækkes nedefra med zoom og glider let i rammen ved scroll (`data-scroll="parallax"`). "My process" er fire store ord i omrids, der fyldes fra venstre ved scroll (`data-scroll="fill"`), med en personlig linje i Sarahs stemme. Ingen pile. Titel: "Brand & Creative Manager".
- Kanten under topmenuen vises først, når man scroller.
- Casesider: én "Get in touch"-knap (details/summary), der folder ud til Email og Call. Ingen henvisning til kontaktsektionen.
- Kontakt: mail, telefon, LinkedIn og Instagram er runde ikon-knapper (ikke synlig adresse); labels vises ved hover. E-mailadressen står som tekst i footeren.
- Footer: kun Portfolio, Services, About og Contact (ingen caseliste). Claim, links og et kæmpe SGA-logo, der rejser sig ved scroll; "Back to top" uden pil; S-mærket snurrer ved hover.
- Topmenu: logo til venstre, **Portfolio** (`/work/`) og About til højre. Footeren har Portfolio, Services, About og Contact.
- Portfolio-siden (`/work/`) er et fedt indeks med kæmpe projektnavne. På desktop fyldes rækken ved hover med casens tone, de andre tones ned, og billedet følger musen (`main.js`). På touch vises en thumbnail. Casesidernes brødkrumme peger på Portfolio. Ingen Contact-knap (kontakt findes nederst og i footeren).

## Arkitektur

```
content/site.json      domæne, kontaktinfo
content/cases.json     de fem cases (tekst, roller, credits, billeder, alt-tekster)
tools/build_site.py    genererer ALLE html-sider + robots, sitemap, manifest, _headers i public/
tools/optimize_media.py  assets/ (originaler) -> public/assets/img + video (AVIF/WebP/JPEG)
tools/make_brand.py    logoer, favicons, delingsbillede
tools/make_webfont.py  Inter -> public/assets/fonts/Inter-VF.woff2 (latin, vægt 400 til 600)
tools/share/            delingsbilleder pr. side (node + playwright-core, bruger Google Chrome)
tools/retouch_lookbook_hero.py  hero-udgave af lookbook-coveret uden tekst (kræver numpy + opencv); originalen bruges på casesiden
tools/check.py         kvalitetsgate før commit
public/                det publicerede site (html genereres, css/js redigeres direkte)
assets/                originalmedier, ændres aldrig
docs/intern/           brief, CV, kildemateriale, AFKLARINGER.md. Lokalt, gitignored, ALDRIG i Git
```

## Arbejdsgang

Vi arbejder direkte i mappen og pusher til `main`. Cloudflare publicerer automatisk.

```bash
python3 tools/build_site.py
python3 tools/check.py        # skal være grønt
git add . && git commit -m "Kort beskrivelse på dansk" && git push
```

Lokal visning: `python3 -m http.server 8000 --directory public`, eller `npx wrangler pages dev public` for at få samme opførsel som Cloudflare (404, `_headers`, trailing slash).

## Faste regler

- **Sitet er på engelsk.** Det gælder tekst, metadata, alt-tekster og fejltekster (`lang="en"`). Dokumentation og commitbeskeder er på dansk.
- **Ingen lange tankestreger** (— eller –) på sitet eller i `content/`. Brug kolon, komma eller almindelig bindestreg. `check.py` fanger dem.
- **Billeder og pladsholdere:** Et galleribillede i `content/cases.json`, hvis fil ikke findes endnu, vises som en pladsholder. Læg `assets/images/<navn>.jpg`, kør `optimize_media.py` og `build_site.py`, og skriv alt-teksten i `cases.json`. `check.py` fejler, hvis et nyt billede mangler alt-tekst. Portrættet i About hedder `sarah-al-farhan-01`.
- **Rediger aldrig html i `public/` direkte.** Ret i `content/` eller `tools/build_site.py`, og byg. CSS og JS i `public/assets/` redigeres direkte.
- **Korrekt kreditering:** Sarahs tidligere arbejde vises som hendes arbejde med dokumenteret rolle og arbejdsgiver (Rezet Store, konsulent for Nike), aldrig som SGA-opgaver. Opfind aldrig kunder, credits, resultater, citater, årstal eller virksomhedsoplysninger. Er noget uafklaret, noteres det i `docs/intern/AFKLARINGER.md`.
- **Repoet er offentligt:** CV, brief og interne noter ligger kun i `docs/intern/`. Ingen hemmeligheder i Git. `check.py` scanner for begge dele.
- Bevægelse bruger transform og opacity og respekterer `prefers-reduced-motion`. Alt indhold og al kontakt skal virke uden JavaScript.
- Test ved 360, 390, 768, 1024 og 1440 px før større ændringer. Rapportér kun tests, der faktisk er kørt.
- Publicering og DNS-ændringer hos Simply og Cloudflare kræver aftale først.
