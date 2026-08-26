#!/usr/bin/env python3
"""Make phone-sized copies of the hero clips: docs/videos/<name>-540.mp4

Why: the full clips are 1280x720 at ~2.1 Mbps, about 2.5 MB each. That is fine
on a desktop and rude on a cellular connection, which is why the video loader
used to skip real footage below 760px entirely and show the still photograph.
With a small encode it can serve the small file instead of serving nothing.

960x540 is an exact 16:9 with both dimensions even (x264 wants even dimensions
for 4:2:0 chroma), and it is enough for a background loop sitting behind a dark
veil on a phone at 2-3x pixel density.

There is no ffmpeg on this machine. GStreamer is here and has x264enc,
videoscale and mp4mux, which is a complete pipeline. faststart=true puts the
moov atom in front of the media data, without which the browser has to download
the whole file before it can start.

Run after adding or replacing footage, then re-run encode_videos.py.
"""
import pathlib, subprocess, sys

SRC = pathlib.Path(__file__).parent.parent / "docs" / "videos"
CLIPS = {                                  # output stem -> source file
    "warm-540": "A_warm_and_cheerful_scene_of.mp4",
    "reel-540": "A_dynamic_cinematic_video_show.mp4",
}
W, H, KBPS = 960, 540, 700

if not (gst := __import__("shutil").which("gst-launch-1.0")):
    sys.exit("gst-launch-1.0 not found. Install gstreamer1.0-tools and "
             "gstreamer1.0-plugins-ugly, or encode elsewhere with ffmpeg:\n"
             f"  ffmpeg -i IN.mp4 -vf scale={W}:{H} -c:v libx264 -b:v {KBPS}k "
             "-an -movflags +faststart OUT.mp4")

for stem, filename in CLIPS.items():
    src, out = SRC / filename, SRC / f"{stem}.mp4"
    if not src.exists():
        print(f"  missing source: {filename}")
        continue
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        print(f"  {out.name:16s} up to date, skipped")
        continue
    subprocess.run([
        gst, "-q", "filesrc", f"location={src}", "!", "qtdemux", "!", "avdec_h264",
        "!", "videoscale", "!", "videoconvert", "!", f"video/x-raw,width={W},height={H}",
        "!", "x264enc", f"bitrate={KBPS}", "speed-preset=slower", "key-int-max=60",
        "!", "mp4mux", "faststart=true", "!", "filesink", f"location={out}",
    ], check=True)
    print(f"  {out.name:16s} {W}x{H}  {src.stat().st_size/1048576:.2f} MB -> "
          f"{out.stat().st_size/1048576:.2f} MB  "
          f"({100 - out.stat().st_size*100//src.stat().st_size}% smaller)")
