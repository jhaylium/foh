#!/usr/bin/env python3
"""Inject data-URI assets into mockup sources. Run: python3 mockups/build.py

Images live in .assets.json (small, committed). Videos live in .videos.json
(large, NOT committed -- regenerate with encode_videos.py from docs/videos/).
Any {{VIDEO_*}} token whose asset is missing is replaced with an empty string,
so the pages still build and fall back to the drifting still photograph.
"""
import json, pathlib, re, sys

root = pathlib.Path(__file__).parent
assets = json.load(open(root / ".assets.json"))
# every key in .assets.json becomes {{KEY}} — heroSm -> {{HERO_SM}}
import re as _re
def _tok(k):
    return "{{" + _re.sub(r"(?<!^)(?=[A-Z])", "_", k).upper() + "}}"
tokens = {_tok(k): v for k, v in assets.items()}

vpath = root / ".videos.json"
videos = json.load(open(vpath)) if vpath.exists() else {}
for name, uri in videos.items():
    tokens["{{VIDEO_" + name.upper() + "}}"] = uri

built = 0
for src in sorted((root / "src").glob("*.html")):
    html = src.read_text()
    for k, v in tokens.items():
        html = html.replace(k, v)
    # drop any video token we have no asset for -> graceful still-photo fallback
    missing = set(re.findall(r"\{\{VIDEO_[A-Z_]+\}\}", html))
    for m in missing:
        html = html.replace(m, "")
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        print(f"  !! {src.name}: unresolved {set(leftover)}", file=sys.stderr)
    out = root / src.name
    out.write_text(html)
    flag = "  (video omitted)" if missing else ""
    print(f"  {src.name:22s} -> {out.stat().st_size/1024:8.0f} KB{flag}")
    built += 1
print(f"{built} pages built")
