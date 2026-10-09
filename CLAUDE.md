# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A website redesign for **The Friends of Hendricks** — a 501(c)(3) run by parent volunteers
that raises money for Hendricks Avenue Elementary School in Jacksonville, Florida. Their
current site is stock WordPress (Astra theme) at `friendsofhendricks.com`.

**This is not an application.** It is a set of self-contained HTML mockups presenting five
competing design directions to the organization's board, who will pick one. No framework, no
package manager, no tests, no dependencies beyond Python 3 with Pillow. The chosen direction
becomes a real site later; nothing here is the production site.

Hosting, content editing and form handling are **deliberately undecided** — see
`docs/hosting-and-decisions.md`. Don't resolve those without being asked.

## Build

```bash
python3 mockups/build.py          # mockups/src/*.html -> mockups/*.html  (Artifact fragments)
python3 mockups/build.py --site   # mockups/src/de-*.html -> site/        (a real website)
python3 mockups/encode_mobile.py  # docs/videos/*-540.mp4, the phone-sized clips
python3 mockups/cut_clips.py      # docs/videos/arrival*.mp4, the warm clip with bad shots cut
python3 mockups/encode_videos.py  # regenerate mockups/.videos.json from docs/videos/
python3 mockups/trim_sponsors.py  # trim logo margins, record each logo's shape ("ar")
uv run --no-project --with weasyprint mockups/levels_pdf.py   # mockups/sponsor-levels.pdf
```

**The sponsor walls are generated, not written.** `{{SPONSOR_WALL_LEGACY}}` (and
`_VISIONARY`, `_INVESTORS`, `_BUILDERS`) expands from `.sponsor-names.json` alongside the
partials. Each entry has `key`, `tier`, `name`, `url` and `ar`; a non-empty `url` turns the
card into a link out, an empty one leaves a plain box. Logos are sized by **area**, not by
filling the card — `AREA` in `build.py` — so a long wordmark and a square badge carry about
the same weight. Next year's sponsors: add the JPEG to `.sponsors.json`, the entry to
`.sponsor-names.json`, run `trim_sponsors.py`, rebuild. All 37 `url` fields are empty until
the committee supplies the websites — do not guess them.

**`sponsor-levels.pdf` is read out of `de-partners.html`.** `levels_pdf.py` parses the five
tiers and lays them out as a comparison chart; every benefit must match a row in its `ROWS`
or the script stops, so a changed benefit cannot silently drop off the printed sheet. The PDF
is committed; `{{LEVELS_PDF}}` becomes a file in `site/` and a data URI in the mockups. Rerun
it whenever the levels change. Headless Brave (the only Chromium here) starts and never
prints, which is why it uses WeasyPrint through uv rather than a browser.

**Two outputs, one set of sources.** They differ only in what the tokens resolve to,
which is the whole reason the pages go through tokens rather than carrying URLs of their
own:

| | `build.py` | `build.py --site` |
|---|---|---|
| Output | `mockups/*.html`, all 20 | `site/`, the seven `de-*` only |
| Shape | fragments — the Artifact host adds `<!doctype>`, `<head>`, `<body>` | full HTML documents, with `charset`, `viewport`, `description`, Open Graph and a real favicon |
| Images | inlined as data URIs | files in `site/img/`, `{{HERO}}` → `img/hero.jpg` |
| Video | inlined; the loader decodes base64 into a blob | files in `site/video/`; the loader takes the URL and the browser streams it |
| Links | absolute artifact URLs from `.links.json` | relative filenames from `SITE_PAGES` |
| Home page | ~4 MB | ~44 KB |

Site mode **prunes anything no page references** — it dropped 3.7 MB on the first run,
including the unused third video clip. `site/` is wiped and rewritten each time, so never
hand-edit it. It *is* committed, because the video comes from git-ignored `.videos.json`
and a CI runner could not rebuild it; `.github/workflows/pages.yml` uploads the folder as-is.

**Always edit `mockups/src/`, never `mockups/*.html`** — the latter are generated and will be
overwritten.

`build.py` substitutes tokens and does two other things, both added when the site went from two
pages to seven:

- **`{{> name }}` pulls in `mockups/src/_partials/name.html`.** The theme tokens, base
  stylesheet, nav, footer, scripts and the video loader are identical on all seven pages. Seven
  copies of a nav is seven places to get a link wrong. Partials expand before token
  substitution, so a partial can use tokens — which is how the nav gets its URLs.
- **`{{URL_HOME}}` and friends resolve from `mockups/.links.json`.** Each page is its own
  Artifact with its own URL, so cross-page links have to be absolute. A key whose value is
  empty resolves to `#`, which is what makes the first publish possible: build, publish, paste
  the URLs into `.links.json`, rebuild, republish.

A page that wants real footage sets `<span id="film-src" data-video="{{VIDEO_WARM}}" hidden>`
and includes `{{> film }}`. The partial is the same everywhere; only the clip differs.

**`henry-modal` is the one partial that is not shared.** It carries the Hugs from Henry
Birthday Club dialog and its script, and only `de-takepart` includes it, so the other six
pages do not pay for markup they never show. Its *styling* lives in `de-takepart`'s own
`<style>` block with the rest of that page's CSS, not in `base.html`.

The button that opens it is a real link to the donate page (`{{URL_DONATE}}#gift`). The
script only takes it over where `dialog.showModal` exists, so with no scripting the button
still lands somewhere useful. Same rule as the mobile nav: never put something behind a
button that scripting has to build.

**`preventDefault()` alone does not stop a cross-page link inside an Artifact.** The host
frame runs its own click listener in the **capture** phase: any `<a>` whose `href` resolves
to a different origin is turned into a navigation of the whole top frame, and it reads the
`href` attribute at click time. Capture beats a listener on the element, so the host had
already sent the page away before our handler ran — the dialog opened and the page left
underneath it. The fix is to stop the link being cross-origin at all: the script does
`open.setAttribute('href','#henry')` before wiring the click, and a same-origin fragment is
the one thing that listener ignores. The cross-origin `href` stays in the markup for the
no-script case. Any future in-page control built on a `{{URL_*}}` link needs the same
handover.

**`--photo` is declared per page, not in `tokens.html`.** It holds the 400 KB hero photograph,
and a page with no `.media` backdrop should not carry it — `de-sponsors` and `de-partners` do
not. The five that do declare `:root{--photo:url("{{HERO}}")}` in their own style block, right
after `{{> base }}`. If you add a `.media .layer` to a page, add that declaration too or the
backdrop comes up empty.

`spiritNight` is the **one WebP** in `.assets.json`; every other image is JPEG or PNG. It is
the Upcoming Spirit Nights flyer, which is flat color and dense lettering — the case JPEG is
worst at. WebP q90 comes out at 142 KB where JPEG q86 needs 203 KB *and* smears the text.
Re-encode it from `docs/photos/spirit-night.webp`, not from the old 760×760 banner it
replaced. The flyer is portrait, so its `.shot` on `de-takepart` carries `.tall` (4/5) —
the page default of 4/3 would crop through the dates.

Every key in `mockups/.assets.json` becomes a token: `logo` → `{{LOGO}}`, `heroSm` →
`{{HERO_SM}}`, `rockWalk` → `{{ROCK_WALK}}` (camelCase splits on capitals). Videos in
`.videos.json` become `{{VIDEO_REEL}}`, `{{VIDEO_WARM}}`, `{{VIDEO_ENERGY}}`. A `{{VIDEO_*}}`
token with no matching asset is replaced with an empty string so pages still build and fall
back to a still photograph.

| File | Size | Tracked | Why |
|---|---|---|---|
| `mockups/.assets.json` | ~3.6 MB | **yes** | Images as data URIs. `docs/` is git-ignored, so this is the only committed copy of the logo and photography — the build cannot run without it. |
| `mockups/.sponsors.json` | ~790 KB | **yes** | The 37 sponsor logos, downscaled to 400px, as data URIs — `{{SPONSOR_DOPAZO}}` and so on. Same reasoning as `.assets.json`: `docs/` is git-ignored, so this is the only committed copy. |
| `mockups/.sponsor-names.json` | ~6 KB | **yes** | Which logo belongs to which business, at which level, its website, and its shape. Names read off the artwork, not guessed. |
| `mockups/sponsor-levels.pdf` | ~90 KB | **yes** | Made by `levels_pdf.py`; the build only copies it. |
| `mockups/.links.json` | ~700 B | **yes** | Page key → Artifact URL. |
| `mockups/.videos.json` | ~10 MB | **no** | Regenerate with `encode_videos.py`. Never commit. |

## Publishing

Pages are **Artifact fragments**, not documents: no `<!doctype>`, `<html>`, `<head>` or
`<body>` — the publish step wraps them. Each page starts with `<title>`, a Google Fonts
`<link>`, then `<style>`.

Publish with the Artifact tool, one file per call. A **strict CSP blocks every external host
except Google Fonts**, which is why all imagery is inlined as data URIs. Page ceiling is 16 MB;
the heaviest page (`e-home`) is ~4.7 MB.

Each page has its own URL, so **cross-page links must be absolute artifact URLs**, not
`b-partners.html`. When adding a page: publish it, then rewrite the links that point at it,
then republish the pages that changed. Republishing the same file path in the same
conversation keeps the URL; from a different conversation you must pass `url`.

| | Home | Business Partner |
|---|---|---|
| Hub (start here) | `613a6c9c-00ad-4313-997e-61f31151096d` | — |
| A — Standing Strong | `5bb94452-833e-46f5-9822-ca09f6f31909` | `2e88d275-fba1-4a65-a08d-05cf1678350d` |
| B — Schoolyard | `eddf114f-a3c2-4289-8ad7-48c4059ef47f` | `304fea92-5e77-457b-ba50-f1b3f082bd14` |
| C — Momentum | `e76783e1-0af7-4f36-ab61-904479e3aa43` | `48107c90-2860-4a47-a420-2e58d400305d` |
| D — Reel | `5471b56d-174d-4494-9e7d-646e544f1967` | `382de4cb-6c77-4cc0-9efb-3a747870bd89` |
| E — Foundation | `e96a67bd-9f6f-4bea-a7a9-988260b1a179` | `f77ac934-4f1e-425b-a154-c892cc964dc1` |
| Video explainer | `21484430-3404-4703-bff3-2c78d8559706` | — |

The board voted on 2026-08-22: **D 3, E 2, B 1** — six votes from three people, so each
named two favorites and D was on every list. A and C are out.

Two prototypes of the D/E split follow. They share one home page and differ only in the
sponsor page. The original A–E artifacts are frozen as the record of the vote — `de-*` are
separate files, not edits to them.

**Chosen on 2026-08-24: direction D, reading A** — `de-home` plus `de-partners`, one dark
world across both pages. (The palette was inverted to light on 2026-08-28; see below.)
`de-partners-light`
(reading B) is superseded. It is still published, but nothing points at it any more; leave it
as a record rather than editing it.

**Direction D is the chosen design as of 2026-08-24, and the whole site is now built in it.**
Seven pages, all sharing the partials above.

| Page | Source | Artifact | Favicon |
|---|---|---|---|
| Home | `de-home` | `66ba65c8-e1fb-417c-a6c0-aa08f0f2e51e` | 🎞️ |
| Donate | `de-donate` | `482858ed-dcb9-4fee-9a30-4004281de3bf` | 💛 |
| Walkathon | `de-walkathon` | `dac7a340-6fae-441d-92af-cdbf76e9252e` | 👟 |
| Our Sponsors | `de-sponsors` | `1bdee726-6dbc-4391-9a2b-f235c9e92270` | 🏅 |
| Become a Sponsor | `de-partners` | `9629bc70-f0aa-4c2f-8ec3-c3f46adb324e` | 🌑 |
| Take Part | `de-takepart` | `e190645b-1e7f-4990-81e9-3b0eaf86b52e` | 🎪 |
| Meet the Parents | `de-parents` | `46960c6b-6472-4131-962e-acbf588687e1` | 👪 |

Navigation is six top-level items with two dropdowns — Sponsors opens to *Our Sponsors* and
*Become a Sponsor*; Take Part opens to the three programme anchors on one page. Dropdowns open
on `:hover` **and** `:focus-within`, so they work from the keyboard with no script.

**`.nohero` has to out-specify `.sect.tight`.** A page with no hero starts underneath the
fixed bar and needs `padding-top:calc(var(--nav-h) + …)` to clear it. `.sect.tight` is two
classes and beat a bare `.nohero` regardless of order, and its `padding` *shorthand* then
rewrote the top value — which is why the first red eyebrow on `de-donate`, `de-sponsors`,
`de-takepart` and `de-parents` sat on the nav hairline. The rule is now written
`.nohero,.sect.nohero` so the two tie on weight and source order decides. `de-partners` was
always right because it uses `sect nohero` with no `tight`.

**That fixed the cascade; the phones needed a measurement fix too (2026-08-28).** The
clearance is `calc(var(--nav-h) + …)`, which is only ever right if the bar really is
`--nav-h` tall. On desktop it is — `.topnav` sets `height:var(--nav-h)`. Below 1080px that
hard height is thrown away for `height:auto` + `flex-wrap:wrap` + 24px of new padding, so a
bar that wrapped to two rows stood ~110px tall against a 72px token and the first red eyebrow
landed under the hairline. `scroll-margin-top` had the same stale number, so `#henry`,
`#rock`, `#spirit`, `#levels` and `#gift` did too. Three changes:

- `.js .topnav:not(.open){height:var(--nav-h)}` — with scripting on and the menu shut, the
  bar is now exactly what the token claims. Open, or with no script, it still grows and
  stacks its links, which is the deliberate fallback.
- A `@media (max-width:400px)` block keeps the row on one line. **Measured on 2026-10-07,
  not estimated:** with the wordmark beside the logo the row needs ~350px, and at a true 320px
  the Donate pill wrapped under the bar — it already did before the logo grew. So below 400px
  the wordmark is visually hidden (still read by screen readers) and the logo card carries the
  name. **If anything is ever added to the bar, re-render it at 320px.**
- The logo is a full lockup and its navy "HENDRICKS" disappears on the film, so it sits on a
  white card: 50px tall under 760px, 62px above, 46px under 400px. The home hero carries a
  large copy (`.crest`) — the committee asked for the logo to be more prominent.
- The floor rose: `clamp(40px,6vw,78px)` → `clamp(52px,6vw,78px)`, and `scroll-margin-top`
  from `+14px` to `+20px`. At 375px the `6vw` term sits at its floor, which is exactly when
  the bar is tallest.

**Two form rules that are easy to reintroduce.** `.field input` sets `width:100%` and 13px of
padding, which is right for a text box and stretches a checkbox or radio into a full-width
slab — hence `.field input[type=checkbox],.field input[type=radio]{width:auto;padding:0}`.
And `.field label` is small shouting uppercase, which is right over a text box and wrong
wrapped around a sentence, so a label that wraps a control takes `class="plain"`.

**The mobile nav has no JS-only failure mode.** Below 1080px, with no script, the bar simply
grows and stacks its links. `head.html` adds `.js` to the root element, and only then does the
CSS collapse the panel behind the Menu button. Never hide the links behind a button that
scripting has to create.

`de-partners-light` (reading B of the old D/E split) is superseded. It is still published at
`fa353c4f-76a0-4436-856e-35a12fba5dc9` as a record of that exploration — leave it alone.

**Navigation on the `de-*` pages.** D's fixed bar moved from the bottom of the page to the
top, following obama.org: `position:fixed; top:0`, transparent while it sits on the hero
photograph, filling in with a blurred surface and a hairline rule once you scroll past it.
The **filled state is the CSS default** and a script adds `.over-hero` — so with no JS the
bar is legible rather than white-on-white. Anchored sections carry
`scroll-margin-top: calc(var(--nav-h) + 20px)` so in-page links don't land underneath it.
D's persistent bottom donate bar is gone; the ask now rides in the top bar instead.

**The site is light, and the film inside it is dark (2026-08-28).** D shipped as a single
dark world with a `Light mode` button; that reversed. There is now **one palette, light**, no
toggle, no `localStorage`, no `.lite` class, and nothing that reads the viewer's theme. The
dark values survive in exactly one rule, at the bottom of `tokens.html`:

```css
.act1,.frame,.close,.filmcap,.past figure,.topnav.over-hero{ … color:var(--ink); }
```

That is the hero, the mid-page frame, the closing shot, the captioned photograph, the
Walkathon archive tiles and the top bar while it is still over the film. It is not a dark
mode — it is the veil over a photograph, and white type is the only thing readable on it.
Four things about the arrangement are easy to break:

- **The rule needs `color:var(--ink)`, not just the retoned tokens.** A custom property only
  affects declarations that *use* it inside that subtree. Headings carry no `color` of their
  own — they inherit the computed colour from `<body>`, which already resolved `var(--ink)`
  against `:root`. Without the `color` line every headline over a photograph comes out dark
  navy on a dark picture.
- **`color-scheme:light` is set on `body`, not `:root`.** The Artifact host writes
  `style.colorScheme` inline on the root and an inline style beats a stylesheet. `body` is
  untouched by the host, so declaring it there wins for everything below it.
- **`--nav-h` is a colour-free token living in the same `:root` block.** It and its
  `@media (min-width:760px)` companion must survive any edit to the palette.
- **Three gold fills had to change when the ground went pale.** Gold is 1.5:1 on paper.
  `.pill` keeps the gold fill but gains `border:1px solid var(--gold-ink)`, which draws an
  edge on the page and vanishes into the fill over a photograph, where `--gold-ink` resolves
  back to `#FFBE04`. The Walkathon thermometer fill (`de-walkathon`, `.goal .bar i`) went from
  `--gold` to `--gold-ink`, 1.4:1 → 5.1:1, because that bar carries a number. And
  `accent-color` on checkboxes went from `--gold` to `--navy`, 1.7:1 → 10.6:1 on white.

The palette: `--ground #F6F6F4`, `--raise #EFEEE7`, `--sink #EAE9E1`, `--ink #0B2340`,
`--muted #42536B`, `--faint #54637A`, `--navy`/`--navy-ink` both `#003E7E`, `--red`/`--red-ink`
both `#C71014`, `--gold #FFBE04` as a fill with `--gold-ink #7A5D00` as text, `--on-gold
#070F1A`, `--line #D6D5CC`, `--line-soft #E4E3DA`, `--edge #858479`, `--bar
rgba(246,246,244,.93)`, `--field #FFFFFF`, `--tile #FFFFFF`. Every resolved text pair passes
AA; the worst is `--red-ink` on `--sink` at 4.91:1. `--edge` clears 3:1 on all four surfaces.

Two token splits worth keeping in mind:

| Token | On paper | Over a photograph | Why |
|---|---|---|---|
| `--gold` (fill) | `#FFBE04` | `#FFBE04` | Gold behind dark text — 11.6:1. Never flips. |
| `--gold-ink` (text) | `#7A5D00` | `#FFBE04` | Gold on paper is 1.5:1. Same hue, darkened to 5.7:1. |
| `--edge` | `#858479` | `#476888` | Borders of things you click need 3:1. |

**Fixed when the toggle went in, still true:** `de-home` had **no base `.pill` rule** — it was dropped when
the page was split off `d-home`, so every Donate button on the published home page had been
rendering as a bare link. Restored from `d-home`, with `color:#070F1A` tokenized as `--on-gold`.

**Footage on `de-home`.** The page plays `{{VIDEO_ARRIVAL}}`: the warm clip
(`A_warm_and_cheerful_scene_of.mp4`) with the shot of a big eagle sign and the hallway shot cut
out, 6.4 s of the original 10. The committee pointed out Hendricks has no such sign and does not
look like that inside. `cut_clips.py` holds the frame ranges and why. The uncut clip is still
`{{VIDEO_WARM}}`, which only the frozen `e-home` uses. The mid-page frame on `de-home` is now a
real photograph (`{{SHIRT26}}`, last year's shirts, from the 2026 Walkathon photos), not footage.
`d-home` still carries `{{VIDEO_REEL}}` because the A-E artifacts are frozen as the record of
the vote.

Prefix with `https://claude.ai/code/artifact/`. Keep each page's favicon stable across
redeploys — the seven above, plus the frozen record of the vote: A 🏛️, B ✏️, C 📣, D 🎞️,
E 🏫, hub 🏫, video explainer 🎬, split reading B 🌗.

The `assets` capability is **not available** on this account (only `artifact`, `downloads`,
`mcp`, `self`), so video cannot be hosted beside a page — embedding is the only route.

## The five directions

All five use one palette and the same two pages. They differ in layout, typography and
intended audience, so the board is choosing a **voice**, not an identity.

| | Character | Aimed at | Display / body type |
|---|---|---|---|
| A Standing Strong | restrained, editorial | business sponsors, larger gifts | Newsreader / Archivo |
| B Schoolyard | warm, rounded | parents, sign-ups | Caprasimo / Assistant |
| C Momentum | loud, urgent | Walkathon turnout | Anton / Barlow + Barlow Condensed |
| D Reel | cinematic, film-led | anyone who scrolls | Bricolage Grotesque / Manrope |
| E Foundation | institutional, warm | the closest analog to obama.org | Figtree / Source Serif 4 + Archivo Narrow |

Each direction structures the sponsorship matrix differently on purpose — A a comparison
table, B choose-your-level cards, C full-width slabs, D hairline rows, E editorial rows. All
five carry the same nine benefits as real text.

## Palette rules

Sampled from the organization's own logo and printed flyer. **No colour comes from the
inspiration sites** — they informed layout and typography only.

| Role | Hex |
|---|---|
| Navy (logo, authoritative) | `#003E7E` |
| Red as ink and as a surface | `#C71014` |
| Red, bright — display sizes and decoration only | `#EE2A24` |
| Gold (from their flyer) | `#FFBE04` |
| Pale blues | `#DBE3EE`, `#A3B9D5` |

Two rules that are easy to break:

**The two reds.** `#EE2A24` gives only 4.21:1 on white — fine for large headlines and
decoration, **failing for body text and button labels**. Use `#C71014` (5.98:1) wherever red
carries small text or sits behind white text. Red on navy is 2.51:1 and is never used. Gold on
white is 1.66:1 — gold only ever appears on navy, on the ink strip, or as a fill behind dark
text.

**Surface tokens vs ink tokens.** Where navy or red is used both as a background *and* as text,
a single token cannot flip for a dark ground — a lightened navy would wreck every navy slab.
C, D and E therefore split them: `--navy` / `--red` stay fixed for surfaces, `--navy-ink` /
`--red-ink` lighten for text on a dark ground. Don't collapse them. On the live `de-*` pages
the two halves resolve to the same value on paper and only diverge over a photograph, which is
the whole point of keeping them apart.

`#0A085E` appears in the old site's CSS but is a WordPress theme setting, not part of the mark.
Do not use it.

## Theming

Every page defines the complete light palette on bare `:root`, redefines **only tokens** under
`@media (prefers-color-scheme: dark)` guarded as `:root:not([data-theme="light"])`, and again
under `:root[data-theme="dark"]`. Never declare a colour whose only definition sits inside a
media or `[data-theme]` block — the default "system" state stamps no attribute, and such a
colour never applies.

**The `de-*` pages are the exception and ignore the theme entirely.** They carry one
palette, light, on bare `:root`, with no `prefers-color-scheme` block, no `[data-theme]`
block and no switch. That is a decision, not an omission — see the section above. The rule
that keeps the photography dark needs *two* things, not one:

```css
.act1,.frame,.close,.filmcap,.past figure,.topnav.over-hero{
  --ink:#EDF2F8; ...        /* retone the tokens */
  color:var(--ink);          /* AND set a real colour */
}
```

Retoning `--ink` alone is not enough and the failure is easy to miss — the reason is in the
section above. That selector list is the live one; older copies of this file quoted
`.perk .sq` and `.pep figcaption`, which exist only in the frozen `de-partners-light` and
`e-home` and are not part of the partials.

The paragraph above this one still governs the **frozen A–E artifacts**, `index.html` and
`video-hero.html`: they do not use the partials, they keep their `prefers-color-scheme` and
`[data-theme]` blocks, and they must not be touched.

## Motion and video

The default is a still photograph scaled and drifted in CSS — **zero extra bytes**, and it
works with the assets that exist. Real footage layers over it via a progressive-enhancement
script: a `<video>` is injected only into `.media[data-film]` containers, and **only** when
JS runs, motion is allowed, and the browser is not reporting `saveData`. Any failure keeps
the photograph.

**760px now chooses a file; it does not gate on/off.** It used to skip footage entirely
below 760px, so every phone got the still — which reads as the video being broken, because
it starts playing the moment you switch a phone to desktop mode. The loader now takes
`data-video-sm` under 760px and `data-video` above it. The small copies are 960x540 at
~750 KB against 1280x720 at ~2.5 MB. A page offering no `data-video-sm` resolves it to an
empty string and skips, which is exactly the old behavior — so the frozen `c-home`,
`d-home` and `e-home` are untouched, and a new page opts in by adding the attribute. All videos are
`muted`, `loop`, `playsinline`, `aria-hidden`, and share one blob URL so extra frames cost
nothing. Every page with motion has a visible on/off control that starts paused under
`prefers-reduced-motion`.

**The three clips in `docs/videos/` are AI-generated** — embedded C2PA credentials read
"Created by Google Generative AI", `digitalSourceType: trainedAlgorithmicMedia`, plus a SynthID
watermark, model Veo. Verifiable by anyone and not removable. Using them on a donor-facing
charity page is a board decision, flagged in `docs/site-content-brief.md` §14. They are in the
mockups so the board can judge the mechanic.

## Content rules

**Nothing is invented.** Every price, name, date and sponsor traces to the live site or the
2025–26 partner flyer; `docs/site-content-brief.md` records each fact and its source. Where a
figure does not exist — total raised to date, for instance — the space is **visibly marked as
needing a real figure** rather than filled with something plausible. Preserve that. American
English throughout.

The 2027 Walkathon is **Saturday, February 20, 2027** — confirmed by the board in the
2026-10-05 feedback round. The sponsorship chart's "21st" was the error; the "to confirm"
marker is gone from `de-walkathon`.

**Cash and checks are not encouraged anywhere (2026-10-05).** The school district is strict
about how fundraising is collected, so every page points to Zeffy and nothing to PayPal,
checks, or the envelope sent home. The Friends of Hendricks is described as "a volunteer
group of parents" — teachers are not members — and the site never says it funds faculty
positions or staffing, which is against DCPS policy. The board likes the Oxford comma.

**One bolding rule on `de-partners` (2026-08-28).** `class="q"` on a benefit `<li>` means
*this is what changes with the level* — it bumps the weight to 600, lifts the colour to
`--ink` and turns the bullet gold. The three things every level gets, which the page's own
lede names, stay plain and close every list in the same order: yard sign at both entrances,
name on the Walkathon banner, name or logo on this website. Emphasized items come first.
The counts are 6/4/4/4/2 from $5,000 down. Before this, "Booth at the Walkathon" was plain
in the four tiers that get it even though it is a level benefit, and the bold items were
scattered through the list, so the highlight followed no rule a reader could see. `.q` means
something different in the frozen directions — an arrow bullet in A, weight 700 in C — so
don't carry an assumption across.

**The sponsor names are now settled — 48 of 49.** The 37 logo images were downloaded from the
live site and read; every business name is printed inside its own mark, so nothing was guessed.
`mockups/.sponsor-names.json` is the mapping. Several file names actively mislead and the brief
had them wrong: `dapazo` is **Dopazo Orthodontics**, `UPS-web` is **Heyday!** (not the UPS
Store, which is a separate sponsor), `PL-1` is **P&L Automotive**, `CP-Web` is **Coach Polster's
Summer Camp**, `AJWeb` is **Allison James Estates & Homes Elite**, `PLR` is **Players Locker
Room**.

The one still open is the Legacy Circle's sixth place, which the live site fills with
`white-block.jpg` — **a pure white 600×600 image, one distinct colour**. It is either a sponsor
whose logo never arrived or page filler. Do not guess.

**As of the 2026-08-25 feedback round it is no longer flagged on the page.** The board asked
for the explanatory paragraph and its red "one name to confirm" marker to come off
`de-sponsors`, and asked that the count read **48 everywhere** so no page claims more partners
than it shows. Four places changed: the `de-sponsors` and `de-home` sponsor headlines, the
`de-home` stat strip, and the `de-partners` "Already in" headline — plus the new home hero
copy, which the board wrote as forty-eight. The 49th place is still an open question; it now
lives here rather than on the site.

## Reference docs (`docs/`, git-ignored)

`site-content-brief.md` is the important one — every fact from all 11 pages of the live site,
the sponsorship matrix transcribed out of a PNG, the board roster, the five program inboxes,
the asset inventory, and the inspiration-site teardown. Read it instead of re-scraping.
Alongside it: `design-directions.md` (the five directions and their trade-offs),
`hosting-and-decisions.md` (parked hosting/forms questions), `web-inspo.md` (the original
brief), `inspiration-sites/` (~98 MB of saved pages — the only readable copy of
surfers-against-sewage, which 403s automated fetches), `photos/` and `videos/`.

`docs/` is entirely git-ignored, so **the reference docs and original media exist only on this
machine.** Nothing in `docs/` should be relied on by anyone cloning the repository.

## Environment constraints

No ffmpeg, ffprobe, OpenCV, imageio or PyAV. **But GStreamer is installed and can do
both** — `gst-launch-1.0` has `qtdemux`, `avdec_h264`, `videoscale`, `x264enc` and
`mp4mux`, which is a complete transcoding pipeline, plus `jpegenc` for pulling frames out
to look at. `mockups/encode_mobile.py` is the working example. Two things it gets right that
are easy to get wrong: `mp4mux faststart=true`, without which the moov atom lands after the
media data and the browser must download the whole file before it can play; and even pixel
dimensions, since x264 wants them for 4:2:0 chroma — asking for 854 wide silently produced
853. MP4 metadata can also be read by parsing atoms directly. Pillow is available; always run
`ImageOps.exif_transpose()` before processing, since several source photos carry rotation flags
and will otherwise come out sideways.

**Pages can be rendered (found 2026-10-07).** Firefox is a snap, and it hangs or reports
"Could not find profile folder" when given a profile under `/tmp`, which it cannot reach. A
profile inside its own snap folder works:

```bash
P=$HOME/snap/firefox/common/ff-shot; mkdir -p $P
firefox --headless --no-remote --profile $P --window-size=1440,900 --screenshot $P/out.png file://$PWD/site/index.html
```

It captures the window only, not the full page, and reserves ~12px for a scrollbar — so a
`--window-size=332,…` is a true 320px phone. For a long page, use a tall window and a temporary
copy with `.act1{min-height:900px}` and `.rv{opacity:1}` added, or the 100svh hero fills it.
Delete the copy afterwards; it must not land in `site/`. When touching a page, check: resolved token contrast against
WCAG AA in both themes, tag balance, no fixed width over ~340px outside an `overflow-x: auto`
container, every multi-column grid has a collapse breakpoint, `alt` on every `<img>`, and no
external request other than Google Fonts.
