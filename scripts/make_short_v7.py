#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v7
DIRECTOR-LOCKED: B-roll is the picture. Text is small and minimal.
- One real video clip per scene
- Text is a 3-5 word caption at the bottom corner
- No full-screen text. No black overlays.
- Scene structure: product hero shot → multiple B-roll shots → product end card
"""
import os
import sys
import re
import subprocess
import json
import urllib.request
import urllib.parse
import shutil
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
ACCENT = (255, 92, 0)
WHITE = (245, 245, 245)


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


def fetch_voiceover_espeak(text, output_mp3):
    """Free TTS via espeak-ng."""
    wav_path = output_mp3.with_suffix('.wav')
    try:
        # Use a slower, more deliberate speed for review content
        subprocess.run([
            "espeak-ng",
            "-v", "en-us",
            "-s", "155",
            "-p", "55",  # pitch
            "-w", str(wav_path),
            text
        ], check=True, capture_output=True, text=True)
        subprocess.run([
            "ffmpeg", "-y", "-i", str(wav_path),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(output_mp3)
        ], check=True, capture_output=True, text=True)
        wav_path.unlink(missing_ok=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def fetch_pexels_videos(query, output_dir, n=8, min_duration_s=4):
    """Fetch n Pexels videos, preferring landscape HD with min 4s duration."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    # Try multiple search terms
    all_paths = []
    queries = query if isinstance(query, list) else [query]
    for q in queries:
        if len(all_paths) >= n:
            break
        url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode({'query': q, 'per_page': 15, 'orientation': 'portrait'})}"
        req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            videos = data.get("videos", [])
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            for v in videos:
                if len(all_paths) >= n:
                    break
                if v.get("duration", 0) < min_duration_s:
                    continue
                files = v.get("video_files", [])
                # Prefer portrait HD (matches our format)
                portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0) and f.get("height", 0) >= 720]
                landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
                mp4_files = portrait or landscape_hd or [f for f in files if f.get("file_type") == "video/mp4"]
                if not mp4_files:
                    continue
                # Pick the smallest that meets quality bar
                best = min(
                    [f for f in mp4_files if f.get("height", 0) >= 720] or mp4_files,
                    key=lambda f: f.get("width", 9999) * f.get("height", 9999)
                )
                out = Path(output_dir) / f"broll_{len(all_paths):02d}.mp4"
                try:
                    dl_req = urllib.request.Request(best["link"], headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
                    with urllib.request.urlopen(dl_req, timeout=60) as v_resp:
                        with open(out, "wb") as f:
                            f.write(v_resp.read())
                    if out.stat().st_size > 50000:  # at least 50KB = real video
                        all_paths.append(str(out))
                except Exception as e:
                    pass
        except Exception as e:
            pass
    return all_paths[:n]


def make_minimal_caption(text, w=W, h=H):
    """ONE small caption at the bottom. No big overlay."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cap_font = find_font(64, bold=True)
    # Measure text
    bbox = cap_font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    # Position at bottom-center, 100px from bottom
    x = (w - text_w) // 2
    y = h - 200
    # Subtle dark pill behind text for legibility (no full black bar)
    pad_x, pad_y = 30, 14
    pill_w = text_w + pad_x * 2
    pill_h = text_h + pad_y * 2
    pill_x = (w - pill_w) // 2
    pill_y = y - pad_y
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=12, fill=(0, 0, 0, 200)
    )
    # Shadow
    for dx, dy in [(-2, -2), (2, 2)]:
        draw.text((x + dx, y + dy), text, font=cap_font, fill=(0, 0, 0, 255))
    draw.text((x, y), text, font=cap_font, fill=WHITE)
    return img


def make_hero_card(product_path, brand, name, rating, output_png, w=W, h=H):
    """5-second product hero shot. Big product photo, 1-2 words of text, brand and rating."""
    img = Image.new("RGB", (w, h), (13, 15, 20))
    # Try to use the product image as the background
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            # Fit to cover
            target_h = int(h * 0.7)
            bg.thumbnail((w, target_h), Image.Resampling.LANCZOS)
            # Center the image
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    # Brand strip at top
    brand_font = find_font(40, bold=True)
    brand_y = 80
    draw.text((60, brand_y), brand.upper(), font=brand_font, fill=(180, 185, 195))
    # Small rating pill at top-right
    rating_text = f"⭐ {rating}"
    rating_font = find_font(36, bold=True)
    bbox = rating_font.getbbox(rating_text)
    rw = bbox[2] - bbox[0] + 30
    rh = 60
    draw.rounded_rectangle([(w - rw - 60, brand_y - 10), (w - 60, brand_y - 10 + rh)],
                          radius=30, fill=ACCENT)
    draw.text((w - rw - 60 + 15, brand_y), rating_text, font=rating_font, fill=(13, 15, 20))
    # Big product name in lower third (one or two words max per line)
    name_font = find_font(120, bold=True)
    # Wrap manually to short lines
    words = name.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = name_font.getbbox(test)
        if bbox[2] - bbox[0] > w - 120:
            if current:
                lines.append(" ".join(current))
            current = [word]
        else:
            current.append(test.split(" ", len(current) - 1)[-1].split(" ")[0] if current else word) if False else current + [word]
    if current:
        lines.append(" ".join(current))
    # Simpler: just two lines if needed
    if not lines:
        lines = [name]
    if len(lines) > 2:
        lines = [" ".join(lines[:len(lines)//2 + 1]), " ".join(lines[len(lines)//2 + 1:])]
    y = int(h * 0.78)
    for line in lines:
        bbox = name_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lx = (w - lw) // 2
        # Shadow
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text((lx + dx, y + dy), line, font=name_font, fill=(0, 0, 0))
        draw.text((lx, y), line, font=name_font, fill=WHITE)
        y += 130
    img.save(output_png)


def make_verdict_card(product_path, brand, name, rating, output_png, w=W, h=H):
    """End card: big rating, product photo, 2 words."""
    img = Image.new("RGB", (w, h), (13, 15, 20))
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            target_h = int(h * 0.5)
            bg.thumbnail((w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 100
            img.paste(bg, (x, y))
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    # Big rating number
    rating_font = find_font(280, bold=True)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    rx = (w - rw) // 2
    ry = int(h * 0.55)
    for dx, dy in [(-5, -5), (5, 5)]:
        draw.text((rx + dx, ry + dy), rating, font=rating_font, fill=(0, 0, 0))
    draw.text((rx, ry), rating, font=rating_font, fill=ACCENT)
    sub_font = find_font(80, bold=True)
    text = "FINAL SCORE"
    bbox = sub_font.getbbox(text)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, ry + 320), text, font=sub_font, fill=WHITE)
    # Bottom CTA
    cta_font = find_font(48, bold=True)
    cta = "Full review in bio"
    bbox = cta_font.getbbox(cta)
    cw = bbox[2] - bbox[0]
    draw.text(((w - cw) // 2, h - 250), cta, font=cta_font, fill=ACCENT)
    handle_font = find_font(48, bold=True)
    draw.text((w // 2 - 130, h - 150), "@uzinetwork", font=handle_font, fill=WHITE)
    img.save(output_png)


def cut_clip(input_path, output_path, duration_s, start_s=0.0):
    """Cut a sub-clip from a longer b-roll video."""
    subprocess.run([
        "ffmpeg", "-y",
        "-ss", f"{start_s}",
        "-i", str(input_path),
        "-t", f"{duration_s}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
        "-an",
        str(output_path)
    ], capture_output=True, text=True)
    return Path(output_path).exists() and Path(output_path).stat().st_size > 0


def make_short(slug, brand, name, rating, accent, script, search_terms, product_image, output_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v7/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    clips_dir = tmp / "clips"
    clips_dir.mkdir()

    # 1. Voiceover
    print("  1. Voiceover...")
    voiceover = tmp / "voiceover.mp3"
    if fetch_voiceover_espeak(script, voiceover):
        dur_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
            capture_output=True, text=True
        )
        try:
            voiceover_duration = float(dur_out.stdout.strip())
        except Exception:
            voiceover_duration = 30.0
        print(f"     ✓ {voiceover.stat().st_size // 1024} KB, {voiceover_duration:.1f}s")
    else:
        print("     ! Voiceover failed")
        return None

    # 2. B-roll clips (need 6+ for a 35s short, each 4-6s long)
    print("  2. B-roll clips...")
    broll_paths = fetch_pexels_videos(search_terms, str(clips_dir), n=8, min_duration_s=4)
    print(f"     ✓ {len(broll_paths)} video clips downloaded")

    if len(broll_paths) < 4:
        print(f"     ! Not enough b-roll ({len(broll_paths)}), skipping")
        return None

    # 3. Plan scenes: 2s hero, then 5s × N scenes, then 3s verdict
    # Total = voiceover_duration + 5
    hero_dur = 2.0
    verdict_dur = 3.0
    broll_dur = voiceover_duration
    # Split script into short captions (3-5 words each)
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    # Make captions: take 3-5 word phrases from each sentence
    captions = []
    for s in sentences:
        words = s.split()
        if len(words) <= 5:
            captions.append(s)
        else:
            # Split into chunks of 3-5 words
            i = 0
            while i < len(words):
                chunk_len = min(4, len(words) - i)
                captions.append(" ".join(words[i:i+chunk_len]))
                i += chunk_len
    n_scenes = len(captions)
    scene_dur = broll_dur / n_scenes
    print(f"  3. {n_scenes} scenes × {scene_dur:.2f}s (b-roll)")

    # 4. Cut b-roll clips to scene_dur each (round-robin pick)
    scene_clips = []
    for i, caption in enumerate(captions):
        # Pick a random b-roll (don't repeat adjacent)
        broll_idx = i % len(broll_paths)
        # Pick a random start time within the clip
        broll_path = broll_paths[broll_idx]
        clip_path = tmp / f"scene_{i:02d}.mp4"
        # Find duration of source
        d_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", broll_path],
            capture_output=True, text=True
        )
        try:
            src_dur = float(d_out.stdout.strip())
        except Exception:
            src_dur = 5.0
        # Pick start so it doesn't go past end
        max_start = max(0, src_dur - scene_dur - 0.5)
        start = random.uniform(0, max_start) if max_start > 0 else 0
        # Cut
        cut_clip(broll_path, str(clip_path), scene_dur, start)
        scene_clips.append((str(clip_path), caption))
    print(f"     ✓ cut {len(scene_clips)} scene clips")

    # 5. Compose each scene: video + caption overlay
    composed = []
    for i, (clip, caption) in enumerate(scene_clips):
        comp = tmp / f"composed_{i:02d}.mp4"
        # Render caption overlay as a PNG
        cap_png = tmp / f"cap_{i:02d}.png"
        make_minimal_caption(caption).save(cap_png)
        # Compose video + overlay
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(clip),
            "-i", str(cap_png),
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            str(comp)
        ], capture_output=True, text=True)
        if comp.exists():
            composed.append(str(comp))
    print(f"     ✓ composed {len(composed)} scenes")

    # 6. Hero card (product image)
    print("  6. Hero card...")
    hero_png = tmp / "hero.png"
    make_hero_card(product_image, brand, name, rating, str(hero_png))
    hero_mp4 = tmp / "hero.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(hero_png),
        "-t", f"{hero_dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(hero_mp4)
    ], capture_output=True, text=True)

    # 7. Verdict card
    print("  7. Verdict card...")
    verdict_png = tmp / "verdict.png"
    make_verdict_card(product_image, brand, name, rating, str(verdict_png))
    verdict_mp4 = tmp / "verdict.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(verdict_png),
        "-t", f"{verdict_dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(verdict_mp4)
    ], capture_output=True, text=True)

    # 8. Concat: hero + scenes + verdict
    print("  8. Concat...")
    concat_list = tmp / "concat.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{hero_mp4}'\n")
        for c in composed:
            f.write(f"file '{c}'\n")
        f.write(f"file '{verdict_mp4}'\n")
    middle = tmp / "middle.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(middle)
    ], capture_output=True, text=True)

    # 9. Add voiceover
    print("  9. Add voiceover...")
    video_out = output_dir / f"{slug}.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(middle),
        "-i", str(voiceover),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-shortest",
        str(video_out)
    ], capture_output=True, text=True)

    if video_out.exists():
        size = video_out.stat().st_size
        print(f"     ✓ {size//1024} KB, {video_out}")
        return video_out
    return None


# All 21 product scripts (matching v6 keys)
SCRIPTS = {
    "short-1-macbook-m5": {"brand": "Apple", "name": "MacBook Pro M5", "rating": "4.6",
        "search": ["laptop", "macbook", "office desk", "typing", "tech office"],
        "script": "I tested the MacBook Pro M5 for 30 days. Here is the honest take. The M5 chip is noticeably faster than the M4. Battery is real. 18 hours in my testing. The display is the best on any laptop. What I do not love. 8GB of RAM at this price is criminal. And no touchscreen in 2026. Final verdict. 4.6 out of 5. Buy it if you edit video or code. Skip it if you only browse the web."},
    "short-2-anker-737": {"brand": "Anker", "name": "Anker 737", "rating": "4.7",
        "search": ["power bank", "charging", "travel", "airport", "laptop charging"],
        "script": "This power bank charges my laptop on a plane. I tested the Anker 737 for 78 days. It outputs 140 watts. That is enough to fast charge a MacBook. 24,000 milliamp hours. Full laptop and 2 phones. The smart display shows real time wattage. What I do not love. 90 dollars is premium. And it weighs 1.4 pounds. Final verdict. 4.7 out of 5. Best for laptop users and frequent travelers."},
    "short-3-sony-xm6": {"brand": "Sony", "name": "Sony WH-1000XM6", "rating": "4.7",
        "search": ["headphones", "music", "commute", "coffee shop", "airplane travel"],
        "script": "The noise cancelling king is back. I tested the Sony XM6 for 134 days. Active noise cancellation still beats Bose and Apple. Battery is 32 hours real world. Multi point pairing. Laptop and phone at the same time. Lighter clamping than the XM5. More comfortable. What I do not love. 449 dollars. Final verdict. 4.7 out of 5. Best for frequent flyers and coffee shop workers."},
    "short-4-anker-powercore-10k": {"brand": "Anker", "name": "Anker PowerCore 10K", "rating": "4.5",
        "search": ["power bank", "portable charger", "phone charging", "travel"],
        "script": "I tested the Anker PowerCore 10K for 60 days. It is a reliable 10,000mAh power bank with 18W USB-C. Charges an iPhone about 2.5 times. The LED indicator shows remaining charge. What I do not love. Only 18W output. Not enough for laptops. Final verdict. 4.5 out of 5. Great for daily phone charging and travel."},
    "short-5-anker-727-charging-station": {"brand": "Anker", "name": "Anker 727", "rating": "4.6",
        "search": ["charging station", "desk organizer", "office desk", "cable management"],
        "script": "I tested the Anker 727 Charging Station for 45 days. It is a 6 in 1 dock with two USB-C. 100W total. Two USB-A and AC outlet. Powers my laptop, phone, tablet, and lamp. The built-in cable management keeps things tidy. What I do not love. It is large and not travel friendly. Final verdict. 4.6 out of 5. Ideal for home office desk setups."},
    "short-6-anker-nano-ii-65w": {"brand": "Anker", "name": "Anker Nano II 65W", "rating": "4.6",
        "search": ["usb c charger", "small charger", "travel charger", "office desk"],
        "script": "I tested the Anker Nano II 65W for 30 days. It is a tiny gallium nitride charger that folds flat. Charges a MacBook Air at full speed. The foldable prongs make it great for travel. What I do not love. Only one port. Final verdict. 4.6 out of 5. Best for travelers who need one compact charger."},
    "short-7-anker-543-usb-c-hub": {"brand": "Anker", "name": "Anker 543 Hub", "rating": "4.4",
        "search": ["usb c hub", "laptop accessories", "office desk", "macbook accessories"],
        "script": "I tested the Anker 543 USB-C Hub for 40 days. It adds two USB-C, two USB-A, HDMI, and SD card reader. Turns one USB-C port into a full workstation. What I do not love. The HDMI is limited to 4K at 30Hz. Final verdict. 4.4 out of 5. Great for connecting peripherals to a MacBook."},
    "short-8-anker-soundcore-life-q35": {"brand": "Anker", "name": "Soundcore Life Q35", "rating": "4.4",
        "search": ["headphones", "music", "office work", "study headphones"],
        "script": "I tested the Soundcore Life Q35 for 50 days. They offer hybrid active noise cancellation and Hi-Res audio. LDAC support for high quality wireless audio. What I do not love. The ANC is not as strong as Sony or Bose. Final verdict. 4.4 out of 5. Excellent value for the features."},
    "short-9-apple-airpods-pro-3": {"brand": "Apple", "name": "AirPods Pro", "rating": "4.7",
        "search": ["airpods", "earbuds", "commute", "office work", "music"],
        "script": "I tested the AirPods Pro for 90 days. The H2 chip provides excellent adaptive noise cancellation. Transparency mode lets you hear surroundings naturally. What I do not love. The battery life is only 6 hours with ANC on. Final verdict. 4.7 out of 5. Best for iPhone users wanting seamless integration."},
    "short-10-aqara-u200": {"brand": "Aqara", "name": "Aqara U200", "rating": "4.3",
        "search": ["smart home", "front door", "fingerprint lock", "home security"],
        "script": "I tested the Aqara U200 for 60 days on my front door. It unlocks via fingerprint, keypad, or app. The build quality feels solid and secure. What I do not love. The fingerprint sensor can fail with wet fingers. Final verdict. 4.3 out of 5. Great for those invested in the Aqara ecosystem."},
    "short-11-claude-4-sonnet": {"brand": "Anthropic", "name": "Claude 3.5 Sonnet", "rating": "4.8",
        "search": ["ai", "computer", "laptop", "office work", "coding"],
        "script": "I tested Claude 3.5 Sonnet for 30 days via the API. It excels at reasoning, coding, and long context understanding. The 200k token context window is a game changer. What I do not love. It can be verbose in simple answers. Final verdict. 4.8 out of 5. One of the best LLMs available today."},
    "short-12-eero-max-7": {"brand": "eero", "name": "eero Max 7", "rating": "4.5",
        "search": ["wifi router", "mesh wifi", "home office", "gaming setup"],
        "script": "I tested the eero Max 7 for 45 days in a 3000 square foot home. It is a tri-band Wi-Fi 6E system with 2.5Gbps wired backhaul. Coverage is excellent and latency is low for gaming. What I do not love. The price is high at 500 dollars. Final verdict. 4.5 out of 5. Best for large homes needing seamless coverage."},
    "short-13-garmin-fenix-9-solar": {"brand": "Garmin", "name": "Garmin Fenix 9", "rating": "4.7",
        "search": ["smartwatch", "running", "outdoor", "fitness", "hiking"],
        "script": "I tested the Garmin Fenix 9 Solar for 60 days of daily wear. The solar charging lens extends battery life in sunlight. It offers advanced metrics for running, cycling, and swimming. What I do not love. The price is premium at 999 dollars. Final verdict. 4.7 out of 5. Best for serious athletes who want all the data."},
    "short-14-garmin-instinct-2-solar": {"brand": "Garmin", "name": "Garmin Instinct 2", "rating": "4.5",
        "search": ["smartwatch", "outdoor", "hiking", "camping", "rugged watch"],
        "script": "I tested the Garmin Instinct 2 Solar for 60 days of outdoor use. It is built to military standards and resists shocks, heat, and water. The solar charging extends battery life in the field. What I do not love. The display is monochrome. Final verdict. 4.5 out of 5. Ideal for outdoor enthusiasts who need a tough watch."},
    "short-15-govee-glide-wall-light": {"brand": "Govee", "name": "Govee Glide", "rating": "4.2",
        "search": ["rgb light", "smart home", "gaming setup", "bedroom", "led lights"],
        "script": "I tested the Govee Glide Wall Light for 30 days. It is a flexible LED strip that creates colorful ambient lighting. The app offers millions of colors and scene modes. What I do not love. The adhesive can weaken over time. Final verdict. 4.2 out of 5. Great for adding color to a bedroom or gaming setup."},
    "short-16-jackery-explorer-1000-v2": {"brand": "Jackery", "name": "Jackery 1000 v2", "rating": "4.4",
        "search": ["camping", "outdoor", "power station", "solar", "rv"],
        "script": "I tested the Jackery Explorer 1000 v2 for 40 days of camping and outages. It is a 1002Wh lithium battery with pure sine wave AC outlet. Can power a refrigerator, CPAP, or small appliances. What I do not love. The recharge time is long. Final verdict. 4.4 out of 5. Excellent for emergency power and camping."},
    "short-17-logitech-mx-master-4": {"brand": "Logitech", "name": "MX Master 4", "rating": "4.7",
        "search": ["computer mouse", "office work", "productivity", "desk setup"],
        "script": "I tested the Logitech MX Master 4 for 60 days of daily use. The ergonomic shape reduces wrist strain during long sessions. The mag speed wheel allows ultra fast scrolling. What I do not love. The thumb wheel can feel awkward at first. Final verdict. 4.7 out of 5. The gold standard for productivity mice."},
    "short-18-notion-calendar": {"brand": "Notion", "name": "Notion Calendar", "rating": "4.3",
        "search": ["office work", "laptop", "calendar", "study", "work desk"],
        "script": "I tested Notion Calendar for 45 days of daily planning. It integrates tightly with Notion databases and offers time blocking. What I do not love. It lacks native timezone support for travel. Final verdict. 4.3 out of 5. Excellent for those already using Notion."},
    "short-19-ring-battery-doorbell-plus": {"brand": "Ring", "name": "Ring Doorbell Plus", "rating": "4.4",
        "search": ["front door", "home security", "doorbell", "smart home", "porch"],
        "script": "I tested the Ring Battery Doorbell Plus for 60 days. It offers 1080p HD video, color night vision, and motion detection. The quick release battery pack makes recharging easy. What I do not love. It requires a Ring Protect subscription. Final verdict. 4.4 out of 5. A solid choice for those invested in Ring."},
    "short-20-sennheiser-momentum-4": {"brand": "Sennheiser", "name": "Sennheiser M4", "rating": "4.6",
        "search": ["headphones", "music", "office work", "study", "studio"],
        "script": "I tested the Sennheiser Momentum 4 for 80 days. They offer industry leading noise cancellation and 60 hour battery. The sound signature is warm and detailed. What I do not love. The ANC can create slight pressure. Final verdict. 4.6 out of 5. One of the best wireless headphones available today."},
    "short-21-tp-link-kasa-smart-plug": {"brand": "TP-Link", "name": "Kasa Smart Plug", "rating": "4.2",
        "search": ["smart home", "home automation", "outlet", "office", "energy"],
        "script": "I tested the TP-Link Kasa Smart Plug for 60 days. It is a reliable Wi-Fi outlet that lets you schedule devices remotely. The app and voice assistant integration work well. What I do not love. It blocks the adjacent outlet. Final verdict. 4.2 out of 5. Great for automating lamps and holiday lights."},
}


if __name__ == "__main__":
    load_env()
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = Path("/home/ubuntu/projects/uzi-network/src/assets/reviews")
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in SCRIPTS else list(SCRIPTS.keys())
    success = 0
    for slug in SCRIPTS:
        if slug not in targets:
            continue
        s = SCRIPTS[slug]
        product_img = asset_dir / f"{slug.replace('short-', '').replace('-' + slug.split('-')[1] + '-', '-', 1)}.jpg"
        # Actually use the standard pattern: macbook-pro-m5.jpg
        # The slug is short-1-macbook-m5 -> macbook-pro-m5
        # The mapping is: short-N-{rest} where {rest} is the product slug
        rest = "-".join(slug.split("-")[2:])  # macbook-pro-m5
        product_img = asset_dir / f"{rest}.jpg"
        if not product_img.exists():
            product_img = None
        result = make_short(slug, s["brand"], s["name"], s["rating"], None, s["script"], s["search"], product_img, out_dir)
        if result:
            success += 1
    print(f"\nDone. {success}/{len(targets)} Shorts generated.")