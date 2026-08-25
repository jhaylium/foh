#!/usr/bin/env python3
"""Inject data-URI assets into mockup sources. Run: python3 mockups/build.py

Images live in .assets.json (small, committed). Sponsor logos live in
.sponsors.json (committed). Videos live in .videos.json (large, NOT committed --
regenerate with encode_videos.py from docs/videos/). Any {{VIDEO_*}} token whose
asset is missing is replaced with an empty string, so the pages still build and
fall back to the drifting still photograph.

Two things beyond substitution, both added when the site grew from two pages to
seven:

  {{> name }}     pulls in src/_partials/name.html. The nav, footer, theme
                  tokens and scripts are identical on every page, and seven
                  copies of a nav is seven places to get a link wrong.

  {{URL_HOME}}    resolves from .links.json -- each page is its own Artifact with
                  its own URL, so cross-page links have to be absolute. A key
                  with no entry yet resolves to "#", which is what makes the
                  publish-then-rewire pass possible: build, publish, fill in
                  .links.json, rebuild, republish.

Partials are expanded before token substitution, so a partial can use tokens.
"""
import json, pathlib, re, sys

root = pathlib.Path(__file__).parent
partials_dir = root / "src" / "_partials"


def load(name, default=None):
    p = root / name
    return json.load(open(p)) if p.exists() else (default if default is not None else {})


assets = load(".assets.json")
sponsors = load(".sponsors.json")
videos = load(".videos.json")
links = load(".links.json")


# every key in .assets.json becomes {{KEY}} -- heroSm -> {{HERO_SM}}
def _tok(k):
    return "{{" + re.sub(r"(?<!^)(?=[A-Z])", "_", k).upper() + "}}"


tokens = {_tok(k): v for k, v in assets.items()}
for name, uri in sponsors.items():
    tokens["{{SPONSOR_" + name.upper() + "}}"] = uri
for name, uri in videos.items():
    tokens["{{VIDEO_" + name.upper() + "}}"] = uri
for name, url in links.items():
    if url:  # an empty entry is "not published yet" -> falls through to "#"
        tokens["{{URL_" + name.upper() + "}}"] = url

PARTIAL = re.compile(r"\{\{>\s*([a-z0-9_-]+)\s*\}\}")


def expand(html, src_name, depth=0):
    """Expand {{> partial }} recursively. Depth-capped so a partial that
    includes itself fails loudly instead of hanging the build."""
    if depth > 5:
        print(f"  !! {src_name}: partial nesting too deep", file=sys.stderr)
        return html

    def one(m):
        p = partials_dir / f"{m.group(1)}.html"
        if not p.exists():
            print(f"  !! {src_name}: no partial '{m.group(1)}'", file=sys.stderr)
            return ""
        return expand(p.read_text().rstrip("\n"), src_name, depth + 1)

    return PARTIAL.sub(one, html)


built = 0
for src in sorted((root / "src").glob("*.html")):
    html = expand(src.read_text(), src.name)
    for k, v in tokens.items():
        html = html.replace(k, v)
    # drop any video token we have no asset for -> graceful still-photo fallback
    missing = set(re.findall(r"\{\{VIDEO_[A-Z_]+\}\}", html))
    for m in missing:
        html = html.replace(m, "")
    # a page URL we have not published yet -> inert but valid link
    unlinked = set(re.findall(r"\{\{URL_[A-Z_]+\}\}", html))
    for m in unlinked:
        html = html.replace(m, "#")
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        print(f"  !! {src.name}: unresolved {set(leftover)}", file=sys.stderr)
    out = root / src.name
    out.write_text(html)
    flags = []
    if missing:
        flags.append("video omitted")
    if unlinked:
        flags.append(f"{len(unlinked)} link(s) not yet published")
    flag = "  (" + ", ".join(flags) + ")" if flags else ""
    print(f"  {src.name:22s} -> {out.stat().st_size/1024:8.0f} KB{flag}")
    built += 1
print(f"{built} pages built")
