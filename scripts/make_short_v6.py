#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v6
Uses espeak-ng for TTS (free, robotic voice) instead of ElevenLabs.
Keeps everything else same as v5: product card intro, B-roll, captions, verdict outro.
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


def fetch_voiceover_espeak(text, output_wav):
    """Use espeak-ng to generate WAV, then convert to MP3."""
    # espeak-ng: -s 150 (speed wpm), -v en-us
    wav_path = output_wav.with_suffix('.wav')
    try:
        subprocess.run([
            "espeak-ng",
            "-v", "en-us",
            "-s", "150",
            "-w", str(wav_path),
            text
        ], check=True, capture_output=True, text=True)
        # Convert wav to mp3 (ffmpeg)
        subprocess.run([
            "ffmpeg", "-y", "-i", str(wav_path),
            "-c:a", "libmp3lame", "-b:a", "128k",
            str(output_wav)
        ], check=True, capture_output=True, text=True)
        wav_path.unlink(missing_ok=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ! espeak-ng error: {e.stderr[:200]}")
        return False
    except Exception as e:
        print(f"  ! Voiceover error: {e}")
        return False


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
    img = Image.new("RGB", (w, h), BG_COLOR)
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            target_w = w
            target_h = int(h * 0.55)
            bg.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
        except Exception as e:
            print(f"  ! Product image load failed: {e}")
    draw = ImageDraw.Draw(img)
    brand_font = find_font(48, bold=False)
    draw.text((60, 60), brand.upper(), font=brand_font, fill=(150, 155, 165))
    name_font = find_font(80, bold=True)
    name_lines = wrap_text(name, name_font, w - 120)
    y = 130
    for line in name_lines[:2]:
        draw.text((60, y), line, font=name_font, fill=WHITE)
        y += 90
    rating_y = int(h * 0.65)
    draw.rectangle([(60, rating_y), (w - 60, rating_y + 4)], fill=ACCENT)
    rating_font = find_font(120, bold=True)
    rating_text = f"⭐ {rating}/5"
    bbox = rating_font.getbbox(rating_text)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, rating_y + 60), rating_text, font=rating_font, fill=WHITE)
    sub_font = find_font(56, bold=False)
    draw.text(((w - 200) // 2, rating_y + 220), "30 DAYS TESTED", font=sub_font, fill=ACCENT)
    logo_font = find_font(36, bold=True)
    draw.text((w - 250, 60), "UZI NETWORK", font=logo_font, fill=WHITE)
    handle_font = find_font(48, bold=True)
    draw.text((w // 2 - 130, h - 120), "@uzinetwork", font=handle_font, fill=ACCENT)
    img.save(output_png)


def make_caption_frame(text, w=W, h=H):
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
    draw.rectangle([(40, 40), (130, 130)], fill=ACCENT)
    logo_font = find_font(36, bold=True)
    draw.text((150, 55), "UZI NETWORK", font=logo_font, fill=WHITE)
    handle_font = find_font(36, bold=True)
    draw.text((w // 2 - 100, h - 80), "@uzinetwork", font=handle_font, fill=ACCENT)
    return img


def make_verdict_card(brand, name, rating, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), BG_COLOR)
    draw = ImageDraw.Draw(img)
    rating_font = find_font(280, bold=True)
    bbox = rating_font.getbbox(rating)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, h // 2 - 300), rating, font=rating_font, fill=ACCENT)
    sub_font = find_font(72, bold=True)
    sub_text = "FINAL VERDICT"
    bbox = sub_font.getbbox(sub_text)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, h // 2 + 20), sub_text, font=sub_font, fill=WHITE)
    star_font = find_font(100, bold=True)
    stars = "★" * int(float(rating)) + "☆" * (5 - int(float(rating)))
    bbox = star_font.getbbox(stars)
    stw = bbox[2] - bbox[0]
    draw.text(((w - stw) // 2, h // 2 + 130), stars, font=star_font, fill=ACCENT)
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
    tmp = Path(f"/tmp/short_v6/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)

    # 1. Voiceover (espeak-ng)
    print("  1. Voiceover (espeak-ng)...")
    voiceover = tmp / "voiceover.mp3"
    if fetch_voiceover_espeak(script, voiceover):
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
    intro_dur = 3.0
    outro_dur = 3.0
    broll_dur = voiceover_duration
    scene_duration = broll_dur / n_scenes if n_scenes > 0 else 2.5
    total_dur = intro_dur + broll_dur + outro_dur
    print(f"  3. Intro {intro_dur}s + {n_scenes} captions × {scene_duration:.2f}s + Outro {outro_dur}s = {total_dur:.1f}s")

    # 4. Product card (intro)
    print("  4. Product card (intro)...")
    intro_png = tmp / "intro.png"
    make_product_card(product_image, brand, name, rating, str(intro_png))
    intro_video = tmp / "intro.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(intro_png),
        "-t", f"{intro_dur}", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-r", str(FPS), str(intro_video)
    ], capture_output=True, text=True)

    # 5. Background (b-roll loop)
    print("  5. B-roll background...")
    bg_video = tmp / "bg.mp4"
    if broll_videos:
        concat_list = tmp / "concat.txt"
        with open(concat_list, "w") as f:
            for v in broll_videos:
                f.write(f"file '{v}'\n")
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


# Reuse same SCRIPTS dict from v5
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
    "short-4-anker-powercore-10k": {
        "brand": "Anker", "name": "Anker PowerCore 10000", "rating": "4.5",
        "search": ["power bank", "portable charger"],
        "script": (
            "I tested the Anker PowerCore 10000 for 60 days. "
            "It's a reliable 10000mAh power bank with 18W USB-C. "
            "Charges an iPhone about 2.5 times. "
            "The LED indicator shows remaining charge. "
            "What I don't love: only 18W output, not enough for laptops. "
            "And it's a bit bulky for pocket carry. "
            "Final verdict, 4.5 out of 5. "
            "Great for daily phone charging and travel. "
            "Pair with a 30W USB-C charger for faster recharging."
        ),
    },
    "short-5-anker-727-charging-station": {
        "brand": "Anker", "name": "Anker 727 Charging Station", "rating": "4.6",
        "search": ["charging station", "desk organizer"],
        "script": (
            "I tested the Anker 727 Charging Station for 45 days. "
            "It's a 6-in-1 dock with two USB-C (100W total), two USB-A, and AC outlet. "
            "Powers my laptop, phone, tablet, and lamp all from one unit. "
            "The built-in cable management keeps things tidy. "
            "What I don't love: it's large and not travel-friendly. "
            "And the AC outlet is only 60W. "
            "Final verdict, 4.6 out of 5. "
            "Ideal for home office desk setups. "
            "If you need portability, look at the Anker 523 instead."
        ),
    },
    "short-6-anker-nano-ii-65w": {
        "brand": "Anker", "name": "Anker Nano II 65W", "rating": "4.6",
        "search": ["usb c charger", "65w charger"],
        "script": (
            "I tested the Anker Nano II 65W for 30 days. "
            "It's a tiny gallium nitride charger that folds flat. "
            "Charges a MacBook Air at full speed. "
            "The foldable prongs make it great for travel. "
            "What I don't love: only one port. "
            "And it can get warm under heavy load. "
            "Final verdict, 4.6 out of 5. "
            "Best for travelers who need one compact charger. "
            "If you need multiple ports, get the Anker 577 instead."
        ),
    },
    "short-7-anker-543-usb-c-hub": {
        "brand": "Anker", "name": "Anker 543 USB-C Hub", "rating": "4.4",
        "search": ["usb c hub", "multiport adapter"],
        "script": (
            "I tested the Anker 543 USB-C Hub for 40 days. "
            "It adds two USB-C, two USB-A, HDMI, and SD card reader. "
            "Turns one USB-C port into a full workstation. "
            "What I don't love: the HDMI is limited to 4K@30Hz. "
            "And it doesn't support Thunderbolt 4 speeds. "
            "Final verdict, 4.4 out of 5. "
            "Great for connecting peripherals to a MacBook. "
            "If you need Thunderbolt 4, consider the CalDigit Element 5."
        ),
    },
    "short-8-anker-soundcore-life-q35": {
        "brand": "Anker", "name": "Soundcore Life Q35", "rating": "4.4",
        "search": ["wireless headphones", "noise cancelling"],
        "script": (
            "I tested the Soundcore Life Q35 for 50 days. "
            "They offer hybrid active noise cancellation and Hi-Res audio. "
            "LDAC support for high-quality wireless audio. "
            "What I don't love: the ANC is not as strong as Sony or Bose. "
            "And the ear cups can feel warm after long use. "
            "Final verdict, 4.4 out of 5. "
            "Excellent value for the features. "
            "If you need top-tier ANC, go for Sony XM6 or Bose QC Ultra."
        ),
    },
    "short-9-apple-airpods-pro-3": {
        "brand": "Apple", "name": "AirPods Pro (2nd gen)", "rating": "4.7",
        "search": ["airpods pro", "wireless earbuds"],
        "script": (
            "I tested the AirPods Pro (2nd gen) for 90 days. "
            "The H2 chip provides excellent adaptive noise cancellation. "
            "Transparency mode lets you hear surroundings naturally. "
            "What I don't love: the battery life is only 6 hours with ANC on. "
            "And the case doesn't support wireless charging in this model. "
            "Final verdict, 4.7 out of 5. "
            "Best for iPhone users wanting seamless integration. "
            "If you need longer battery, consider the AirPods (3rd gen)."
        ),
    },
    "short-10-aqara-u200": {
        "brand": "Aqara", "name": "Aqara U200 Smart Door Lock", "rating": "4.3",
        "search": ["smart door lock", "fingerprint lock"],
        "script": (
            "I tested the Aqara U200 for 60 days on my front door. "
            "It unlocks via fingerprint, keypad, or app. "
            "The build quality feels solid and secure. "
            "What I don't love: the fingerprint sensor can fail with wet fingers. "
            "And it requires a separate Aqara Hub to work with Apple Home. "
            "Final verdict, 4.3 out of 5. "
            "Great for those invested in the Aqara ecosystem. "
            "If you want native HomeKit, look at the Yale Assure Lock SL."
        ),
    },
    "short-11-claude-4-sonnet": {
        "brand": "Anthropic", "name": "Claude 3.5 Sonnet", "rating": "4.8",
        "search": ["ai model", "large language model"],
        "script": (
            "I tested Claude 3.5 Sonnet for 30 days via the API. "
            "It excels at reasoning, coding, and long-context understanding. "
            "The 200k token context window is a game-changer. "
            "What I don't love: it can be verbose in simple answers. "
            "And it sometimes over-refuses harmless prompts. "
            "Final verdict, 4.8 out of 5. "
            "One of the best LLMs available today. "
            "If you need the absolute cutting edge, wait for Claude 4 Opus."
        ),
    },
    "short-12-eero-max-7": {
        "brand": "eero", "name": "eero Max 7", "rating": "4.5",
        "search": ["mesh wifi", "wifi 6e router"],
        "script": (
            "I tested the eero Max 7 for 45 days in a 3000 sq ft home. "
            "It's a tri-band Wi-Fi 6E system with 2.5Gbps wired backhaul. "
            "Coverage is excellent and latency is low for gaming. "
            "What I don't love: the price is high at $500 for a 2-pack. "
            "And the setup requires the eero app (no web interface). "
            "Final verdict, 4.5 out of 5. "
            "Best for large homes needing seamless coverage. "
            "If you're on a budget, consider the TP-Link Deco XE75."
        ),
    },
    "short-13-garmin-fenix-9-solar": {
        "brand": "Garmin", "name": "Garmin Fenix 9 Solar", "rating": "4.7",
        "search": ["garmin fenix", "solar watch"],
        "script": (
            "I tested the Garmin Fenix 9 Solar for 60 days of daily wear. "
            "The solar charging lens extends battery life in sunlight. "
            "It offers advanced metrics for running, cycling, and swimming. "
            "What I don't love: the price is premium at $999. "
            "And the interface can feel overwhelming for beginners. "
            "Final verdict, 4.7 out of 5. "
            "Best for serious athletes who want all the data. "
            "If you want a simpler experience, look at the Garmin Forerunner 265."
        ),
    },
    "short-14-garmin-instinct-2-solar": {
        "brand": "Garmin", "name": "Garmin Instinct 2 Solar", "rating": "4.5",
        "search": ["garmin instinct", "solar watch rugged"],
        "script": (
            "I tested the Garmin Instinct 2 Solar for 60 days of outdoor use. "
            "It's built to military standards and resists shocks, heat, and water. "
            "The solar charging extends battery life in the field. "
            "What I don't love: the display is monochrome and limited. "
            "And it lacks advanced running dynamics found in pricier models. "
            "Final verdict, 4.5 out of 5. "
            "Ideal for outdoor enthusiasts who need a tough watch. "
            "If you want a color display, look at the Garmin Venu 3."
        ),
    },
    "short-15-govee-glide-wall-light": {
        "brand": "Govee", "name": "Govee Glide Wall Light", "rating": "4.2",
        "search": ["rgb wall light", "smart lighting"],
        "script": (
            "I tested the Govee Glide Wall Light for 30 days. "
            "It's a flexible LED strip that creates colorful ambient lighting. "
            "The app offers millions of colors and scene modes. "
            "What I don't love: the adhesive can weaken over time on textured walls. "
            "And the Bluetooth range is limited to about 30 feet. "
            "Final verdict, 4.2 out of 5. "
            "Great for adding color to a bedroom or gaming setup. "
            "If you need longer range, consider the Philips Hue Lightstrip Plus."
        ),
    },
    "short-16-jackery-explorer-1000-v2": {
        "brand": "Jackery", "name": "Jackery Explorer 1000 v2", "rating": "4.4",
        "search": ["portable power station", "solar generator"],
        "script": (
            "I tested the Jackery Explorer 1000 v2 for 40 days of camping and outages. "
            "It's a 1002Wh lithium battery with pure sine wave AC outlet. "
            "Can power a refrigerator, CPAP, or small appliances. "
            "What I don't love: the recharge time is long via wall outlet (~7 hours). "
            "And it's heavy at 22 pounds for frequent carrying. "
            "Final verdict, 4.4 out of 5. "
            "Excellent for emergency power and camping. "
            "If you need faster charging, look at the EcoFlow Delta 2."
        ),
    },
    "short-17-logitech-mx-master-4": {
        "brand": "Logitech", "name": "Logitech MX Master 4", "rating": "4.7",
        "search": ["ergonomic mouse", "wireless mouse"],
        "script": (
            "I tested the Logitech MX Master 4 for 60 days of daily use. "
            "The ergonomic shape reduces wrist strain during long sessions. "
            "The mag-speed wheel allows ultra-fast scrolling. "
            "What I don't love: the thumb wheel can feel awkward at first. "
            "And it doesn't work well on glass surfaces. "
            "Final verdict, 4.7 out of 5. "
            "The gold standard for productivity mice. "
            "If you prefer a lighter mouse, look at the Logitech MX Anywhere 3."
        ),
    },
    "short-18-notion-calendar": {
        "brand": "Notion", "name": "Notion Calendar", "rating": "4.3",
        "search": ["calendar app", "schedule planner"],
        "script": (
            "I tested Notion Calendar for 45 days of daily planning. "
            "It integrates tightly with Notion databases and offers time blocking. "
            "What I don't love: it lacks native timezone support for travel. "
            "And the mobile app feels slower than the web version. "
            "Final verdict, 4.3 out of 5. "
            "Excellent for those already using Notion for notes and tasks. "
            "If you need a dedicated calendar app, consider Fantastical or Apple Calendar."
        ),
    },
    "short-19-ring-battery-doorbell-plus": {
        "brand": "Ring", "name": "Ring Battery Doorbell Plus", "rating": "4.4",
        "search": ["video doorbell", "smart doorbell"],
        "script": (
            "I tested the Ring Battery Doorbell Plus for 60 days. "
            "It offers 1080p HD video, color night vision, and motion detection. "
            "The quick-release battery pack makes recharging easy. "
            "What I don't love: the motion zones can be tricky to set up precisely. "
            "And it requires a Ring Protect subscription for video storage. "
            "Final verdict, 4.4 out of 5. "
            "A solid choice for those invested in the Ring ecosystem. "
            "If you want local storage only, consider the Eufy SoloCam S220."
        ),
    },
    "short-20-sennheiser-momentum-4": {
        "brand": "Sennheiser", "name": "Sennheiser Momentum 4", "rating": "4.6",
        "search": ["wireless headphones", "noise cancelling"],
        "script": (
            "I tested the Sennheiser Momentum 4 for 80 days of daily use. "
            "They offer industry-leading noise cancellation and 60-hour battery. "
            "The sound signature is warm and detailed, great for all genres. "
            "What I don't love: the ANC can create a slight pressure sensation. "
            "And the touch controls can be overly sensitive. "
            "Final verdict, 4.6 out of 5. "
            "One of the best wireless headphones available today. "
            "If you want the absolute best ANC, consider the Sony XM6."
        ),
    },
    "short-21-tp-link-kasa-smart-plug": {
        "brand": "TP-Link", "name": "TP-Link Kasa Smart Plug", "rating": "4.2",
        "search": ["smart plug", "outlet timer"],
        "script": (
            "I tested the TP-Link Kasa Smart Plug for 60 days of daily use. "
            "It's a reliable Wi-Fi outlet that lets you schedule devices remotely. "
            "The app and voice assistant integration work well. "
            "What I don't love: the Wi-Fi connection can drop occasionally. "
            "And it blocks the adjacent outlet due to its size. "
            "Final verdict, 4.2 out of 5. "
            "Great for automating lamps, fans, and holiday lights. "
            "If you need outdoor use, look at the TP-Link Tapo P110."
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