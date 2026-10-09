#!/usr/bin/env python3
"""Print the sponsorship levels as a one-page PDF chart.

Run: uv run --no-project --with weasyprint mockups/levels_pdf.py
     -> mockups/sponsor-levels.pdf

The committee asked for a version of the five levels a business can print, or
lay side by side -- the page lists each level's benefits under it, which is
right for reading and wrong for comparing. This turns the same benefits into a
chart: levels across the top, benefits down the side, and what each level gets
in the cell.

The levels are read out of src/de-partners.html, so the page stays the one
place they are written down. Change a benefit there, rerun this, rebuild.

Every benefit has to match a row in ROWS below. One that does not stops the
script with its text, rather than being left off the chart -- a benefit that
quietly vanishes from a printed sheet is worse than a script that refuses to
run. When the audited list of benefits arrives, expect to add rows here.

Prints with WeasyPrint, which renders HTML and CSS to PDF without a browser --
hence uv, which fetches it for the one run rather than making it a dependency
of the build. (Headless Brave, the only Chromium here, starts and never prints.)
Fonts come from Google Fonts, so it needs the network. build.py --site copies
the PDF into site/; the build itself never runs this.
"""
import html, json, pathlib, re, sys

root = pathlib.Path(__file__).parent
src = root / "src" / "de-partners.html"
out = root / "sponsor-levels.pdf"

# (row label, pattern, what goes in the cell). A cell of True prints a tick.
ROWS = [
    ("Naming rights to the Walkathon", r"Naming rights to the Walkathon", True),
    ("Speak at the pep rally", r"Speak at the pep rally", True),
    ("Booth at the Walkathon", r"Booth at the Walkathon", True),
    ("Days on the school marquee", r"School marquee\W+(\d+) days?", r"\1"),
    ("On the student t-shirts", r"(Large|Medium|Small) logo on student t-shirts", r"\1 logo"),
    ("On the student t-shirts", r"Name on student t-shirts", "Name"),
    ("Social media posts", r"(\d+) social media posts?", r"\1"),
    ("Yard sign at both entrances", r"Yard sign at both entrances", True),
    ("Name on the Walkathon banner", r"Name on the Walkathon banner", True),
    ("On this website", r"(Logo|Name) on this website", r"\1"),
]


def text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def read_levels():
    page = src.read_text()
    levels = []
    for block in re.findall(r'<div class="tier[^"]*">(.*?)</ul>', page, re.S):
        amount = text(re.search(r'class="amt">(.*?)<', block).group(1))
        name = text(re.search(r'class="nm">(.*?)<', block).group(1))
        only = re.search(r'class="only">(.*?)<', block)
        cells = {}
        for li in re.findall(r"<li[^>]*>(.*?)</li>", block, re.S):
            benefit = re.sub(r"\s+", " ", text(li))
            for label, pattern, value in ROWS:
                m = re.fullmatch(pattern, benefit)
                if m:
                    cells[label] = True if value is True else m.expand(value)
                    break
            else:
                sys.exit(f"!! {name}: no row in ROWS matches the benefit {benefit!r}\n"
                         f"   Add one to levels_pdf.py so it appears on the chart.")
        levels.append({"amount": amount, "name": name,
                       "only": text(only.group(1)) if only else "", "cells": cells})
    if len(levels) != 5:
        sys.exit(f"!! expected five levels in {src.name}, found {len(levels)}")
    return levels


def chart(levels):
    logo = json.loads((root / ".assets.json").read_text())["logo"]
    labels = list(dict.fromkeys(label for label, _, _ in ROWS))
    head = "".join(
        f'<th class="{"top" if i == 0 else ""}"><b>{html.escape(l["amount"])}</b>'
        f'<span>{html.escape(l["name"])}</span>'
        + (f'<em>{html.escape(l["only"])}</em>' if l["only"] else "") + "</th>"
        for i, l in enumerate(levels))
    body = []
    for label in labels:
        row = []
        for i, l in enumerate(levels):
            v = l["cells"].get(label)
            cell = ('<span class="tick" aria-label="Included">&#10003;</span>' if v is True
                    else html.escape(v) if v else '<span class="no">&mdash;</span>')
            row.append(f'<td class="{"top" if i == 0 else ""}">{cell}</td>')
        body.append(f'<tr><th scope="row">{html.escape(label)}</th>{"".join(row)}</tr>')
    walkathon = re.search(r"The 2027 Walkathon is\s*<strong[^>]*>(.*?)</strong>",
                          src.read_text(), re.S)
    date = text(walkathon.group(1)) if walkathon else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Business Partner Levels</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,800&family=Manrope:wght@400;500;600;700&display=swap">
<style>
@page{{size:letter landscape;margin:0.45in 0.5in}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Manrope,Arial,sans-serif;color:#0B2340;font-size:10.5pt;
  font-variant-ligatures:no-common-ligatures;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
header{{display:flex;align-items:center;gap:18px;border-bottom:2px solid #003E7E;padding-bottom:12px}}
header img{{height:74px}}
header h1{{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:23pt;margin:0;
  letter-spacing:-.02em;line-height:1}}
header p{{margin:5px 0 0;color:#42536B}}
header .eyebrow{{margin:0 0 5px;font-size:8pt;font-weight:700;letter-spacing:.2em;
  text-transform:uppercase;color:#C71014}}
table{{width:100%;border-collapse:collapse;margin-top:14px;table-layout:fixed}}
col.lbl{{width:26%}}
thead th{{text-align:center;padding:10px 6px 9px;vertical-align:bottom;border-bottom:2px solid #0B2340}}
thead th b{{display:block;font-family:"Bricolage Grotesque",sans-serif;font-weight:400;
  font-size:22pt;letter-spacing:-.03em;line-height:1}}
thead th span{{display:block;margin-top:5px;font-size:7.5pt;font-weight:700;letter-spacing:.16em;
  text-transform:uppercase;color:#42536B}}
thead th em{{display:block;margin-top:3px;font-style:normal;font-size:7.5pt;color:#7A5D00;font-weight:700}}
.top{{background:#FFF6DA}}
thead th.top{{border-top:3px solid #FFBE04}}
tbody th{{text-align:left;font-weight:600;padding:8px 10px 8px 0}}
tbody td{{text-align:center;padding:8px 6px;font-weight:600}}
tbody tr{{border-bottom:1px solid #D6D5CC}}
.tick{{color:#003E7E;font-size:13pt;line-height:1}}
.no{{color:#A8A79C}}
.notes{{display:flex;gap:28px;margin-top:16px;font-size:9.5pt;color:#42536B}}
.notes div{{flex:1}}
.notes b{{color:#0B2340}}
footer{{margin-top:14px;padding-top:10px;border-top:1px solid #D6D5CC;display:flex;
  justify-content:space-between;gap:20px;font-size:9pt;color:#42536B}}
footer b{{color:#0B2340}}
</style></head><body>
<header><img src="{logo}" alt="The Friends of Hendricks">
  <div><p class="eyebrow">Business Partner Program</p>
    <h1>Five ways to sponsor the Walkathon</h1>
    <p>Hendricks Avenue Elementary &middot; 650+ students and their families
      {f"&middot; The 2027 Walkathon is {html.escape(date)}" if date else ""}</p></div>
</header>
<table><colgroup><col class="lbl"><col><col><col><col><col></colgroup>
<thead><tr><th></th>{head}</tr></thead>
<tbody>{"".join(body)}</tbody></table>
<div class="notes">
  <div><b>Credit a student.</b> Sponsorship dollars can be credited to a student of your
    choice &mdash; child, grandchild, niece or nephew &mdash; toward the Walkathon incentive
    parties. Tell us the relationship when you get in touch.</div>
  <div><b>Tax deductible.</b> The Friends of Hendricks is a 501(c)(3) nonprofit, Tax ID
    20-4931978. Every dollar is given to Hendricks Avenue Elementary through a grant process.</div>
</div>
<footer><span><b>Business partner inquiries</b> &middot; FriendsBusinessPartners@gmail.com</span>
  <span>The Friends of Hendricks &middot; Standing Strong for Our School</span></footer>
</body></html>"""


levels = read_levels()
try:
    import weasyprint
except ImportError:
    sys.exit("!! needs WeasyPrint: uv run --no-project --with weasyprint mockups/levels_pdf.py")
weasyprint.HTML(string=chart(levels), base_url=str(root)).write_pdf(out)
print(f"{out.relative_to(root.parent)}  {out.stat().st_size // 1024} KB  "
      f"({len(levels)} levels, {len({l for l, _, _ in ROWS})} rows)")
