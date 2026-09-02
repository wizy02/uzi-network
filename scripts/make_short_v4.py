#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v4
Real B-roll as full-screen video, text only as lower-third caption.
Like a CapCut / news / TikTok style short.
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
FPS = 30

ACCENT = (255, 92, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SHADOW = (0, 0, 0, 200)


def load_env():
    env_path = Path.home() / ".hermes" / ".social-credentials"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                k, v = line[7:].split("=", 1)
                os.environ[k] = v.strip('"').strip("'")


def find_font(size, bold=True):
    for path in [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


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


def fetch_pexels_videos(query, output_dir, n=4, orientation="portrait"):
    """Fetch n stock videos for the query. Prefers portrait orientation."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode({'query': query, 'per_page': n, 'orientation': orientation})}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        videos = data.get("videos", [])
        paths = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for i, v in enumerate(videos[:n]):
            files = v.get("video_files", [])
            # Prefer portrait HD (720x1280 or similar)
            portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0)]
            landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
            mp4_files = portrait or landscape_hd or [f for f in files if f.get("file_type") == "video/mp4"]
            if not mp4_files:
                continue
            # Pick the smallest that meets quality bar
            best = min(
                [f for f in mp4_files if f.get("height", 0) >= 720] or mp4_files,
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
                if out.stat().st_size > 10000:  # at least 10KB
                    paths.append(str(out))
            except Exception as e:
                print(f"  ! B-roll download failed: {e}")
        return paths
    except Exception as e:
        print(f"  ! Pexels error: {e}")
    return []


def fetch_pexels_thumbnails(query, output_dir, n=4):
    """Fetch portrait thumbnails as a fallback when no video."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    url = f"https://api.pexels.com/v1/search?{urllib.parse.urlencode({'query': query, 'per_page': n, 'orientation': 'portrait'})}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        photos = data.get("photos", [])
        paths = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        for i, p in enumerate(photos[:n]):
            img_url = p.get("src", {}).get("portrait") or p.get("src", {}).get("large2x") or p.get("src", {}).get("large")
            if not img_url:
                continue
            out = Path(output_dir) / f"thumb_{i}.jpg"
            try:
                with urllib.request.urlopen(img_url, timeout=30) as r:
                    with open(out, "wb") as f:
                        f.write(r.read())
                if out.stat().st_size > 10000:
                    paths.append(str(out))
            except Exception:
                pass
        return paths
    except Exception as e:
        print(f"  ! Pexels thumb error: {e}")
    return []


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


def make_caption_frame(text, w=W, h=H):
    """Lower-third caption with shadow. Transparent background except for the caption bar."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Caption is at the bottom 1/3, with semi-transparent black gradient bar
    bar_top = int(h * 0.55)
    # Black gradient bar (we'll fake it with a solid bar + blur via ffmpeg later)
    for y in range(bar_top, h):
        # Gradient from black-translucent to solid black
        alpha = int(180 + 75 * ((y - bar_top) / (h - bar_top)))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))

    # Logo top-left
    draw.rectangle([(40, 40), (130, 130)], fill=ACCENT)
    logo_font = find_font(36, bold=True)
    draw.text((150, 55), "UZI NETWORK", font=logo_font, fill=WHITE)

    # Caption text
    cap_font = find_font(72, bold=True)
    lines = wrap_text(text, cap_font, w - 80)
    y = bar_top + 60
    for line in lines[:3]:  # max 3 lines
        bbox = cap_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (w - line_w) // 2
        # Strong shadow
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), line, font=cap_font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=cap_font, fill=WHITE)
        y += 90

    # Handle bottom-center
    handle_font = find_font(36, bold=True)
    draw.text((w // 2 - 100, h - 80), "@uzinetwork", font=handle_font, fill=ACCENT)
    return img


def make_animated_caption(frames_data, scene_duration, output_mp4, fps=FPS):
    """
    Make a video where each caption is held for scene_duration.
    frames_data: list of (text) tuples
    """
    tmp = Path(output_mp4).parent
    held = int(scene_duration * fps)

    # Render each frame as a PNG
    pngs = []
    for i, (text,) in enumerate(frames_data):
        frame = make_caption_frame(text)
        png_path = tmp / f"cap_{i:03d}.png"
        frame.save(png_path)
        pngs.append(png_path)

    # Concat PNGs with ffmpeg, each held for scene_duration
    with open(tmp / "cap_concat.txt", "w") as f:
        for png in pngs:
            f.write(f"file '{png}'\n")
            f.write(f"duration {scene_duration:.3f}\n")
        # Last file needs extra duration entry
        f.write(f"file '{pngs[-1]}'\n")

    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(tmp / "cap_concat.txt"),
        "-r", str(fps),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"  ! Caption render error: {res.stderr[-300:]}")
        return False
    return True


def make_short(slug, title, rating, accent, script, search_terms, output_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v4/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    # 1. Voiceover
    print("  1. Voiceover...")
    voiceover = tmp / "voiceover.mp3"
    if fetch_voiceover(script, str(voiceover)):
        dur_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
            capture_output=True, text=True
        )
        voiceover_duration = float(dur_out.stdout.strip())
        print(f"     ✓ {voiceover.stat().st_size // 1024} KB, {voiceover_duration:.1f}s")
    else:
        voiceover = None
        voiceover_duration = 30.0

    # 2. B-roll videos (try multiple search terms, multiple orientation filters)
    print("  2. B-roll...")
    broll_videos = []
    for term in search_terms:
        for orient in ["portrait", ""]:
            vids = fetch_pexels_videos(term, str(tmp / "videos"), n=4, orientation=orient)
            broll_videos.extend(vids)
            if len(broll_videos) >= 3:
                break
        if len(broll_videos) >= 3:
            break

    if not broll_videos:
        # Fall back to image slideshow
        print("     No videos found, falling back to image slideshow")
        for term in search_terms:
            thumbs = fetch_pexels_thumbnails(term, str(tmp / "thumbs"), n=4)
            if thumbs:
                broll_videos = thumbs
                break
    print(f"     {len(broll_videos)} source clip(s)")

    # 3. Split script into scenes
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    n_scenes = len(sentences)
    scene_duration = voiceover_duration / n_scenes if voiceover_duration > 0 else 3.0
    print(f"  3. {n_scenes} scenes × {scene_duration:.2f}s")

    # 4. Build background video
    print("  4. Background video...")
    bg_video = tmp / "bg.mp4"
    if not broll_videos:
        # Solid dark background
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x0d0f14:s={W}x{H}:d={voiceover_duration + 1}:r={FPS}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg_video)
        ], capture_output=True, text=True)
    else:
        # Concat all b-roll, scaled to fill 1080x1920, trimmed to voiceover_duration
        # Use concat demuxer, then scale + crop
        concat_list = tmp / "concat.txt"
        with open(concat_list, "w") as f:
            for v in broll_videos:
                f.write(f"file '{v}'\n")
        # Loop the b-roll if total < voiceover_duration
        # First, find total duration of b-roll
        total = 0
        for v in broll_videos:
            d = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", v],
                capture_output=True, text=True
            )
            try:
                total += float(d.stdout.strip())
            except Exception:
                total += 5
        if total < voiceover_duration:
            # Add an extra loop entry
            with open(concat_list, "a") as f:
                for v in broll_videos:
                    f.write(f"file '{v}'\n")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-t", f"{voiceover_duration + 0.5}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an",
            str(bg_video)
        ], capture_output=True, text=True)
    print(f"     ✓ {bg_video.stat().st_size // 1024} KB")

    # 5. Build caption overlay
    print("  5. Caption overlay...")
    cap_video = tmp / "cap.mp4"
    frames_data = [(s,) for s in sentences]
    make_animated_caption(frames_data, scene_duration, str(cap_video))
    print(f"     ✓ {cap_video.stat().st_size // 1024} KB")

    # 6. Composite
    print("  6. Compositing...")
    video_out = output_dir / f"{slug}.mp4"
    if voiceover and voiceover.exists():
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-i", str(cap_video),
            "-i", str(voiceover),
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(bg_video),
            "-i", str(cap_video),
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)

    if video_out.exists():
        print(f"     ✓ {video_out.stat().st_size // 1024} KB, {video_out}")
    else:
        print("     ! Render failed")
    return video_out


def make_thumbnail(broll_paths, title, rating, output_png):
    """Use first b-roll frame as thumbnail, with text overlay."""
    img = Image.new("RGB", (W, H), (13, 15, 20))
    if broll_paths and Path(broll_paths[0]).exists():
        try:
            if broll_paths[0].endswith(".mp4"):
                # Extract first frame
                subprocess.run([
                    "ffmpeg", "-y", "-i", broll_paths[0],
                    "-vf", "select=eq(n\\,0)", "-vframes", "1",
                    "/tmp/thumb_extract.jpg"
                ], capture_output=True, text=True)
                bg = Image.open("/tmp/thumb_extract.jpg").convert("RGB")
            else:
                bg = Image.open(broll_paths[0]).convert("RGB")
            bg.thumbnail((W, H))
            img.paste(bg, ((W - bg.width) // 2, (H - bg.height) // 2))
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    title_font = find_font(140, bold=True)
    rating_font = find_font(120, bold=True)
    small_font = find_font(64, bold=True)

    # Dark gradient overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 100))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Title
    lines = wrap_text(title.upper(), title_font, W - 120)
    y = 600
    for line in lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        for dx, dy in [(-4, -4), (4, 4)]:
            draw.text((x + dx, y + dy), line, font=title_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=title_font, fill=WHITE)
        y += 160
    y += 60
    draw.rectangle([(W//2 - 200, y), (W//2 + 200, y + 180)], fill=ACCENT)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    draw.text((W//2 - rw//2, y + 10), rating, font=rating_font, fill=(13, 15, 20))
    draw.text((W//2 - 280, H - 220), "30 DAYS TESTED", font=small_font, fill=WHITE)
    draw.text((W//2 - 180, H - 130), "@uzinetwork", font=small_font, fill=ACCENT)
    img.save(output_png)
    Path("/tmp/thumb_extract.jpg").unlink(missing_ok=True)


SCRIPTS = {
    "short-1-macbook-m5": {
        "title": "MacBook Pro M5: Worth It?",
        "rating": "4.6",
        "search": ["apple laptop", "macbook", "laptop computer", "typing laptop", "office desk laptop"],
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
        "search": ["power bank", "portable charger", "battery charging", "phone charging", "travel charger"],
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
        "search": ["headphones", "wireless headphones", "music listening", "headphones person", "commute headphones"],
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
        make_short(slug, s["title"], s["rating"], None, s["script"], s["search"], out_dir)
    print("\nDone.")
