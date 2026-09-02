#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v5
Real product card intro + B-roll + voiceover + captions
Structure (40s Short):
  0-3s:   Product card (real product image, brand, rating)
  3-5s:   Hook scene (kinetic text)
  5-35s:  B-roll background + caption overlay
  35-40s: Verdict card (rating + verdict)
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

BG_COLOR = (13, 15, 20)
ACCENT = (255, 92, 0)
WHITE = (245, 245, 245)
BLACK = (0, 0, 0)


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
        url, data=json.dumps(payload).encode(),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        with open(output_mp3, "wb") as f:
            f.write(resp.read())
    return True


def fetch_pexels_videos(query, output_dir, n=4):
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
            portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0)]
            landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
            mp4_files = portrait or landscape_hd or [f for f in files if f.get("file_type") == "video/mp4"]
            if not mp4_files:
                continue
            best = min(
                [f for f in mp4_files if f.get("height", 0) >= 720] or mp4_files,
                key=lambda f: f.get("width", 9999) * f.get("height", 9999)
            )
            out = Path(output_dir) / f"broll_{i}.mp4"
            try:
                dl_req = urllib.request.Request(best["link"], headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
                with urllib.request.urlopen(dl_req, timeout=60) as v_resp:
                    with open(out, "wb") as f:
                        f.write(v_resp.read())
                if out.stat().st_size > 10000:
                    paths.append(str(out))
            except Exception as e:
                pass
        return paths
    except Exception:
        return []


def make_product_card(product_path, brand, name, rating, output_png, w=W, h=H):
    """Make the intro product card (3 seconds). Real product image, brand, rating."""
    img = Image.new("RGB", (w, h), BG_COLOR)
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            # Fit to width, leave space for text at top
            target_w = w
            target_h = int(h * 0.55)
            bg.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
        except Exception as e:
            print(f"  ! Product image load failed: {e}")
    draw = ImageDraw.Draw(img)
    # Top: brand + product name
    brand_font = find_font(48, bold=False)
    draw.text((60, 60), brand.upper(), font=brand_font, fill=(150, 155, 165))
    name_font = find_font(80, bold=True)
    name_lines = wrap_text(name, name_font, w - 120)
    y = 130
    for line in name_lines[:2]:
        draw.text((60, y), line, font=name_font, fill=WHITE)
        y += 90
    # Bottom: rating + verdict
    rating_y = int(h * 0.65)
    draw.rectangle([(60, rating_y), (w - 60, rating_y + 4)], fill=ACCENT)
    rating_font = find_font(120, bold=True)
    rating_text = f"⭐ {rating}/5"
    bbox = rating_font.getbbox(rating_text)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, rating_y + 60), rating_text, font=rating_font, fill=WHITE)
    # Sub
    sub_font = find_font(56, bold=False)
    draw.text(((w - 200) // 2, rating_y + 220), "30 DAYS TESTED", font=sub_font, fill=ACCENT)
    # Logo top-right
    logo_font = find_font(36, bold=True)
    draw.text((w - 250, 60), "UZI NETWORK", font=logo_font, fill=WHITE)
    # Handle
    handle_font = find_font(48, bold=True)
    draw.text((w // 2 - 130, h - 120), "@uzinetwork", font=handle_font, fill=ACCENT)
    img.save(output_png)


def make_caption_frame(text, w=W, h=H):
    """Lower-third caption with shadow."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bar_top = int(h * 0.55)
    for y in range(bar_top, h):
        alpha = int(180 + 75 * ((y - bar_top) / (h - bar_top)))
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    cap_font = find_font(72, bold=True)
    lines = wrap_text(text, cap_font, w - 80)
    y = bar_top + 60
    for line in lines[:3]:
        bbox = cap_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (w - line_w) // 2
        for dx, dy in [(-4, -4), (4, -4), (-4, 4), (4, 4), (-2, 0), (2, 0)]:
            draw.text((x + dx, y + dy), line, font=cap_font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=cap_font, fill=WHITE)
        y += 90
    # Logo top
    draw.rectangle([(40, 40), (130, 130)], fill=ACCENT)
    logo_font = find_font(36, bold=True)
    draw.text((150, 55), "UZI NETWORK", font=logo_font, fill=WHITE)
    handle_font = find_font(36, bold=True)
    draw.text((w // 2 - 100, h - 80), "@uzinetwork", font=handle_font, fill=ACCENT)
    return img


def make_verdict_card(brand, name, rating, output_png, w=W, h=H):
    """Final verdict card (3 seconds)."""
    img = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)
    # Big rating
    rating_font = find_font(280, bold=True)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, h // 2 - 300), rating, font=rating_font, fill=ACCENT)
    # Subtitle
    sub_font = find_font(72, bold=True)
    sub_text = "FINAL VERDICT"
    bbox = sub_font.getbbox(sub_text)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, h // 2 + 20), sub_text, font=sub_font, fill=WHITE)
    # Stars
    star_font = find_font(100, bold=True)
    stars = "★" * int(float(rating)) + "☆" * (5 - int(float(rating)))
    bbox = star_font.getbbox(stars)
    stw = bbox[2] - bbox[0]
    draw.text(((w - stw) // 2, h // 2 + 130), stars, font=star_font, fill=ACCENT)
    # CTA
    cta_font = find_font(48, bold=True)
    cta_text = "Full review in description"
    bbox = cta_font.getbbox(cta_text)
    cw = bbox[2] - bbox[0]
    draw.text(((w - cw) // 2, h - 250), cta_text, font=cta_font, fill=WHITE)
    handle_font = find_font(48, bold=True)
    draw.text((w // 2 - 130, h - 150), "@uzinetwork", font=handle_font, fill=ACCENT)
    img.save(output_png)


def make_short(slug, brand, name, rating, accent, script, search_terms, product_image, output_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v5/{slug}")
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

    # 2. B-roll
    print("  2. B-roll...")
    broll_videos = []
    for term in search_terms:
        vids = fetch_pexels_videos(term, str(tmp / "videos"), n=4)
        broll_videos.extend(vids)
        if len(broll_videos) >= 3:
            break
    print(f"     {len(broll_videos)} b-roll clip(s)")

    # 3. Scenes
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    n_scenes = len(sentences)
    # Total: 3s intro + (voiceover_duration + 3s) b-roll + 3s outro
    intro_dur = 3.0
    outro_dur = 3.0
    broll_dur = voiceover_duration
    scene_duration = broll_dur / n_scenes if n_scenes > 0 else 2.5
    total_dur = intro_dur + broll_dur + outro_dur
    print(f"  3. Intro {intro_dur}s + {n_scenes} captions × {scene_duration:.2f}s + Outro {outro_dur}s = {total_dur:.1f}s")

    # 4. Build product card (intro)
    print("  4. Product card (intro)...")
    intro_png = tmp / "intro.png"
    make_product_card(product_image, brand, name, rating, str(intro_png))
    intro_video = tmp / "intro.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(intro_png),
        "-t", f"{intro_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(FPS), str(intro_video)
    ], capture_output=True, text=True)

    # 5. Build background (b-roll loop)
    print("  5. B-roll background...")
    bg_video = tmp / "bg.mp4"
    if broll_videos:
        concat_list = tmp / "concat.txt"
        with open(concat_list, "w") as f:
            for v in broll_videos:
                f.write(f"file '{v}'\n")
        # Loop if needed
        total_broll = 0
        for v in broll_videos:
            d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                               "-of", "default=noprint_wrappers=1:nokey=1", v], capture_output=True, text=True)
            try:
                total_broll += float(d.stdout.strip())
            except Exception:
                total_broll += 5
        while total_broll < broll_dur + 1:
            with open(concat_list, "a") as f:
                for v in broll_videos:
                    f.write(f"file '{v}'\n")
            total_broll *= 2
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-t", f"{broll_dur + 0.5}",
            "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-an", str(bg_video)
        ], capture_output=True, text=True)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"color=c=0x0d0f14:s={W}x{H}:d={broll_dur + 0.5}:r={FPS}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg_video)
        ], capture_output=True, text=True)
    print(f"     ✓ {bg_video.stat().st_size // 1024} KB")

    # 6. Caption overlay
    print("  6. Caption overlay...")
    cap_pngs = []
    for i, s in enumerate(sentences):
        p = make_caption_frame(s)
        p.save(tmp / f"cap_{i:03d}.png")
        cap_pngs.append(tmp / f"cap_{i:03d}.png")
    with open(tmp / "cap_concat.txt", "w") as f:
        for p in cap_pngs:
            f.write(f"file '{p}'\n")
            f.write(f"duration {scene_duration:.3f}\n")
        f.write(f"file '{cap_pngs[-1]}'\n")
    cap_video = tmp / "cap.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "cap_concat.txt"),
        "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(cap_video)
    ], capture_output=True, text=True)
    print(f"     ✓ {cap_video.stat().st_size // 1024} KB")

    # 7. Outro (verdict card)
    print("  7. Outro card...")
    outro_png = tmp / "outro.png"
    make_verdict_card(brand, name, rating, str(outro_png))
    outro_video = tmp / "outro.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(outro_png),
        "-t", f"{outro_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(FPS), str(outro_video)
    ], capture_output=True, text=True)

    # 8. Composite: intro + bg_with_caption + outro
    print("  8. Composite...")
    middle_video = tmp / "middle.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(bg_video),
        "-i", str(cap_video),
        "-filter_complex", "[0:v][1:v]overlay=0:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(middle_video)
    ], capture_output=True, text=True)

    # Concat intro + middle + outro
    concat_final = tmp / "concat_final.txt"
    with open(concat_final, "w") as f:
        f.write(f"file '{intro_video}'\n")
        f.write(f"file '{middle_video}'\n")
        f.write(f"file '{outro_video}'\n")
    video_out = output_dir / f"{slug}.mp4"
    if voiceover and voiceover.exists():
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_final),
            "-i", str(voiceover),
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k",
            "-pix_fmt", "yuv420p", "-shortest", str(video_out)
        ], capture_output=True, text=True)
    else:
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_final),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest", str(video_out)
        ], capture_output=True, text=True)
    if video_out.exists():
        print(f"     ✓ {video_out.stat().st_size // 1024} KB, {video_out}")
    else:
        print("     ! Render failed")
    return video_out


SCRIPTS = {
    "short-1-macbook-m5": {
        "brand": "Apple", "name": "MacBook Pro M5", "rating": "4.6",
        "search": ["laptop", "macbook", "office"],
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
            "Skip it if you only browse the web."
        ),
    },
    "short-2-anker-737": {
        "brand": "Anker", "name": "Anker 737 Power Bank", "rating": "4.7",
        "search": ["power bank", "charging", "travel"],
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
            "Phone only users should get the 25 dollar Anker 10K."
        ),
    },
    "short-3-sony-xm6": {
        "brand": "Sony", "name": "Sony WH-1000XM6", "rating": "4.7",
        "search": ["headphones", "music", "commute"],
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
            "Glasses wearers should get the Bose QC Ultra instead."
        ),
    },
}


if __name__ == "__main__":
    load_env()
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = Path("/home/ubuntu/projects/uzi-network/src/assets/reviews")
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in SCRIPTS else list(SCRIPTS.keys())
    for slug in SCRIPTS:
        if slug not in targets:
            continue
        s = SCRIPTS[slug]
        product_img = asset_dir / f"{slug}.jpg"
        if not product_img.exists():
            product_img = None
        make_short(slug, s["brand"], s["name"], s["rating"], None, s["script"], s["search"], product_img, out_dir)
    print("\nDone.")
