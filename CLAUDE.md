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

`build.py` is a token substituter, nothing more. **Always edit `mockups/src/`, never
`mockups/*.html`** — the latter are generated and will be overwritten.

Every key in `mockups/.assets.json` becomes a token: `logo` → `{{LOGO}}`, `heroSm` →
`{{HERO_SM}}`, `rockWalk` → `{{ROCK_WALK}}` (camelCase splits on capitals). Videos in
`.videos.json` become `{{VIDEO_REEL}}`, `{{VIDEO_WARM}}`, `{{VIDEO_ENERGY}}`. A `{{VIDEO_*}}`
token with no matching asset is replaced with an empty string so pages still build and fall
back to a still photograph.

| File | Size | Tracked | Why |
|---|---|---|---|
| `mockups/.assets.json` | ~3.6 MB | **yes** | Images as data URIs. `docs/` is git-ignored, so this is the only committed copy of the logo and photography — the build cannot run without it. |
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

Prefix with `https://claude.ai/code/artifact/`. Keep each page's favicon stable across
redeploys: A 🏛️, B ✏️, C 📣, D 🎞️, E 🏫, hub 🏫, video explainer 🎬.

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
has no dark-mode block and paints every colour explicitly. That is a decision, not an omission.

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

Two live inconsistencies to leave flagged, not silently fixed: the sponsorship chart gives the
2027 Walkathon as both February 20th and 21st (the 20th is the Saturday), and 41 of 49 sponsors
are shown because eight are identifiable only by logo file name.

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
