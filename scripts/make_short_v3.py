#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v3
Pipeline: script → ElevenLabs voiceover → Pexels B-roll (as video bg) → 9:16 with overlay text
"""
import os
import sys
import re
import subprocess
import json
import urllib.request
import urllib.parse
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 24
DUR_PER_SCENE = 2.5

BG_COLOR = (13, 15, 20)
ACCENT = (255, 92, 0)
TEXT = (245, 245, 245)
TEXT_DIM = (180, 185, 195)


def load_env():
    env_path = Path.home() / ".hermes" / ".social-credentials"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                k, v = line[7:].split("=", 1)
                os.environ[k] = v.strip('"').strip("'")


def find_font(size=72, bold=True):
    for path in [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    words = text.split()
    lines, current = [], []
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


def fetch_voiceover(text, output_mp3):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return False
    voice_id = "CwhRBWXzGAHq8TQ4Fs17"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        with open(output_mp3, "wb") as f:
            f.write(resp.read())
    return True


def fetch_pexels_videos(query, output_dir, n=2):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode({'query': query, 'per_page': n})}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        videos = data.get("videos", [])
        paths = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for i, v in enumerate(videos[:n]):
            files = v.get("video_files", [])
            mp4_files = [f for f in files if f.get("file_type") == "video/mp4"]
            if not mp4_files:
                continue
            best = min(
                [f for f in mp4_files if f.get("width", 9999) <= 1280] or mp4_files,
                key=lambda f: f.get("width", 9999) * f.get("height", 9999)
            )
            out = Path(output_dir) / f"broll_{i}.mp4"
            try:
                dl_req = urllib.request.Request(
                    best["link"],
                    headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"}
                )
                with urllib.request.urlopen(dl_req, timeout=60) as v_resp:
                    with open(out, "wb") as f:
                        f.write(v_resp.read())
                paths.append(str(out))
            except Exception as e:
                print(f"  ! B-roll download failed: {e}")
        return paths
    except Exception as e:
        print(f"  ! Pexels video error: {e}")
    return []


def make_text_overlay(text_lines, accent_idx=None, logo=True, w=W, h=H):
    """Render just the text overlay (transparent PNG)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    title_font = find_font(96, bold=True)
    body_font = find_font(72, bold=False)
    small_font = find_font(36, bold=False)
    logo_font = find_font(48, bold=True)

    # Always show logo + brand (top left)
    if logo:
        draw.rectangle([(60, 60), (180, 180)], fill=ACCENT)
        draw.text((220, 80), "UZI NETWORK", font=logo_font, fill=(255, 255, 255, 255))

    if not text_lines:
        return img

    title = text_lines[0]
    body = text_lines[1:]
    title_lines = wrap_text(title, title_font, w - 120)
    y = 700
    for line in title_lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (w - line_w) // 2
        if accent_idx is not None and accent_idx == 0:
            draw.rectangle([(x, y - 30), (x + 80, y - 20)], fill=ACCENT)
        # Black shadow for legibility on any bg
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=title_font, fill=(0, 0, 0, 220))
        draw.text((x, y), line, font=title_font, fill=TEXT if accent_idx is None else ACCENT)
        y += 110
    y += 40
    for line in body:
        body_lines = wrap_text(line, body_font, w - 120)
        for bl in body_lines:
            bbox = body_font.getbbox(bl)
            line_w = bbox[2] - bbox[0]
            x = (w - line_w) // 2
            for dx, dy in [(-2, -2), (2, 2)]:
                draw.text((x + dx, y + dy), bl, font=body_font, fill=(0, 0, 0, 200))
            draw.text((x, y), bl, font=body_font, fill=TEXT_DIM)
            y += 90

    # Footer
    footer_font = find_font(42, bold=True)
    for dx, dy in [(-2, -2), (2, 2)]:
        draw.text((W // 2 - 100 + dx, H - 150 + dy), "@uzinetwork", font=footer_font, fill=(0, 0, 0, 220))
    draw.text((W // 2 - 100, H - 150), "@uzinetwork", font=footer_font, fill=ACCENT)
    return img


def make_short(slug, title, rating, accent, script, search_terms, output_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_prod/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    # 1. Voiceover
    print("  1. Voiceover...")
    voiceover = tmp / "voiceover.mp3"
    if fetch_voiceover(script, str(voiceover)):
        # Get voiceover duration via ffprobe
        dur_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
            capture_output=True, text=True
        )
        voiceover_duration = float(dur_out.stdout.strip())
        print(f"     ✓ {voiceover.stat().st_size // 1024} KB, {voiceover_duration:.1f}s")
    else:
        voiceover = None
        voiceover_duration = 0

    # 2. B-roll
    print("  2. B-roll...")
    broll_videos = []
    for term in search_terms:
        vids = fetch_pexels_videos(term, str(tmp / "broll"), n=3)
        broll_videos.extend(vids)
        if broll_videos:
            break
    print(f"     {len(broll_videos)} b-roll clip(s)")

    # 3. Compute scene timing based on voiceover duration
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    n_scenes = len(sentences)

    if voiceover_duration > 0 and n_scenes > 0:
        scene_duration = voiceover_duration / n_scenes
    else:
        scene_duration = DUR_PER_SCENE

    print(f"  3. {n_scenes} scenes × {scene_duration:.2f}s each")

    # 4. Build text overlay frames (one per scene)
    accent_words = set(w.lower() for w in (accent or []))
    print("  4. Building overlays...")
    for i, s in enumerate(sentences):
        if "," in s and len(s) > 60:
            t, b = s.split(",", 1)
            t, b = t.strip(), b.strip()
        elif len(s) > 60:
            t, b = s[:50].strip(), s[50:].strip()
        else:
            t, b = s, ""
        lines = [t] + ([b[i:i+50] for i in range(0, len(b), 50)] if b else [])
        is_accent = any(w in s.lower() for w in accent_words)
        overlay = make_text_overlay(lines, accent_idx=0 if is_accent else None, logo=(i == 0))
        overlay.save(tmp / f"overlay_{i:03d}.png")

    # 5. Build background video by cycling through b-roll
    print("  5. Background video...")
    bg_video = tmp / "bg.mp4"
    if broll_videos:
        # Concat b-roll videos into one, then trim to voiceover duration
        # First, write a list file for ffmpeg concat
        concat_list = tmp / "concat.txt"
        with open(concat_list, "w") as f:
            for v in broll_videos:
                f.write(f"file '{v}'\n")
        # Concat and trim
        target_duration = max(voiceover_duration, n_scenes * scene_duration)
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-t", f"{target_duration + 1}",  # +1 for safety
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            str(bg_video)
        ], capture_output=True, text=True)
    else:
        # Solid color background
        target_duration = max(voiceover_duration, n_scenes * scene_duration)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0d0f14:s={W}x{H}:d={target_duration + 1}:r={FPS}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(bg_video)
        ], capture_output=True, text=True)
    print(f"     ✓ {bg_video.stat().st_size // 1024} KB")

    # 6. Build overlay video with timing
    print("  6. Overlay video with timing...")
    overlay_video = tmp / "overlay.mp4"
    # Use ffmpeg to make a video where each overlay is held for scene_duration
    # We use the "loop" + "concat" approach: each overlay becomes a video, then concat
    overlay_clips = []
    for i in range(n_scenes):
        clip = tmp / f"clip_{i:03d}.mp4"
        # Hold one PNG for scene_duration
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", str(tmp / f"overlay_{i:03d}.png"),
            "-t", f"{scene_duration:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            str(clip)
        ], capture_output=True, text=True)
        overlay_clips.append(str(clip))
    # Concat overlay clips
    with open(tmp / "overlay_concat.txt", "w") as f:
        for c in overlay_clips:
            f.write(f"file '{c}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "overlay_concat.txt"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(overlay_video)
    ], capture_output=True, text=True)
    print(f"     ✓ {overlay_video.stat().st_size // 1024} KB")

    # 7. Composite bg + overlay
    print("  7. Compositing...")
    video_out = output_dir / f"{slug}.mp4"
    if voiceover and voiceover.exists():
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-i", str(overlay_video),
            "-i", str(voiceover),
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-i", str(overlay_video),
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)

    if video_out.exists():
        print(f"     ✓ {video_out.stat().st_size // 1024} KB")
    else:
        print("     ! Final render failed")
    return video_out


def make_thumbnail(title, rating, output_png):
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    title_font = find_font(140, bold=True)
    rating_font = find_font(120, bold=True)
    small_font = find_font(64, bold=True)
    lines = wrap_text(title.upper(), title_font, W - 120)
    y = 600
    for line in lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        draw.text((x, y), line, font=title_font, fill=TEXT)
        y += 160
    y += 60
    draw.rectangle([(W//2 - 200, y), (W//2 + 200, y + 180)], fill=ACCENT)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    draw.text((W//2 - rw//2, y + 10), rating, font=rating_font, fill=(13, 15, 20))
    draw.text((W//2 - 280, H - 220), "30 DAYS TESTED", font=small_font, fill=TEXT)
    draw.text((W//2 - 180, H - 130), "@uzinetwork", font=small_font, fill=ACCENT)
    img.save(output_png)


SCRIPTS = {
    "short-1-macbook-m5": {
        "title": "MacBook Pro M5: Worth It?",
        "rating": "4.6",
        "accent": ["worth", "love", "best"],
        "search": ["apple laptop", "laptop computer", "typing on laptop"],
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
        "search": ["power bank", "portable charger", "battery"],
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
        "search": ["headphones", "wireless headphones", "music listening"],
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
    load_env()
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in SCRIPTS else list(SCRIPTS.keys())
    for slug in SCRIPTS:
        if slug not in targets:
            continue
        s = SCRIPTS[slug]
        thumb = out_dir / f"{slug}.png"
        make_thumbnail(s["title"], s["rating"], str(thumb))
        make_short(slug, s["title"], s["rating"], s["accent"], s["script"], s["search"], out_dir)
    print("\nDone.")
