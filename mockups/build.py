#!/usr/bin/env python3
"""Inject data-URI assets into mockup sources. Run: python3 mockups/build.py"""
import json, pathlib, re, sys

root = pathlib.Path(__file__).parent
assets = json.load(open(root / ".assets.json"))
tokens = {"{{LOGO}}": assets["logo"], "{{HERO}}": assets["hero"], "{{HERO_SM}}": assets["heroSm"]}

built = 0
for src in sorted((root / "src").glob("*.html")):
    html = src.read_text()
    for k, v in tokens.items():
        html = html.replace(k, v)
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", html)
    if leftover:
        print(f"  !! {src.name}: unresolved {set(leftover)}", file=sys.stderr)
    out = root / src.name
    out.write_text(html)
    print(f"  {src.name:22s} -> {out.stat().st_size/1024:7.0f} KB")
    built += 1
print(f"{built} pages built")
