#!/usr/bin/env python3
"""Trim the blank margin off every sponsor logo, and record its shape.

Run: python3 mockups/trim_sponsors.py

The logos arrive as the businesses sent them, and most carry a margin of plain
background baked into the file -- some a few pixels, some half the image. Put in
identical boxes, a logo with a wide margin looks small and one cropped to its
edges looks large, which is what the committee saw on the sponsor wall. This
cuts every logo to its own edges, plus a sliver, so the page decides how big
each one looks rather than the file.

It also writes "ar" (width / height, after trimming) into .sponsor-names.json.
build.py uses that to size each logo by area rather than by "fill the box", so
a long wordmark and a round badge carry about the same visual weight.

Running it twice changes nothing: a trimmed logo has no margin left to cut.
To add next year's sponsors: put the downscaled JPEG in .sponsors.json and the
name, tier and website in .sponsor-names.json, then run this and build.py.
"""
import base64, io, json, pathlib

from PIL import Image, ImageChops, ImageOps

root = pathlib.Path(__file__).parent
logos_path = root / ".sponsors.json"
names_path = root / ".sponsor-names.json"

THRESHOLD = 24     # how far a pixel must differ from the background to count as logo
PAD = 0.04         # margin added back, as a fraction of the longer side
QUALITY = 85
MIN_CUT = 0.02   # ignore a crop that removes less than this much of either side


def background(im):
    """The colour of the four corners, if they agree; else white."""
    w, h = im.size
    corners = [im.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    first = corners[0]
    if all(max(abs(a - b) for a, b in zip(c, first)) < THRESHOLD for c in corners):
        return first
    return (255, 255, 255)


def trim(im):
    im = ImageOps.exif_transpose(im).convert("RGB")
    bg = background(im)
    diff = ImageChops.difference(im, Image.new("RGB", im.size, bg)).convert("L")
    box = diff.point(lambda v: 255 if v > THRESHOLD else 0).getbbox()
    if not box:
        return im, False
    l, t, r, b = box
    pad = round(max(r - l, b - t) * PAD)
    l, t = max(0, l - pad), max(0, t - pad)
    r, b = min(im.width, r + pad), min(im.height, b + pad)
    # JPEG noise along an edge can read as a pixel or two of logo. A crop that
    # small is noise, not margin -- and skipping it is what makes a second run
    # leave the file alone instead of shaving it again.
    if (r - l) > im.width * (1 - MIN_CUT) and (b - t) > im.height * (1 - MIN_CUT):
        return im, False
    return im.crop((l, t, r, b)), True


logos = json.loads(logos_path.read_text())
names = json.loads(names_path.read_text())
by_key = {n["key"]: n for n in names}

changed = 0
for key, uri in logos.items():
    head, data = uri.split(",", 1)
    before = Image.open(io.BytesIO(base64.b64decode(data)))
    size_before = before.size
    after, cut = trim(before)
    if cut:
        buf = io.BytesIO()
        after.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        logos[key] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
        changed += 1
    entry = by_key.get(key.upper())
    if entry is None:
        print(f"  !! {key}: in .sponsors.json but not in .sponsor-names.json")
        continue
    entry["ar"] = round(after.width / after.height, 3)
    note = f"{size_before[0]}x{size_before[1]} -> {after.width}x{after.height}" if cut else "already tight"
    print(f"  {key:14s} {note:22s} ar {entry['ar']}")

logos_path.write_text(json.dumps(logos))
names_path.write_text(json.dumps(names, indent=1))
print(f"{changed} of {len(logos)} logos trimmed")
