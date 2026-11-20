"""The parts of the site that change every year, read from content/*.json.

Those files are what the board edits through Pages CMS (see .pages.yml at the
repository root), so everything here assumes a person typed the values into a
form: it checks them and stops the build with a plain message naming the file
and the entry, rather than publishing a page with a hole in it. A failed build
on GitHub leaves the last good site up.

build.py and levels_pdf.py both call tokens(); the only thing that differs
between the mockups and site/ is where an image ends up, which the caller
decides through place(data, mime, name) -> the string to put in src="".
"""
import datetime, html, io, json, math, pathlib, re

from PIL import Image, ImageChops, ImageOps

repo = pathlib.Path(__file__).resolve().parent.parent
content_dir = repo / "content"


class ContentError(SystemExit):
    pass


def fail(file, msg):
    raise ContentError(f"content/{file}: {msg}")


def read(name):
    try:
        return json.loads((content_dir / name).read_text())
    except FileNotFoundError:
        fail(name, "file is missing")
    except json.JSONDecodeError as e:
        fail(name, f"not valid JSON ({e})")


# ---------------------------------------------------------------- small helpers

esc = html.escape


def text(s):
    """Escape typed text, then turn a hyphen between two digits into an en dash
    -- "3-7pm" reads 3&ndash;7pm, the way the pages were written by hand."""
    return re.sub(r"(?<=\d)-(?=\d)", "&ndash;", esc(s or "", quote=False))


def day(file, where, value):
    if not value:
        fail(file, f"{where}: date is empty")
    try:
        return datetime.date.fromisoformat(str(value)[:10])
    except ValueError:
        fail(file, f"{where}: '{value}' is not a date")


def school_year(file, value):
    """'2026-27' or '2026-2027' -> (2026, 2027). Anything else stops the build."""
    m = re.fullmatch(r"\s*(\d{4})\s*[-–/]\s*(\d{2}|\d{4})\s*", str(value or ""))
    if not m:
        fail(file, f"school year '{value}' should look like 2026-27")
    a, b = int(m.group(1)), int(m.group(2))
    b = b if b > 99 else a // 100 * 100 + b
    if b != a + 1:
        fail(file, f"school year '{value}' should be two years in a row, like 2026-27")
    return a, b


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen").split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n):
    """48 -> 'forty-eight'. Good to 999, which is more sponsors than a school gets."""
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    rest = n % 100
    return ONES[n // 100] + " hundred" + (" " + words(rest) if rest else "")


# ---------------------------------------------------------------- images

SPONSOR_MAX = 400      # logos are shown at most 420px wide; this is what they shipped at
FLYER_MAX = 1200
PHOTO_MAX = 1600       # the widest photograph on the site today is 1500
MAX_BYTES = 600_000    # a phone photo straight off the camera is several MB
THRESHOLD = 24         # how far a pixel must differ from the background to count as logo
PAD = 0.04             # margin added back, as a fraction of the longer side
MIN_CUT = 0.02         # ignore a crop that removes less than this much of either side


def media_file(file, where, value):
    """A path Pages CMS wrote ('/content/media/x.jpg') -> the file in the repo."""
    if not value:
        fail(file, f"{where}: no image chosen")
    # The docs show a leading-slash public path; accept one relative to the
    # media folder too, rather than find out which on a live edit.
    rel = str(value).lstrip("/")
    for p in ((repo / rel).resolve(), (content_dir / "media" / rel).resolve()):
        if repo in p.parents and p.is_file():
            return p
    fail(file, f"{where}: image '{value}' is not in the repository")


def _flatten(im):
    """Transparent PNGs go onto white -- a plain convert('RGB') turns them black."""
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        return bg
    return im.convert("RGB")


def _background(im):
    """The colour of the four corners, if they agree; else white."""
    w, h = im.size
    corners = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    first = corners[0]
    if all(max(abs(a - b) for a, b in zip(c, first)) < THRESHOLD for c in corners):
        return first
    return (255, 255, 255)


def _trim(im):
    """Cut a logo to its own edges plus a sliver. Logos arrive with margins of
    every size baked in, and in identical boxes a wide margin reads as a small
    sponsor. A cut under MIN_CUT is JPEG noise, and skipping it is what makes
    an already-trimmed logo come through untouched."""
    diff = ImageChops.difference(im, Image.new("RGB", im.size, _background(im))).convert("L")
    box = diff.point(lambda v: 255 if v > THRESHOLD else 0).getbbox()
    if not box:
        return im, False
    l, t, r, b = box
    pad = round(max(r - l, b - t) * PAD)
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    if (r - l) > im.width * (1 - MIN_CUT) and (b - t) > im.height * (1 - MIN_CUT):
        return im, False
    return im.crop((l, t, r, b)), True


def logo(file, where, value):
    """-> (jpeg bytes, width / height). A logo already trimmed and small enough
    -- every one migrated from the old .sponsors.json -- passes through byte for
    byte; a fresh upload is trimmed, scaled to SPONSOR_MAX and saved as JPEG."""
    p = media_file(file, where, value)
    raw = p.read_bytes()
    try:
        src = Image.open(io.BytesIO(raw))
        src.load()
    except Exception:
        fail(file, f"{where}: '{value}' is not an image the build can read")
    im, cut = _trim(_flatten(src))
    big = max(im.size) > SPONSOR_MAX
    if big:
        im.thumbnail((SPONSOR_MAX, SPONSOR_MAX), Image.LANCZOS)
    if cut or big or src.format != "JPEG":
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=85, optimize=True, progressive=True)
        raw = buf.getvalue()
    return raw, round(im.width / im.height, 3)


def photo(file, where, value, widest=FLYER_MAX, fmt="WEBP"):
    """-> (bytes, mime). Wider than `widest`, heavier than MAX_BYTES, or in a
    format browsers can't show, it is scaled and re-saved: WebP for the flyer,
    which keeps flat colour and lettering sharp, JPEG for photographs. A file
    already the right size and shape passes through byte for byte."""
    p = media_file(file, where, value)
    raw = p.read_bytes()
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:
        fail(file, f"{where}: '{value}' is not an image the build can read")
    mime = Image.MIME.get(im.format)
    if (im.width > widest or len(raw) > MAX_BYTES
            or mime not in ("image/jpeg", "image/png", "image/webp")):
        im = _flatten(im)                     # also turns a phone photo the right way up
        im.thumbnail((widest, widest * 3), Image.LANCZOS)
        buf = io.BytesIO()
        if fmt == "WEBP":
            im.save(buf, "WEBP", quality=90)
            return buf.getvalue(), "image/webp"
        im.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
        return buf.getvalue(), "image/jpeg"
    return raw, mime


# ---------------------------------------------------------------- sponsors

# The label the board picks in the editor -> the wall it lands on.
LEVELS = {
    "Visionary Partner": "visionary",
    "Legacy Circle": "legacy",
    "Investor Circle": "investors",
    "Builders Circle": "builders",
    "Friends Circle": "friends",
}

# Logos are sized by AREA, not by "fill the box". Filling the box makes a
# square badge as tall as the card and a long wordmark a thin stripe, so the
# eye reads the badge as the bigger sponsor. Giving each logo the same share of
# the card's area evens that out: a logo of shape ar fills sqrt(0.75 * AREA * ar)
# of the card's width (the card is 4:3), capped where it would hit the top and
# bottom or the sides.
AREA = 0.56


def logo_width(ar):
    w = math.sqrt(0.75 * AREA * ar)
    return min(w, 0.75 * ar, 0.94)  # 0.75*ar is where its height meets the card's


def sponsor_tokens(place):
    f = "sponsors.json"
    data = read(f)
    sponsors = data.get("sponsors") or []
    a, b = school_year(f, data.get("school_year"))
    walls = {tier: [] for tier in LEVELS.values()}
    visionary = None
    for i, s in enumerate(sponsors, 1):
        name = (s.get("name") or "").strip()
        where = f"sponsor {i} ({name or 'no name'})"
        if not name:
            fail(f, f"{where}: name is empty")
        tier = LEVELS.get(s.get("level"))
        if tier is None:
            fail(f, f"{where}: level '{s.get('level')}' is not one of {', '.join(LEVELS)}")
        n = esc(name)
        if tier == "friends":           # this level carries no logo -- a name card
            walls[tier].append(f"<span>{n}</span>")
            continue
        raw, ar = logo(f, where, s.get("logo"))
        stem = pathlib.Path(str(s["logo"])).stem.lower()
        src = place(raw, "image/jpeg", f"img/sponsors/{stem}")
        img = (f'<img src="{src}" alt="{n}" '
               f'style="width:{round(logo_width(ar) * 100, 1)}%" loading="lazy">')
        url = (s.get("website") or "").strip()
        card = (f'<a class="card" href="{esc(url)}" target="_blank" rel="noopener">{img}</a>'
                if url else f'<div class="card">{img}</div>')
        walls[tier].append(f'      <div class="slot">{card}<p class="nm">{n}</p></div>')
        if tier == "visionary" and visionary is None:
            visionary = (name, src)

    t = {"{{SPONSOR_WALL_" + tier.upper() + "}}": "\n".join(items)
         for tier, items in walls.items() if tier != "friends"}
    t["{{SPONSOR_NAMES_FRIENDS}}"] = "".join(walls["friends"])
    count = len(sponsors)
    t["{{SPONSOR_COUNT}}"] = str(count)
    t["{{SPONSOR_COUNT_WORDS}}"] = words(count)
    t["{{SPONSOR_COUNT_WORDS_CAP}}"] = words(count).capitalize()
    t["{{SPONSOR_YEAR}}"] = f"{a}&ndash;{b % 100:02d}"
    t["{{SPONSOR_YEAR_LONG}}"] = f"{a}&ndash;{b}"
    # The home page's lead card. "State Farm — Matt Carlucci, Agent" sets as
    # two lines, split at the dash. With no Visionary Partner the card is left
    # out and the "Take this next year" button stands alone.
    if visionary:
        name, src = visionary
        alt = esc(name).replace("—", "&mdash;")
        lines = "<br>".join(esc(p.strip()) for p in re.split(r"\s+[—–-]\s+", name, 1))
        t["{{SPONSOR_VISIONARY_LEAD}}"] = (
            '<div class="vis">\n'
            '        <div class="slot"><div class="card">\n'
            f'          <img src="{src}" alt="{alt}"></div></div>\n'
            '        <div><p class="tag">Visionary partner &middot; one only</p>\n'
            f'          <div class="disp" style="margin-top:8px">{lines}</div></div>\n'
            '      </div>')
    else:
        t["{{SPONSOR_VISIONARY_LEAD}}"] = ""
    return t


# ---------------------------------------------------------------- walkathon

FIRST_WALKATHON = 2013      # the 2027 Walkathon is the 15th


def walkathon_tokens():
    f = "walkathon.json"
    w = read(f)
    d = day(f, "Walkathon", w.get("date"))
    goal = w.get("goal")
    if not isinstance(goal, (int, float)) or goal <= 0:
        fail(f, f"goal '{goal}' should be a dollar amount")
    return {
        "{{WALK_YEAR}}": str(d.year),
        "{{WALK_WEEKDAY}}": d.strftime("%A"),                                 # Saturday
        "{{WALK_DATE}}": f"{d:%B} {d.day}, {d.year}",                         # February 20, 2027
        "{{WALK_DATE_FULL}}": f"{d:%A}, {d:%B} {d.day}, {d.year}",            # Saturday, February 20, 2027
        "{{WALK_DATE_SHORT}}": f"{d:%b} {d.day}",                             # Feb 20
        "{{WALK_DATE_TILE}}": f"{d:%a}, {d:%b} {d.day}, {d.year}",            # Sat, Feb 20, 2027
        "{{WALK_DATE_ORD}}": f"{d:%B} {ordinal(d.day)}",                      # February 20th
        "{{WALK_DATE_META}}": f"{d:%A} {d.day} {d:%B} {d.year}",              # Saturday 20 February 2027
        "{{WALK_MONTH_YEAR}}": f"{d:%B} {d.year}",                            # February 2027
        "{{WALK_EDITION}}": ordinal(d.year - FIRST_WALKATHON + 1),            # 15th
        "{{WALK_GOAL}}": f"${goal:,.0f}",                                     # $50,000
    }


# ---------------------------------------------------------------- birthday club

def henry_tokens():
    f = "birthday-club.json"
    h = read(f)
    a, b = school_year(f, h.get("school_year"))
    parts = []
    for i, p in enumerate(h.get("parties") or [], 1):
        d = day(f, f"party {i}", p.get("date"))
        note = (p.get("note") or "").strip()
        parts.append(f"{d:%b} {d.day}" + (f" ({text(note)})" if note else ""))
    if not parts:
        fail(f, "no party dates")
    return {"{{HENRY_YEAR}}": f"{a}&ndash;{b}",
            "{{HENRY_DATES}}": "\n          &middot; ".join(parts)}


# ---------------------------------------------------------------- spirit nights

def spirit_tokens(place):
    f = "spirit-nights.json"
    s = read(f)
    a, b = school_year(f, s.get("school_year"))
    rows = []
    for i, n in enumerate(s.get("nights") or [], 1):
        where = f"night {i}"
        d = day(f, where, n.get("date"))
        if not (n.get("restaurant") or "").strip():
            fail(f, f"{where}: restaurant is empty")
        bits = [text(n.get(k, "").strip()) for k in ("hours", "restaurant", "give_back", "extra")]
        rows.append(f"          <li><b>{d:%a} {d.day} {d:%b}</b>"
                    f"<span>{' &middot; '.join(x for x in bits if x)}</span></li>")
    raw, mime = photo(f, "flyer", s.get("flyer"))
    desc = (s.get("flyer_description") or "").strip()
    if not desc:
        fail(f, "flyer description is empty -- it is what a screen reader says instead of the picture")
    return {"{{SPIRIT_YEAR}}": f"{a}&ndash;{b}",
            "{{SPIRIT_NIGHTS}}": "\n".join(rows),
            "{{SPIRIT_FLYER}}": place(raw, mime, "img/spirit-night"),
            "{{SPIRIT_FLYER_ALT}}": esc(desc)}


# ---------------------------------------------------------------- board

def board_tokens():
    f = "board.json"
    b = read(f)
    y1, y2 = school_year(f, b.get("school_year"))
    officers = []
    for i, o in enumerate(b.get("officers") or [], 1):
        role, name = (o.get("role") or "").strip(), (o.get("name") or "").strip()
        if not (role and name):
            fail(f, f"officer {i}: needs both a role and a name")
        officers.append(f'      <div class="pp"><span>{esc(role)}</span><b>{esc(name)}</b></div>')
    directors = [esc(d.strip()) for d in (b.get("directors") or []) if d and d.strip()]
    return {"{{BOARD_YEAR}}": f"{y1}&ndash;{y2 % 100:02d}",
            "{{BOARD_OFFICERS}}": "\n".join(officers),
            "{{BOARD_DIRECTORS}}": " &middot; ".join(directors)}


def tokens(place):
    t = {}
    t.update(sponsor_tokens(place))
    t.update(walkathon_tokens())
    t.update(henry_tokens())
    t.update(spirit_tokens(place))
    t.update(board_tokens())
    return t


# ---------------------------------------------------------------- page text

# Every word on the seven pages, the menu, and the footer lives in
# content/pages/<page>.json, one object per section of the page. The page
# sources carry {{T:page.section.field}} where each one goes. What a field is
# follows from its name:
#
#   photo_N         an image path -> the file the page shows
#   photo_text_N    the photo's alt text      } go inside an attribute,
#   link_N          an outside link address   } so they are escaped as one
#   anything else   text, possibly with bold, italics, links and line breaks
#                   from a rich-text box -- see rich()
#
# Text is filled in before any other token, so a field may carry one
# ({{WALK_YEAR}} and friends) and it resolves like the rest of the page.

pages_dir = content_dir / "pages"
TEXT = re.compile(r"\{\{T:([a-z0-9-]+)\.([a-z0-9_]+)\.([a-z0-9_]+)\}\}")
_pages = {}


def page(name):
    if name not in _pages:
        _pages[name] = read(f"pages/{name}.json")
    return _pages[name]


# What a rich-text box may keep. Everything else is dropped and its words kept,
# so a paste from Word or a stray style can't change the page's design.
KEEP = {"strong", "em", "b", "i", "br", "a"}
TAG = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^<>]*)>")
HREF = re.compile(r'(href|target|rel)\s*=\s*"([^"]*)"')


def rich(value):
    v = str(value or "").strip()
    # An editor wraps text in <p>. The page already has its own <p> or <h2>
    # around the spot, so drop the outer one and turn any breaks between
    # paragraphs into line breaks.
    v = re.sub(r"^<p\b[^>]*>|</p>$", "", v).strip()
    v = re.sub(r"</p>\s*<p\b[^>]*>", "<br>", v)
    out, pos = [], 0
    for m in TAG.finditer(v):
        out.append(esc(html.unescape(v[pos:m.start()]), quote=False))
        pos = m.end()
        close, name = m.group(1), m.group(2).lower()
        if name not in KEEP:
            continue
        if name == "br":
            out.append("<br>")
        elif close:
            out.append(f"</{name}>")
        elif name == "a":
            attrs = "".join(f' {k}="{esc(html.unescape(x))}"' for k, x in HREF.findall(m.group(3)))
            out.append(f"<a{attrs}>")
        else:
            out.append(f"<{name}>")
    out.append(esc(html.unescape(v[pos:]), quote=False))
    return "".join(out)


def text_value(name, group, field):
    f = f"pages/{name}.json"
    g = page(name).get(group)
    if not isinstance(g, dict) or field not in g:
        fail(f, f"{group}.{field} is missing -- the page expects it")
    return g[field]


def fill_text(source, place):
    """Replace every {{T:...}} in a page. place() is the caller's, as above."""
    def one(m):
        name, group, field = m.groups()
        value = text_value(name, group, field)
        if field.startswith("photo_text_") or field.startswith("link_"):
            return esc(html.unescape(str(value or "").strip()))
        if field.startswith("photo_"):
            raw, mime = photo(f"pages/{name}.json", f"{group}.{field}", value,
                              widest=PHOTO_MAX, fmt="JPEG")
            stem = re.sub(r"[^a-z0-9-]+", "-", pathlib.Path(str(value)).stem.lower()).strip("-")
            return place(raw, mime, f"img/{stem}")
        return rich(value)
    return TEXT.sub(one, source)


def search_description(name):
    """Plain text for <meta name="description">; the caller escapes it."""
    v = page(name).get("page", {}).get("search_description_1", "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", str(v)))).strip()
