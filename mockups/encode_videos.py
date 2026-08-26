#!/usr/bin/env python3
"""Encode docs/videos/*.mp4 into mockups/.videos.json as data URIs.

Not committed: the output is ~14 MB. Re-run after adding or replacing footage.
"""
import base64, json, pathlib

root = pathlib.Path(__file__).parent
src = root.parent / "docs" / "videos"
MAP = {                                   # token name -> file
    "reel":    "A_dynamic_cinematic_video_show.mp4",
    "warm":    "A_warm_and_cheerful_scene_of.mp4",
    "energy":  "high_energy_school_promo_video.mp4",
    # Phone-sized copies, made by encode_mobile.py. {{VIDEO_WARM_SM}} and
    # {{VIDEO_REEL_SM}}. A page that offers one gets real footage on a phone
    # instead of the still photograph; one that does not still gets the still.
    "warm_sm": "warm-540.mp4",
    "reel_sm": "reel-540.mp4",
}
out = {}
for name, fn in MAP.items():
    p = src / fn
    if not p.exists():
        print(f"  missing: {fn}")
        continue
    raw = p.read_bytes()
    out[name] = "data:video/mp4;base64," + base64.b64encode(raw).decode()
    print(f"  {name:7s} {fn[:38]:40s} {len(raw)/1048576:5.2f} MB -> {len(out[name])/1048576:5.2f} MB base64")
json.dump(out, open(root / ".videos.json", "w"))
print(f"wrote .videos.json ({(root/'.videos.json').stat().st_size/1048576:.1f} MB)")
