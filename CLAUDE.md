# SGA creatives: hjemmeside

Statisk hjemmeside for SGA creatives (Sarah Al-farhan). Den forbinder brands med kreative mennesker og leder projekter inden for branding, kampagner og kulturelle oplevelser. Målgruppen er fashion-, footwear-, lifestyle- og kulturbrands.

- Repo: https://github.com/AliStair0550/sga-creatives (offentligt, branch `main`)
- Hosting: Cloudflare Pages, build output `public/`, ingen build-kommando
- Domæne: **https://www.sgacreatives.com** (primær). DNS hos Simply: `www` er CNAME til `sga-creatives.pages.dev`. Roddomænet `sgacreatives.com` skal viderestilles via Simplys "URL viderestilling".
- Pages-adresse: https://sga-creatives.pages.dev
- Fuld vejledning til drift, DNS og gendannelse: `README.md`

## Brand

- Retning: **Luxury meets urban culture**. Redaktionelt, premium og magasinagtigt. Færre ord, flere billeder.
- Farver (CSS-variabler i `public/assets/css/main.css`). **Mørkt først, lyst bagefter:**
  - Night `#0E0F0F` er grundbaggrunden (hero, work, about, footer).
  - Warm Paper `#F3F0E9` er den lyse verden (services, contact) og tekstfarven på mørkt.
  - Ink `#171918` er tekst på lyst.
  - Acid Note `#D8F267` bruges kun til små accenter (mærkets punktum, fokusring).
  - Bordeaux/Oxblood er udgået.
  - **Hver case har sin egen tone** (`tone` i `content/cases.json`): Kiosk sort, Lookbook lys salvie-oliven (#B3B18C, mørk tekst), Ways to Style grafit, Timberland dyb petrol og Nike dyb rød (#5E0B10). Nye cases får deres egen dybe tone med mindst AA-kontrast.
- Fonte:
  - **Figtree** (fed 700 til 800, stram spatiering) til logo og overskrifter. Det er en geometrisk grotesk i stil med Spotifys Circular. Vægtkontrast (700 mod 400) bruges i stedet for kursiv.
  - **Archivo** til brødtekst og spærrede versaler til labels.
  - Begge er under OFL og hostes lokalt. Der må højst være to familier.
- Logo: SVG-stier genereret af `tools/make_brand.py`. Mærket er et fedt Figtree-S med et acid-punktum. Se `brand/brandguide.html`.
- Ingen rullende tekst eller karuseller. Bevægelse er rolig: hero-indgang, reveals og let billedzoom.
- Minimal tekst: heroen har kun overskriften, ingen knapper og ingen ydelseslinje. Ingen numre på cases og ingen intro over casene.
- Forsidens rækkefølge: hero, services (problem → løsning), work (case-universer), about med process, contact.
- Services er par af kasser: **problem** (lys, venstre) og **løsning** (mørk, højre), som glider sammen ved scroll (`main.js` sætter `--p` pr. række) og låses med SGA-nøglen (S med acid-punktum) i et hak. Når de mødes, får rækken `.is-locked`, og der kommer et "klik". Teksterne står i `SERVICES` i `tools/build_site.py`. Uden JS eller ved reduced motion står parrene låst fra start.
- Kontakt: Branding, Campaigns, Events og Collaborations springer ind ét ord ad gangen med en acid-highlighter.
- Kanten under topmenuen vises først, når man scroller.
- Topmenu: logo til venstre, Work, Services og About til højre. Ingen Contact-knap (kontakt findes nederst og i footeren).

## Arkitektur

```
content/site.json      domæne, kontaktinfo
content/cases.json     de fem cases (tekst, roller, credits, billeder, alt-tekster)
tools/build_site.py    genererer ALLE html-sider + robots, sitemap, manifest, _headers i public/
tools/optimize_media.py  assets/ (originaler) -> public/assets/img + video (AVIF/WebP/JPEG)
tools/make_brand.py    logoer, favicons, delingsbillede
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
