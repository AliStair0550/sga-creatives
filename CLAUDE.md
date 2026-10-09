# SGA creatives: hjemmeside

Statisk hjemmeside for SGA creatives (Sarah Al-farhan). Den forbinder brands med kreative mennesker og leder projekter inden for branding, kampagner og kulturelle oplevelser. Målgruppen er fashion-, footwear-, lifestyle- og kulturbrands.

- Repo: https://github.com/AliStair0550/sga-creatives (offentligt, branch `main`)
- Hosting: Cloudflare Pages, build output `public/`, ingen build-kommando
- Domæne: **https://www.sgacreatives.com** (primær). DNS hos Simply: `www` er CNAME til `sga-creatives.pages.dev`. Roddomænet `sgacreatives.com` skal viderestilles via Simplys "URL viderestilling".
- Pages-adresse: https://sga-creatives.pages.dev
- Beslutning 29.9.2026: domæne og DNS bliver hos Simply. Egen mail købes senere som Simply Basic Mail (se README "Hvis Sarah senere vil have egen mail"). Flytning til Cloudflare er ikke planlagt.
- Fuld vejledning til drift, DNS og gendannelse: `README.md`

## Brand og udtryk (hvidt redesign, live fra oktober 2026)

Det mørke udtryk fra september 2026 er udgået. Det ligger i Git-historikken før commit `2f0f14d`.

- Retning: hvid luft, ét projekt ad gangen og rolig typografi i stil med renellmedrano.com. Hero og topmenu er bygget i stil med groove-intl.com. Færre ord, flere billeder.
- **Farver** (CSS-variabler i `public/assets/css/main.css`): hvid `#FFFFFF` er baggrunden overalt, Ink `#111111` er tekst, grå `--muted` `#737373` er sekundær tekst, og deep red `#5E0B10` (`--red`) bruges kun til små markeringer: aktiv side og hover i menuen, ::selection og kontaktordenes understregning. Cases har ingen egne farvetoner (`tone` i `cases.json` bruges ikke).
- **Typografi:** én skrift, **Inter** (OFL) i medium 500 med kun tre størrelser: `--t-s` 13 px (menu, billedtekster, detaljer), `--t-m` 20 til 26 px (tekst) og `--t-l` 32 til 56 px (sidetitler, procesord). Hero-overskriften har sin egen, større størrelse. Stram linjeafstand, ingen spærrede versaler og ingen vægtkontrast. Hierarkiet skabes af luft og placering. Webfilen laves af `tools/make_webfont.py`. Inter er valgt for nu; en mere særpræget skrift kan overvejes senere.
- **Logo:** wordmark `sga.creatives` i Oswald Regular som SVG-stier fra `tools/make_brand.py` (`sga-creatives-wordmark-*.svg`, med lidt luft i viewBox, så kantbogstaverne ikke klippes). Oswald indlæses ikke på sitet.
- **Favicon og app-ikoner:** "sga" fra wordmarket i hvidt på sort (`icon_svg()` og `raster_icon()` i `make_brand.py`). Det gamle S-mærke findes kun i `brand/` til brandguiden.
- **Topmenu:** wordmark til venstre, Services, Projects, About me og Contact som ren tekst til højre. Der er ingen Home: logoet er vejen hjem og fører altid til toppen af forsiden (`[data-home]` i `main.js`). Den aktive side og hover er røde. Ingen knap og ingen kant. På mobil er der en burgermenu.
- **Footer:** claimen "Where brands meet culture.", wordmarket under den (også et link til toppen af forsiden) og kontaktoplysningerne. Ingen sidelinks.
- **Forsiden**, i denne rækkefølge:
  - Hero: kun "Where brands / meet culture." stort i sort, rykket ind mod midten. Ved siden af, lidt nede og til højre for midten, to billeder i lag (`HERO_FRONT` og `HERO_BACK` i `build_site.py`): Timberland × Rezet (`timberland-rezet-04`) forrest og adidas Ways to Style (`adidas-ways-to-style-01`, de røde bukser) mindre, højere og til højre bagved. Det bageste glider ud bagfra ved indlæsning og driver hurtigere opad ved scroll.
  - Projekterne ét ad gangen midt på siden med firma over projekttitel under billedet. Nike først (`HOME_ORDER`), derefter rækkefølgen i `cases.json`. Rezet Lookbook vises med coveret uden tekst (`rezet-lookbook-01-hero`, alt-tekst i `card_alt`), og Timberland med `timberland-rezet-03`, så det ikke gentager hero-billedet.
  - Løftet "We connect brands with creative people across campaigns and cultural experiences." som en sektion for sig med streger over og under hele vejen ud til kanten. Den nederste streg er grænsen til footeren.
- **Projekt-feed på mobil og tablet (under 900 px):** heroen fylder præcis én skærm, og projekterne snapper ét pr. skærm som en TikTok-feed (`scroll-snap`, `scroll-snap-stop: always`). `main.js` sætter `html.is-feed` kun mens heroen eller et projekt er midt på skærmen. Løftet er udgangen af feeden. Desktop scroller normalt.
- **Services** (`/services/`): enkle rækker med navnet til venstre og problemet i gråt og løsningen til højre. Ingen klodser, tags eller projektlinks. Teksterne står i `SERVICES` i `build_site.py` og er midlertidige, indtil Sarah sender sine egne.
- **Projects** (`/work/`): alle projekter i to forskudte kolonner med samme billedtekst som på forsiden. Første række vises med det samme (ingen fade), resten kommer ind ved scroll.
- **About me** (`/about/`): portræt (afdækkes nedefra og driver let ved scroll), navn, titel "Brand & Creative Manager", 13+ år, erfaring og "My process": fire ord, der fyldes fra grå til sort ved scroll, med en linje i Sarahs stemme. Ingen CTA nederst.
- **Contact** (`/contact/`): "Let’s make something happen.", Branding, Campaigns, Events og Collaborations med tynd rød understregning, alle kontaktoplysninger skrevet ud med ikon og en kort tekst med link til About me.
- **Casesider** (`/work/<slug>/`): firma, titel og undertitel centreret over coveret, intro, fakta, galleri, Sarahs arbejde og credits, "Next project" og en "Get in touch"-knap (details/summary), der folder ud til Email og Call.
- **Billeder, der mangler:** galleribilleder, der ikke findes endnu, vises ikke (`visible_gallery()` i `build_site.py`), og rækkerne udjævnes, så intet står halvtomt. `check.py` lister dem.
- **Delingsbilleder** (`public/assets/og/`) er i den hvide stil. Lav dem igen med `cd tools/share && node make_share_images.mjs`, når hero, cases eller billeder ændres.
- **Bevægelse** er rolig: indgang i heroen, reveals ved scroll og let billedzoom. Ingen rullende tekst eller karuseller (swipe-feeden på mobil er almindelig scroll med snap).
- **Uden JavaScript** er alt synligt, og på mobil ligger headeren i sidens flow, så den ombrudte menu aldrig dækker første overskrift.

## Arkitektur

```
content/site.json      domæne, kontaktinfo
content/cases.json     de fem cases (tekst, roller, credits, billeder, alt-tekster)
tools/build_site.py    genererer ALLE html-sider + robots, sitemap, manifest, _headers i public/
tools/optimize_media.py  assets/ (originaler) -> public/assets/img + video (AVIF/WebP/JPEG)
tools/make_brand.py    wordmark, favicons, app-ikoner
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
- **Billeder:** Et galleribillede i `content/cases.json`, hvis fil ikke findes endnu, vises ikke. Læg `assets/images/<navn>.jpg`, kør `optimize_media.py` og `build_site.py`, og skriv alt-teksten i `cases.json`. `check.py` fejler, hvis et nyt billede mangler alt-tekst. Portrættet på About me hedder `sarah-al-farhan-01`.
- **Rediger aldrig html i `public/` direkte.** Ret i `content/` eller `tools/build_site.py`, og byg. CSS og JS i `public/assets/` redigeres direkte.
- **Korrekt kreditering:** Sarahs tidligere arbejde vises som hendes arbejde med dokumenteret rolle og arbejdsgiver (Rezet Store, konsulent for Nike), aldrig som SGA-opgaver. Opfind aldrig kunder, credits, resultater, citater, årstal eller virksomhedsoplysninger. Er noget uafklaret, noteres det i `docs/intern/AFKLARINGER.md`.
- **Repoet er offentligt:** CV, brief og interne noter ligger kun i `docs/intern/`. Ingen hemmeligheder i Git. `check.py` scanner for begge dele.
- Bevægelse bruger transform og opacity og respekterer `prefers-reduced-motion`. Alt indhold og al kontakt skal virke uden JavaScript.
- Test ved 360, 390, 768, 1024 og 1440 px før større ændringer. Rapportér kun tests, der faktisk er kørt.
- Publicering og DNS-ændringer hos Simply og Cloudflare kræver aftale først.
