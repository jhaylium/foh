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

Two outputs, from the same seven sources:

  build.py            mockups/*.html -- Artifact fragments. No <!doctype>, no
                      <head>: the publish step wraps them. Every image and clip
                      is inlined as a data URI, because a published Artifact may
                      not fetch from any host but Google Fonts.

  build.py --site     site/ -- an ordinary website. Real HTML documents, images
                      and video written out as files, cross-page links relative.
                      This is what a web server serves.

The two differ only in what the tokens resolve to, which is the whole reason the
sources go through tokens rather than carrying URLs of their own.
"""
import base64, json, pathlib, re, shutil, sys

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
for src in ([] if "--site" in sys.argv else sorted((root / "src").glob("*.html"))):
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
if built:
    print(f"{built} pages built")


# ---------------------------------------------------------------- site build

# Source stem -> the file a visitor actually lands on, and what search results
# and link previews show. Flat, and every link between them is relative, so the
# same output works at a domain root, in a /repo/ subpath on GitHub Pages, or
# anywhere else, with nothing to rewrite.
SITE_PAGES = {
    "de-home":      ("index.html", "The Friends of Hendricks",
                     "Parent volunteers raising money for Hendricks Avenue Elementary in "
                     "San Marco, Jacksonville. We buy what the county budget will not."),
    "de-donate":    ("donate.html", "Donate",
                     "Give to The Friends of Hendricks. A 501(c)(3) nonprofit -- every "
                     "dollar stays inside Hendricks Avenue Elementary."),
    "de-walkathon": ("walkathon.html", "The Walkathon",
                     "The 15th annual Walkathon, Saturday 20 February 2027. Students collect "
                     "pledges, then they walk."),
    "de-sponsors":  ("sponsors.html", "Our Sponsors",
                     "The local businesses backing Hendricks Avenue Elementary in 2025-26, "
                     "grouped by sponsorship level."),
    "de-partners":  ("become-a-sponsor.html", "Become a Sponsor",
                     "Five business sponsorship levels, from $250 to $5,000. Your logo on "
                     "600 t-shirts, the school marquee and both entrances."),
    "de-takepart":  ("take-part.html", "Take Part",
                     "Hugs from Henry, Rent the Spirit Rock and Spirit Nights -- three ways "
                     "to support the school that cost little or nothing."),
    "de-parents":   ("meet-the-parents.html", "Meet the Parents",
                     "The Friends of Hendricks is run entirely by parent volunteers. The "
                     "mission, the 2026-27 board, and how to reach us."),
}

EXT = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "video/mp4": "mp4"}

DOC = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<link rel="icon" href="img/logo.png">
<link rel="apple-touch-icon" href="img/logo.png">
{head}
</head>
<body>
{body}
</body>
</html>
"""


def _write_asset(uri, out, name):
    """Decode one data URI to a real file. Returns its path relative to the
    site root, which is what the token resolves to."""
    mime = uri.split(";", 1)[0].split(":", 1)[1]
    ext = EXT.get(mime)
    if ext is None:
        print(f"  !! {name}: unknown media type {mime}", file=sys.stderr)
        return None
    rel = f"{name}.{ext}"
    path = out / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(uri.split(",", 1)[1]))
    return rel


def build_site():
    out = root.parent / "site"
    if out.exists():
        shutil.rmtree(out)          # stale images from a renamed asset would linger
    out.mkdir(parents=True)

    site_tokens = {}
    written = 0
    for k, v in assets.items():
        rel = _write_asset(v, out, "img/" + re.sub(r"(?<!^)(?=[A-Z])", "-", k).lower())
        if rel:
            site_tokens[_tok(k)] = rel
            written += 1
    for name, uri in sponsors.items():
        rel = _write_asset(uri, out, f"img/sponsors/{name.lower()}")
        if rel:
            site_tokens["{{SPONSOR_" + name.upper() + "}}"] = rel
            written += 1
    for name, uri in videos.items():
        rel = _write_asset(uri, out, f"video/{name.lower()}")
        if rel:
            site_tokens["{{VIDEO_" + name.upper() + "}}"] = rel
            written += 1
    for src_name, (filename, _t, _d) in SITE_PAGES.items():
        site_tokens["{{URL_" + src_name.replace("de-", "").upper() + "}}"] = filename

    for src_name, (filename, title, desc) in SITE_PAGES.items():
        src = root / "src" / f"{src_name}.html"
        html = expand(src.read_text(), src.name)
        for k, v in site_tokens.items():
            html = html.replace(k, v)
        for m in set(re.findall(r"\{\{VIDEO_[A-Z_]+\}\}", html)):
            html = html.replace(m, "")
        leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
        if leftover:
            print(f"  !! {src_name}: unresolved {set(leftover)}", file=sys.stderr)

        # The sources are written head-first: <title>, the font links and the
        # pre-paint script, then one <style>. Everything through that closing
        # tag is head material; the rest is the document body.
        cut = html.find("</style>")
        if cut == -1:
            print(f"  !! {src_name}: no <style> to split on", file=sys.stderr)
            continue
        cut += len("</style>")
        page = DOC.format(desc=desc.replace('"', "&quot;"),
                          title=title.replace('"', "&quot;"),
                          head=html[:cut].strip(), body=html[cut:].strip())
        (out / filename).write_text(page)
        print(f"  {filename:24s} {len(page.encode())/1024:8.0f} KB")

    # .assets.json and .videos.json hold everything the mockups ever used,
    # including the directions that lost the vote. Ship only what the seven
    # pages actually reference -- otherwise the site carries dead weight, and in
    # the case of the unused clip, an AI-generated video nobody asked for.
    seen = "".join((out / f).read_text() for f, _t, _d in SITE_PAGES.values())
    pruned = dropped = 0
    for f in sorted(out.rglob("*")):
        if f.is_file() and f.suffix != ".html" and f.relative_to(out).as_posix() not in seen:
            dropped += f.stat().st_size
            f.unlink()
            pruned += 1
    for d in sorted(out.rglob("*"), reverse=True):        # tidy any dir left empty
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()

    # Pages is served through an Actions workflow, which does not run Jekyll --
    # but this costs nothing and removes the question.
    (out / ".nojekyll").write_text("")
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    if pruned:
        print(f"  pruned {pruned} unreferenced asset(s), {dropped/1024/1024:.1f} MB")
    print(f"{len(SITE_PAGES)} pages + {written - pruned} asset files -> site/  "
          f"({total/1024/1024:.1f} MB total)")


if "--site" in sys.argv:
    build_site()
