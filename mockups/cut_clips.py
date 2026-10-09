#!/usr/bin/env python3
"""Cut shots out of a clip, keeping the rest in order: docs/videos/<name>.mp4

Run: python3 mockups/cut_clips.py, then python3 mockups/encode_videos.py

The committee liked the home page footage but not two things in it: a big
eagle sign Hendricks does not have, and a hallway that looks nothing like the
inside of the school. "Just show the random kid going into the school." The
clip is generated, so it cannot be re-shot with the real building -- but it is
made of separate shots, and the ones that are wrong can be dropped.

Each cut is listed as the frame ranges to KEEP, end exclusive, at the source's
own 24 fps. The shot boundaries were found by comparing neighbouring frames:
a cut shows up as a jump in difference, and between shots there is none.

  arrival  from A_warm_and_cheerful_scene_of.mp4 (240 frames, 10.0 s)
             0- 60  wide shot of the front, children walking up       keep
            60-111  boy walking past the big eagle sign                drop
                    (the next shot opens with the sign's edge still in
                    frame for three frames, so the drop runs to 111)
           111-156  boy on the steps, turning to wave                  keep
           156-204  teacher at the door, children going in             keep
           204-240  the hallway inside                                 drop
           -> 153 frames, 6.4 s, and it loops back to the wide shot cleanly

Writes a full-size copy and a phone-sized one (960x540, the size and bitrate
encode_mobile.py uses), both with faststart so the browser can start before
the whole file arrives. The source file is never touched -- the frozen E
direction still plays it as {{VIDEO_WARM}}.
"""
import pathlib, shutil, subprocess, sys, tempfile

SRC = pathlib.Path(__file__).parent.parent / "docs" / "videos"
FPS = 24

CUTS = {
    "arrival": ("A_warm_and_cheerful_scene_of.mp4", [(0, 60), (111, 156), (156, 204)]),
}

SIZES = [("", 1280, 720, 2000), ("-540", 960, 540, 700)]   # suffix, w, h, kbps

gst = shutil.which("gst-launch-1.0")
if not gst:
    sys.exit("gst-launch-1.0 not found -- see encode_mobile.py for what to install")

for name, (filename, keep) in CUTS.items():
    src = SRC / filename
    if not src.exists():
        print(f"  missing source: {filename}")
        continue
    with tempfile.TemporaryDirectory() as tmp:
        frames = pathlib.Path(tmp)
        # Lossless frames in between, so the only lossy step is the final encode.
        subprocess.run([gst, "-q", "filesrc", f"location={src}", "!", "qtdemux", "!",
                        "avdec_h264", "!", "videoconvert", "!", "pngenc", "compression-level=1",
                        "!", "multifilesink", f"location={frames}/in-%04d.png"], check=True)
        total = len(list(frames.glob("in-*.png")))
        n = 0
        for a, b in keep:
            if b > total:
                sys.exit(f"!! {name}: range {a}-{b} runs past the clip's {total} frames")
            for i in range(a, b):
                (frames / f"in-{i:04d}.png").rename(frames / f"out-{n:04d}.png")
                n += 1
        for suffix, w, h, kbps in SIZES:
            out = SRC / f"{name}{suffix}.mp4"
            subprocess.run([
                gst, "-q", "multifilesrc", f"location={frames}/out-%04d.png", "index=0",
                f"caps=image/png,framerate={FPS}/1", "!", "pngdec", "!", "videoscale", "!",
                "videoconvert", "!", f"video/x-raw,format=I420,width={w},height={h}", "!",
                "x264enc", f"bitrate={kbps}", "speed-preset=slower", f"key-int-max={FPS * 2}",
                "!", "video/x-h264,profile=high", "!",
                "mp4mux", "faststart=true", "!", "filesink", f"location={out}",
            ], check=True)
            print(f"  {out.name:18s} {w}x{h}  {n} of {total} frames, {n / FPS:.1f} s  "
                  f"{out.stat().st_size / 1048576:.2f} MB")
