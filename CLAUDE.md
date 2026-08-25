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
python3 mockups/build.py          # mockups/src/*.html -> mockups/*.html
python3 mockups/encode_videos.py  # regenerate mockups/.videos.json from docs/videos/
```

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

**`--photo` is declared per page, not in `tokens.html`.** It holds the 400 KB hero photograph,
and a page with no `.media` backdrop should not carry it — `de-sponsors` and `de-partners` do
not. The five that do declare `:root{--photo:url("{{HERO}}")}` in their own style block, right
after `{{> base }}`. If you add a `.media .layer` to a page, add that declaration too or the
backdrop comes up empty.

Every key in `mockups/.assets.json` becomes a token: `logo` → `{{LOGO}}`, `heroSm` →
`{{HERO_SM}}`, `rockWalk` → `{{ROCK_WALK}}` (camelCase splits on capitals). Videos in
`.videos.json` become `{{VIDEO_REEL}}`, `{{VIDEO_WARM}}`, `{{VIDEO_ENERGY}}`. A `{{VIDEO_*}}`
token with no matching asset is replaced with an empty string so pages still build and fall
back to a still photograph.

| File | Size | Tracked | Why |
|---|---|---|---|
| `mockups/.assets.json` | ~3.6 MB | **yes** | Images as data URIs. `docs/` is git-ignored, so this is the only committed copy of the logo and photography — the build cannot run without it. |
| `mockups/.sponsors.json` | ~790 KB | **yes** | The 37 sponsor logos, downscaled to 400px, as data URIs — `{{SPONSOR_DOPAZO}}` and so on. Same reasoning as `.assets.json`: `docs/` is git-ignored, so this is the only committed copy. |
| `mockups/.sponsor-names.json` | ~4 KB | **yes** | Which logo belongs to which business, at which level. Read off the artwork, not guessed. |
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
world across both pages, with a light-mode switch added (below). `de-partners-light`
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
`scroll-margin-top: calc(var(--nav-h) + 14px)` so in-page links don't land underneath it.
D's persistent bottom donate bar is gone; the ask now rides in the top bar instead.

**Light mode on the `de-*` pages.** D is still a dark page by design, so **dark is the
default in every theme** and the only way to light is the `Light mode` button in the top bar.
The switch adds `.lite` to the root element and remembers the choice in `localStorage` under
`foh-theme`, shared by both pages. Three things about it are easy to break:

- **It is a class, not `data-theme`.** The Artifact host stamps `data-theme` on the root
  itself from the viewer's Claude setting, so a `[data-theme="light"]` rule would drag the
  page into light without anyone asking for it. `:root.lite` is ours alone.
- **`color-scheme` is set on `body`, not `:root`.** The host writes `style.colorScheme`
  inline on the root, and an inline style beats a stylesheet. `body` is untouched by the host,
  so declaring it there wins for everything below it.
- **Photography stays dark in both modes.** A rule scoping the dark tokens to
  `.act1,.frame,.close,.topnav.over-hero` (home) and `.act1,.perk .sq,.pep figcaption,
  .topnav.over-hero` (partners) keeps the hero, the mid-page frame, the closing shot, the four
  benefit squares and the pep-rally caption reading the same either way. Those overrides are
  *exactly* the dark `:root` values, which is what leaves dark mode untouched.

Light mode needed two token splits beyond the ones listed under Palette rules:

| Token | Dark | Light | Why |
|---|---|---|---|
| `--gold` (fill) | `#FFBE04` | `#FFBE04` | Gold behind dark text — 11.6:1. Never flips. |
| `--gold-ink` (text) | `#FFBE04` | `#7A5D00` | Gold on paper is 1.5:1. Same hue, darkened to 5.7:1. |
| `--edge` | `#1B2B3F` | `#858479` | Borders of things you click need 3:1; `--line` is a hairline at 1.4:1. |
| `--bar` | `rgba(7,15,26,.93)` | `rgba(246,246,244,.93)` | The top bar once it has left the film. |

The rest of the light palette: `--ground #F6F6F4`, `--raise #EFEEE7`, `--sink #EAE9E1`,
`--ink #0B2340`, `--muted #42536B`, `--faint #54637A`, `--navy-ink`/`--red-ink` back to their
`#003E7E`/`#C71014` surface values, `--line #D6D5CC`, `--line-soft #E4E3DA`, and on the
partner page `--field #FFFFFF` for the application form. Every resolved pair passes AA;
the worst is `--faint` on `--sink` at 5.0:1.

**Fixed while adding the toggle:** `de-home` had **no base `.pill` rule** — it was dropped when
the page was split off `d-home`, so every Donate button on the published home page had been
rendering as a bare link. Restored from `d-home`, with `color:#070F1A` tokenized as `--on-gold`.

**Footage on `de-home`.** The page now embeds `{{VIDEO_WARM}}` (`A_warm_and_cheerful_scene_of.mp4`),
not the cinematic reel D shipped with. D's other trait — a dark page in every theme — is unchanged;
only the clip behind it is warmer. `d-home` still carries `{{VIDEO_REEL}}` because the A-E artifacts
are frozen as the record of the vote.

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
a single token cannot flip for dark mode — a lightened navy would wreck every navy slab. C, D
and E therefore split them: `--navy` / `--red` stay fixed for surfaces, `--navy-ink` /
`--red-ink` lighten in dark mode for text. Don't collapse them.

`#0A085E` appears in the old site's CSS but is a WordPress theme setting, not part of the mark.
Do not use it.

## Theming

Every page defines the complete light palette on bare `:root`, redefines **only tokens** under
`@media (prefers-color-scheme: dark)` guarded as `:root:not([data-theme="light"])`, and again
under `:root[data-theme="dark"]`. Never declare a colour whose only definition sits inside a
media or `[data-theme]` block — the default "system" state stamps no attribute, and such a
colour never applies.

**Direction D is deliberately single-theme dark** in every theme, the way a cinema is dark. It
paints every colour explicitly. That is a decision, not an omission. Light mode is opt-in only,
via the button in the top bar.

**Anything sitting on a photograph stays dark in both modes**, and the rule that does it needs
*two* things, not one:

```css
.act1,.frame,.close,.filmcap,.perk .sq,.past figure,.topnav.over-hero{
  --ink:#EDF2F8; ...        /* retone the tokens */
  color:var(--ink);          /* AND set a real colour */
}
```

Retoning `--ink` alone is not enough and the failure is easy to miss. A custom property only
affects declarations that *use* it inside that subtree. Headings carry no `color` of their own
— they inherit the computed colour from `<body>`, which already resolved `var(--ink)` against
`:root`. In light mode that turned every headline over a photograph dark navy while the body
copy beside it stayed white. Setting `color` on the region resolves `--ink` at that element, so
the whole subtree inherits it.

## Motion and video

The default is a still photograph scaled and drifted in CSS — **zero extra bytes**, and it
works with the assets that exist. Real footage layers over it via a progressive-enhancement
script on `c-home`, `d-home` and `e-home`: a `<video>` is injected only into `.media[data-film]`
containers, and **only** when JS runs, motion is allowed, the browser is not reporting
`saveData`, and the viewport is ≥760px. Any failure keeps the photograph. All videos are
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

One live inconsistency to leave flagged, not silently fixed: the sponsorship chart gives the
2027 Walkathon as both February 20th and 21st (the 20th is the Saturday).

**The sponsor names are now settled — 48 of 49.** The 37 logo images were downloaded from the
live site and read; every business name is printed inside its own mark, so nothing was guessed.
`mockups/.sponsor-names.json` is the mapping. Several file names actively mislead and the brief
had them wrong: `dapazo` is **Dopazo Orthodontics**, `UPS-web` is **Heyday!** (not the UPS
Store, which is a separate sponsor), `PL-1` is **P&L Automotive**, `CP-Web` is **Coach Polster's
Summer Camp**, `AJWeb` is **Allison James Estates & Homes Elite**, `PLR` is **Players Locker
Room**.

The one still open is the Legacy Circle's sixth place, which the live site fills with
`white-block.jpg` — **a pure white 600×600 image, one distinct colour**. It is either a sponsor
whose logo never arrived or page filler. Do not guess: it is marked on the sponsors page as a
name to confirm, and the count stays at 49.

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

No ffmpeg, OpenCV, imageio or PyAV — **video frames cannot be decoded or transcoded here.**
MP4 metadata can be read by parsing atoms directly. Pillow is available; always run
`ImageOps.exif_transpose()` before processing, since several source photos carry rotation flags
and will otherwise come out sideways.

Firefox exists but headless screenshotting hangs on first-run profile setup, so layout has been
verified statically, not rendered. When touching a page, check: resolved token contrast against
WCAG AA in both themes, tag balance, no fixed width over ~340px outside an `overflow-x: auto`
container, every multi-column grid has a collapse breakpoint, `alt` on every `<img>`, and no
external request other than Google Fonts.
