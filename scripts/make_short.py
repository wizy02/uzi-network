#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Video Producer
Takes a script (text), generates:
  1. Voiceover MP3 (via text_to_speech tool or a free TTS API)
  2. Vertical 9:16 video with kinetic text on dark background
  3. Thumbnail PNG

Output: docs/social/ready-to-upload/{slug}.mp4 + {slug}.png
"""
import os
import sys
import re
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Layout
W, H = 1080, 1920  # 9:16
FPS = 24
DUR_PER_LINE = 2.2  # seconds per line of text
BG_COLOR = (13, 15, 20)  # ink-900
ACCENT = (255, 92, 0)    # uzi orange
TEXT = (245, 245, 250)
TEXT_DIM = (160, 165, 175)


def find_font(size=72, bold=True):
    """Find a bold sans-serif font. Falls back to default."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    """Word-wrap text to fit max_width."""
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def make_frame(text_lines, accent_idx=None, logo=True, frame_idx=0):
    """Render a single frame with kinetic text."""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Title font large
    title_font = find_font(96, bold=True)
    body_font = find_font(72, bold=False)
    small_font = find_font(36, bold=False)
    logo_font = find_font(48, bold=True)

    # Header: Uzi Network logo
    if logo:
        draw.rectangle([(60, 60), (180, 180)], fill=ACCENT)
        draw.text((220, 80), "UZI NETWORK", font=logo_font, fill=TEXT)

    # Draw text lines (centered, vertically stacked)
    if not text_lines:
        return img

    # Use first line as title (large), rest as body
    title = text_lines[0]
    body = text_lines[1:]

    # Title
    title_lines = wrap_text(title, title_font, W - 120)
    y = 500
    for line in title_lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        # Accent line before the title
        if accent_idx is not None and accent_idx == 0:
            draw.rectangle([(x, y - 30), (x + 80, y - 20)], fill=ACCENT)
        draw.text((x, y), line, font=title_font, fill=TEXT if accent_idx is None else ACCENT)
        y += 110

    # Body
    y += 40
    for line in body:
        body_lines = wrap_text(line, body_font, W - 120)
        for bl in body_lines:
            bbox = body_font.getbbox(bl)
            line_w = bbox[2] - bbox[0]
            x = (W - line_w) // 2
            draw.text((x, y), bl, font=body_font, fill=TEXT_DIM)
            y += 90

    # Footer: handle
    footer_font = find_font(42, bold=True)
    draw.text((W // 2 - 100, H - 150), "@uzinetwork", font=footer_font, fill=ACCENT)

    return img


def make_video(script_text, output_mp4, voiceover_mp3=None, accent_words=None):
    """
    Render a vertical video from a script.
    Each sentence = 1 scene.
    """
    # Split script into scenes (sentences or lines)
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    if not sentences:
        print(f"  ! Empty script, skipping {output_mp4}")
        return False

    accent_words = set(w.lower() for w in (accent_words or []))

    # Generate one frame per sentence (held for DUR_PER_LINE seconds)
    frames = []
    for i, s in enumerate(sentences):
        # Wrap sentence into title + body (split on first comma or at 60 chars)
        if "," in s and len(s) > 60:
            title, body = s.split(",", 1)
            title = title.strip()
            body = body.strip()
        elif len(s) > 60:
            title = s[:50].strip()
            body = s[50:].strip()
        else:
            title = s
            body = ""

        lines = [title]
        if body:
            # Split body into chunks of ~50 chars per visual line
            chunks = [body[i:i+50] for i in range(0, len(body), 50)]
            lines.extend(chunks)

        # Accent if any accent word is in the sentence
        is_accent = any(w in s.lower() for w in (accent_words or []))
        frame = make_frame(lines, accent_idx=0 if is_accent else None, logo=(i == 0))
        frames.append((frame, DUR_PER_LINE))

    # Save frames as PNGs to a temp dir (each frame held 3s)
    tmp = Path("/tmp/video_frames")
    tmp.mkdir(exist_ok=True)
    # Repeat each frame 3 seconds × 30 fps = 90 times
    HELD = int(DUR_PER_LINE * FPS)
    for i, (frame, dur) in enumerate(frames):
        for h in range(HELD):
            frame.save(tmp / f"frame_{i*HELD + h:06d}.png")

    # Build ffmpeg command: image sequence → MP4
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(tmp / "frame_%06d.png"),
    ]
    if voiceover_mp3 and os.path.exists(voiceover_mp3):
        cmd.extend(["-i", voiceover_mp3])
        cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])

    cmd.append(output_mp4)
    print(f"  > {' '.join(cmd[:8])} ...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ! ffmpeg error: {res.stderr[-500:]}")
        return False

    # Cleanup
    for f in tmp.glob("frame_*.png"):
        f.unlink()
    tmp.rmdir()
    return True


def make_thumbnail(title, rating, output_png):
    """Render a YouTube Short thumbnail."""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    title_font = find_font(140, bold=True)
    rating_font = find_font(120, bold=True)
    small_font = find_font(64, bold=True)

    # Big title
    lines = wrap_text(title.upper(), title_font, W - 120)
    y = 600
    for line in lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw.text((x, y), line, font=title_font, fill=TEXT)
        y += 160

    # Rating box
    y += 60
    draw.rectangle([(W//2 - 200, y), (W//2 + 200, y + 180)], fill=ACCENT)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    draw.text((W//2 - rw//2, y + 10), rating, font=rating_font, fill=(13, 15, 20))

    # Bottom label
    draw.text((W//2 - 280, H - 220), "30 DAYS TESTED", font=small_font, fill=TEXT)
    draw.text((W//2 - 180, H - 130), "@uzinetwork", font=small_font, fill=ACCENT)

    img.save(output_png)
    return True


# ============================================================
# SCRIPTS — one per top-3 YouTube Short
# ============================================================
SCRIPTS = {
    "short-1-macbook-m5": {
        "title": "MacBook Pro M5: Worth It?",
        "rating": "4.6",
        "accent": ["worth", "love", "best"],
        "script": (
            "I tested the MacBook Pro M5 for 30 days. "
            "Here is the honest take. "
            "The M5 chip is noticeably faster than the M4. "
            "Battery is real, 18 hours in my testing. "
            "The display is the best on any laptop. "
            "What I don't love, 8GB of RAM at this price is criminal. "
            "And no touchscreen in 2026. "
            "Final verdict, 4.6 out of 5. "
            "Buy it if you edit video or code. "
            "Skip it if you only browse the web. "
            "Full review is in the description."
        ),
    },
    "short-2-anker-737": {
        "title": "Anker 737: 140W Beast",
        "rating": "4.7",
        "accent": ["love", "fast", "best"],
        "script": (
            "This power bank charges my laptop on a plane. "
            "I tested the Anker 737 for 78 days. "
            "It outputs 140 watts. That is enough to fast charge a MacBook. "
            "24,000 milliamp hours means full laptop and 2 phones. "
            "The smart display shows real time wattage. "
            "What I do not love. 90 dollars is premium. "
            "And it weighs 1.4 pounds. Not pocket friendly. "
            "Final verdict, 4.7 out of 5. "
            "Best for laptop users and frequent travelers. "
            "Phone only users should get the 25 dollar Anker 10K. "
            "Full review in description."
        ),
    },
    "short-3-sony-xm6": {
        "title": "Sony XM6: ANC King",
        "rating": "4.7",
        "accent": ["love", "best", "comfortable"],
        "script": (
            "The noise cancelling king is back. "
            "I tested the Sony XM6 for 134 days. "
            "The active noise cancellation still beats Bose and Apple. "
            "Battery is 32 hours real world. "
            "Multi point pairing, laptop and phone at the same time. "
            "Lighter clamping than the XM5. More comfortable. "
            "What I do not love. 449 dollars. "
            "And the case is bigger than the XM5 case. "
            "Final verdict, 4.7 out of 5. "
            "Best for frequent flyers and coffee shop workers. "
            "Glasses wearers should get the Bose QC Ultra instead. "
            "Full review in description."
        ),
    },
}


if __name__ == "__main__":
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)

    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in SCRIPTS else list(SCRIPTS.keys())

    for slug in targets:
        s = SCRIPTS[slug]
        print(f"\n=== {slug} ===")
        # Thumbnail
        thumb = out_dir / f"{slug}.png"
        make_thumbnail(s["title"], s["rating"], str(thumb))
        print(f"  ✓ Thumbnail: {thumb}")
        # Video
        video = out_dir / f"{slug}.mp4"
        ok = make_video(s["script"], str(video), accent_words=s["accent"])
        if ok:
            size = os.path.getsize(video)
            print(f"  ✓ Video: {video} ({size // 1024} KB)")
        else:
            print(f"  ✗ Video failed")
