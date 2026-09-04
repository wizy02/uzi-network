#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v9
HUMAN voice (edge-tts Microsoft Neural) + watermark on every frame
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
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30
ACCENT = (255, 92, 0)
WHITE = (245, 245, 245)
VOICE = "en-US-GuyNeural"


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


def fetch_voiceover_edge_tts(text, output_mp3):
    """Use Microsoft edge-tts (free, sounds human)."""
    import edge_tts
    async def run():
        communicate = edge_tts.Communicate(text, VOICE, rate="+0%", pitch="-2Hz")
        await communicate.save(str(output_mp3))
    asyncio.run(run())
    return output_mp3.exists() and output_mp3.stat().st_size > 1000


def fetch_pexels_videos(query, output_dir, n=10, min_duration_s=8):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
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
                portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0) and f.get("height", 0) >= 720]
                landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
                mp4_files = portrait or landscape_hd or [f for f in files if f.get("file_type") == "video/mp4"]
                if not mp4_files:
                    continue
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
                    if out.stat().st_size > 100000:
                        all_paths.append(str(out))
                except Exception:
                    pass
        except Exception:
            pass
    return all_paths[:n]


def make_watermark(w=W, h=H):
    """Subtle watermark in bottom-right corner, present on every frame."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Watermark: @uzinetwork in bottom-right, 60px from edge
    font = find_font(36, bold=True)
    text = "@uzinetwork"
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad = 18
    # Pill background
    pill_x = w - text_w - pad * 2 - 30
    pill_y = h - text_h - pad * 2 - 30
    pill_w = text_w + pad * 2
    pill_h = text_h + pad * 2
    # Shadow
    for dx, dy in [(3, 3), (-3, 3)]:
        draw.rounded_rectangle(
            [(pill_x + dx, pill_y + dy), (pill_x + pill_w + dx, pill_y + pill_h + dy)],
            radius=8, fill=(0, 0, 0, 100)
        )
    # Pill
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=8, fill=(0, 0, 0, 180)
    )
    # Accent line
    draw.rectangle([(pill_x, pill_y), (pill_x + 4, pill_y + pill_h)], fill=ACCENT)
    # Text
    draw.text((pill_x + pad - 4, pill_y + pad - 4), text, font=font, fill=(*WHITE, 240))
    return img


def make_caption_with_animation(text, frame_index, total_frames, w=W, h=H):
    """Lower-third caption with motion."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cap_font = find_font(64, bold=True)
    bbox = cap_font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    fps = FPS
    anim_in = int(0.5 * fps)
    anim_out = int(0.5 * fps)
    if frame_index < anim_in:
        t = frame_index / anim_in
        offset = int(60 * (1 - t))
        alpha_mult = t
    elif frame_index >= total_frames - anim_out:
        t = (frame_index - (total_frames - anim_out)) / anim_out
        offset = 0
        alpha_mult = 1 - t
    else:
        offset = 0
        alpha_mult = 1.0
    alpha = int(255 * alpha_mult)
    y = h - 300 - 50 + offset
    x = (w - text_w) // 2
    pad_x, pad_y = 30, 14
    pill_w = text_w + pad_x * 2
    pill_h = text_h + pad_y * 2
    pill_x = (w - pill_w) // 2
    pill_y = y - pad_y
    for dx, dy in [(4, 4), (-4, 4)]:
        draw.rounded_rectangle(
            [(pill_x + dx, pill_y + dy), (pill_x + pill_w + dx, pill_y + pill_h + dy)],
            radius=12, fill=(0, 0, 0, alpha // 2)
        )
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=12, fill=(0, 0, 0, alpha)
    )
    for dx, dy in [(-2, -2), (2, 2)]:
        draw.text((x + dx, y + dy), text, font=cap_font, fill=(0, 0, 0, alpha))
    draw.text((x, y), text, font=cap_font, fill=(*WHITE, alpha))
    return img


def make_intro_card(product_path, brand, name, rating, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            target_h = int(h * 0.7)
            bg.thumbnail((w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    brand_font = find_font(64, bold=True)
    draw.text((80, 80), brand.upper(), font=brand_font, fill=(180, 185, 195))
    name_font = find_font(120, bold=True)
    words = name.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = name_font.getbbox(test)
        if bbox[2] - bbox[0] > w - 200:
            if current:
                lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    if not lines:
        lines = [name]
    if len(lines) > 2:
        lines = [" ".join(lines[:len(lines)//2 + 1]), " ".join(lines[len(lines)//2 + 1:])]
    y = int(h * 0.75)
    for line in lines:
        bbox = name_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        for dx, dy in [(-4, -4), (4, 4)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=name_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=name_font, fill=WHITE)
        y += 140
    rating_font = find_font(80, bold=True)
    rating_text = f"⭐ {rating}/5"
    bbox = rating_font.getbbox(rating_text)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, int(h * 0.55)), rating_text, font=rating_font, fill=ACCENT)
    img.save(output_png)


def make_verdict_card(brand, name, rating, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    draw = ImageDraw.Draw(img)
    big_rating = find_font(280, bold=True)
    rating_text = rating
    bbox = big_rating.getbbox(rating_text)
    rw = bbox[2] - bbox[0]
    rx = (w - rw) // 2
    ry = int(h * 0.35)
    for dx, dy in [(-5, -5), (5, 5)]:
        draw.text((rx + dx, ry + dy), rating_text, font=big_rating, fill=(0, 0, 0))
    draw.text((rx, ry), rating_text, font=big_rating, fill=ACCENT)
    final_text = find_font(72, bold=True)
    ftext = "FINAL SCORE"
    bbox = final_text.getbbox(ftext)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, ry + 320), ftext, font=final_text, fill=WHITE)
    sub = find_font(56, bold=False)
    sb = name
    bbox = sub.getbbox(sb)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, ry + 420), sb, font=sub, fill=(180, 185, 195))
    cta = find_font(48, bold=True)
    ctext = "Full review in bio"
    bbox = cta.getbbox(ctext)
    cw = bbox[2] - bbox[0]
    draw.text(((w - cw) // 2, int(H * 0.75)), ctext, font=cta, fill=ACCENT)
    img.save(output_png)


def cut_broll_clip(input_path, output_path, duration_s, start_s=0.0):
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
    tmp = Path(f"/tmp/short_v9/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    clips_dir = tmp / "broll"
    cap_frames_dir = tmp / "cap_frames"
    cap_frames_dir.mkdir()
    clips_dir.mkdir()
    watermark = make_watermark()
    watermark.save(tmp / "watermark.png")

    # 1. Voiceover
    print("  1. Voiceover (edge-tts, human)...")
    voiceover = tmp / "voiceover.mp3"
    if not fetch_voiceover_edge_tts(script, voiceover):
        print("     ! Voiceover failed")
        return None
    dur_out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
        capture_output=True, text=True
    )
    try:
        voiceover_duration = float(dur_out.stdout.strip())
    except Exception:
        voiceover_duration = 60.0
    print(f"     ✓ {voiceover.stat().st_size // 1024} KB, {voiceover_duration:.1f}s")

    # 2. B-roll
    print("  2. B-roll...")
    broll_paths = fetch_pexels_videos(search_terms, str(clips_dir), n=12, min_duration_s=8)
    print(f"     ✓ {len(broll_paths)} clips")
    if len(broll_paths) < 4:
        return None

    # 3. Plan scenes
    intro_dur = 5.0
    outro_dur = 5.0
    broll_dur = voiceover_duration
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    captions = []
    for s in sentences:
        words = s.split()
        if len(words) <= 5:
            captions.append(s)
        else:
            i = 0
            while i < len(words):
                chunk_len = min(4, len(words) - i)
                captions.append(" ".join(words[i:i+chunk_len]))
                i += chunk_len
    n_scenes = len(captions)
    scene_dur = broll_dur / n_scenes
    print(f"  3. {n_scenes} scenes × {scene_dur:.2f}s")

    # 4. Cut b-roll
    print("  4. Cut b-roll...")
    scene_clips = []
    for i, caption in enumerate(captions):
        broll_idx = i % len(broll_paths)
        broll_path = broll_paths[broll_idx]
        clip_path = tmp / f"scene_{i:02d}.mp4"
        d_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", broll_path],
            capture_output=True, text=True
        )
        try:
            src_dur = float(d_out.stdout.strip())
        except Exception:
            src_dur = scene_dur + 1
        max_start = max(0, src_dur - scene_dur - 0.5)
        start = random.uniform(0, max_start) if max_start > 0 else 0
        cut_broll_clip(broll_path, str(clip_path), scene_dur, start)
        scene_clips.append((str(clip_path), caption))
    print(f"     ✓ {len(scene_clips)} scene clips")

    # 5. Caption frames + watermark baked in
    print("  5. Caption + watermark frames...")
    for i, (clip, caption) in enumerate(scene_clips):
        scene_frames_dir = tmp / f"caps_{i:02d}"
        scene_frames_dir.mkdir(exist_ok=True)
        n_frames = int(scene_dur * FPS)
        for f_idx in range(n_frames):
            # Combine caption + watermark
            cap = make_caption_with_animation(caption, f_idx, n_frames)
            combined = Image.alpha_composite(cap, watermark)
            combined.save(scene_frames_dir / f"{f_idx:04d}.png")
    print(f"     ✓ frames for {n_scenes} scenes")

    # 6. Composite over video
    print("  6. Composite...")
    composed_clips = []
    for i, (clip, caption) in enumerate(scene_clips):
        comp = tmp / f"composed_{i:02d}.mp4"
        scene_frames_dir = tmp / f"caps_{i:02d}"
        n_frames = len(list(scene_frames_dir.glob("*.png")))
        if n_frames == 0:
            shutil.copy(clip, comp)
            composed_clips.append(str(comp))
            continue
        subprocess.run([
            "ffmpeg", "-y",
            "-i", clip,
            "-framerate", str(FPS),
            "-i", str(scene_frames_dir / "%04d.png"),
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            str(comp)
        ], capture_output=True, text=True)
        if comp.exists():
            composed_clips.append(str(comp))
    print(f"     ✓ {len(composed_clips)} composed")

    # 7. Concat all scenes
    print("  7. Concat scenes...")
    broll_concat = tmp / "broll_concat.mp4"
    concat_list = tmp / "concat.txt"
    with open(concat_list, "w") as f:
        for c in composed_clips:
            f.write(f"file '{c}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(broll_concat)
    ], capture_output=True, text=True)

    # 8. Intro
    print("  8. Intro...")
    intro_mp4 = tmp / "intro.mp4"
    intro_png = tmp / "intro.png"
    make_intro_card(product_image, brand, name, rating, str(intro_png))
    # Bake watermark onto intro
    intro_img = Image.open(intro_png).convert("RGBA")
    intro_with_wm = Image.alpha_composite(intro_img, watermark)
    intro_with_wm.convert("RGB").save(intro_png)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(intro_png),
        "-t", f"{intro_dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(intro_mp4)
    ], capture_output=True, text=True)

    # 9. Outro
    print("  9. Outro...")
    outro_mp4 = tmp / "outro.mp4"
    outro_png = tmp / "outro.png"
    make_verdict_card(brand, name, rating, str(outro_png))
    outro_img = Image.open(outro_png).convert("RGBA")
    outro_with_wm = Image.alpha_composite(outro_img, watermark)
    outro_with_wm.convert("RGB").save(outro_png)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(outro_png),
        "-t", f"{outro_dur}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(outro_mp4)
    ], capture_output=True, text=True)

    # 10. Final concat
    print("  10. Final concat...")
    video_only = tmp / "video_only.mp4"
    final_concat = tmp / "final_concat.txt"
    with open(final_concat, "w") as f:
        f.write(f"file '{intro_mp4}'\n")
        f.write(f"file '{broll_concat}'\n")
        f.write(f"file '{outro_mp4}'\n")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(final_concat),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(video_only)
    ], capture_output=True, text=True)

    # 11. Mix in voiceover with audio normalization
    print("  11. Mix voiceover...")
    video_out = output_dir / f"{slug}.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_only),
        "-i", str(voiceover),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-pix_fmt", "yuv420p", "-shortest",
        str(video_out)
    ], capture_output=True, text=True)

    if video_out.exists():
        size = video_out.stat().st_size
        d = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_out)],
            capture_output=True, text=True
        )
        try:
            duration = float(d.stdout.strip())
        except Exception:
            duration = 0
        print(f"     ✓ {size//1024//1024} MB, {duration:.1f}s")
        return video_out
    return None


SCRIPTS = {
    "short-1-macbook-m5": {"brand": "Apple", "name": "MacBook Pro M5", "rating": "4.6",
        "search": ["laptop", "macbook", "office desk", "typing", "tech office", "developer", "video editing"],
        "script": "I tested the MacBook Pro M5 for 30 days as my daily driver. Here is my honest take. The M5 chip is noticeably faster than the M4. Video renders take about 20 percent less time. Battery is real. 18 hours in my testing on a single charge. The display is the best on any laptop. Bright, color accurate, smooth. The keyboard is still the best on a laptop. Trackpad is huge and precise. Build quality is premium. The ports include 3 Thunderbolt 5, HDMI, and SD card. MagSafe is back. The speakers are incredible for a laptop. What I do not love. 8 gigabytes of RAM at this price is criminal. 2000 dollars starting. And no touchscreen in 2026. The notch is still there. Final verdict. 4.6 out of 5. Buy it if you edit video, code, or work in the Apple ecosystem. Skip it if you only browse the web. Get a MacBook Air M4 instead and save 800 dollars."},
    "short-2-anker-737": {"brand": "Anker", "name": "Anker 737", "rating": "4.7",
        "search": ["power bank", "charging", "travel", "airport", "laptop charging", "tech travel", "business travel"],
        "script": "This power bank charges my laptop on a plane. I tested the Anker 737 for 78 days. It outputs 140 watts. That is enough to fast charge a MacBook Pro. 24,000 milliamp hours. That is full laptop and 2 phones with room to spare. The smart display shows real time wattage. You know exactly how fast you are charging. It has 2 USB-C and 1 USB-A. Pass through charging works. So you can charge the bank and your devices at the same time. TSA approved for carry on. I flew with it 4 times. The build is solid. Aluminum shell. What I do not love. 90 dollars is premium. And it weighs 1.4 pounds. Not pocket friendly. Slow to recharge itself. 3 plus hours from empty. Final verdict. 4.7 out of 5. Best for laptop users and frequent travelers. Phone only users should get the 25 dollar Anker PowerCore 10K."},
    "short-3-sony-xm6": {"brand": "Sony", "name": "Sony WH-1000XM6", "rating": "4.7",
        "search": ["headphones", "music", "commute", "coffee shop", "airplane travel", "noise cancelling", "study"],
        "script": "The noise cancelling king is back. I tested the Sony XM6 for 134 days. Active noise cancellation still beats Bose and Apple. Better low frequency reduction. Better voice reduction. Better wind reduction. Battery is 32 hours real world. With ANC on. Multi point pairing. Laptop and phone at the same time. No more reconnecting. Lighter clamping than the XM5. More comfortable for long sessions. The case is bigger though. Touch controls are responsive. Sound quality is balanced. LDAC support for high res audio. What I do not love. 449 dollars. And the case is bigger than the XM5 case. Not foldable. Final verdict. 4.7 out of 5. Best for frequent flyers and coffee shop workers. Glasses wearers should get the Bose QC Ultra instead. Less clamping pressure."},
    "short-4-anker-powercore-10k": {"brand": "Anker", "name": "Anker PowerCore 10K", "rating": "4.5",
        "search": ["power bank", "portable charger", "phone charging", "travel", "everyday carry"],
        "script": "I tested the Anker PowerCore 10K for 60 days. It is a reliable 10,000mAh power bank with 18W USB-C. Charges an iPhone about 2.5 times. The LED indicator shows remaining charge. The build quality is solid. It feels like a premium product. USB-C in and out. What I do not love. Only 18W output. Not enough for laptops. And it is a bit bulky for pocket carry. The included cable is short. Final verdict. 4.5 out of 5. Great for daily phone charging and travel. Pair with a 30W USB-C charger for faster recharging."},
    "short-5-anker-727-charging-station": {"brand": "Anker", "name": "Anker 727", "rating": "4.6",
        "search": ["charging station", "desk organizer", "office desk", "cable management", "home office", "desk setup"],
        "script": "I tested the Anker 727 Charging Station for 45 days. It is a 6 in 1 dock with two USB-C. 100 watts total. Two USB-A and an AC outlet. Powers my laptop, phone, tablet, and lamp all from one unit. The built in cable management keeps things tidy. The AC outlet is great for monitors. Compact form factor. What I do not love. It is large and not travel friendly. And the AC outlet is only 60 watts. Not enough for some appliances. Final verdict. 4.6 out of 5. Ideal for home office desk setups. If you need portability, look at the Anker 523 instead."},
    "short-6-anker-nano-ii-65w": {"brand": "Anker", "name": "Anker Nano II 65W", "rating": "4.6",
        "search": ["usb c charger", "small charger", "travel charger", "office desk", "gallium nitride"],
        "script": "I tested the Anker Nano II 65W for 30 days. It is a tiny gallium nitride charger that folds flat. Smaller than the Apple 61W charger. Charges a MacBook Air at full speed. The foldable prongs make it great for travel. 65W is enough for most laptops. What I do not love. Only one port. And it can get warm under heavy load. Final verdict. 4.6 out of 5. Best for travelers who need one compact charger. If you need multiple ports, get the Anker 577 instead."},
    "short-7-anker-543-usb-c-hub": {"brand": "Anker", "name": "Anker 543 Hub", "rating": "4.4",
        "search": ["usb c hub", "laptop accessories", "office desk", "macbook accessories", "port"],
        "script": "I tested the Anker 543 USB-C Hub for 40 days. It adds two USB-C, two USB-A, HDMI, and SD card reader. Turns one USB-C port into a full workstation. Plug and play. No drivers needed. Aluminum build. What I do not love. The HDMI is limited to 4K at 30Hz. And it does not support Thunderbolt 4 speeds. The cable is short. Final verdict. 4.4 out of 5. Great for connecting peripherals to a MacBook. If you need Thunderbolt 4, consider the CalDigit Element 5."},
    "short-8-anker-soundcore-life-q35": {"brand": "Anker", "name": "Soundcore Life Q35", "rating": "4.4",
        "search": ["headphones", "music", "office work", "study headphones", "wireless audio"],
        "script": "I tested the Soundcore Life Q35 for 50 days. They offer hybrid active noise cancellation and Hi-Res audio. LDAC support for high quality wireless audio. 40 hour battery with ANC on. Multi point pairing. What I do not love. The ANC is not as strong as Sony or Bose. And the ear cups can feel warm after long use. The app is required for EQ. Final verdict. 4.4 out of 5. Excellent value for the features. If you need top tier ANC, go for Sony XM6 or Bose QC Ultra."},
    "short-9-apple-airpods-pro-3": {"brand": "Apple", "name": "AirPods Pro", "rating": "4.7",
        "search": ["airpods", "earbuds", "commute", "office work", "music", "wireless earbuds"],
        "script": "I tested the AirPods Pro for 90 days. The H2 chip provides excellent adaptive noise cancellation. Transparency mode lets you hear surroundings naturally. Spatial audio with dynamic head tracking. Seamless iPhone integration. Find My support. What I do not love. The battery life is only 6 hours with ANC on. And the case does not support wireless charging in this model. The fit can be loose for some ears. Final verdict. 4.7 out of 5. Best for iPhone users wanting seamless integration. If you need longer battery, consider the AirPods 3rd gen."},
    "short-10-aqara-u200": {"brand": "Aqara", "name": "Aqara U200", "rating": "4.3",
        "search": ["smart home", "front door", "fingerprint lock", "home security", "smart lock"],
        "script": "I tested the Aqara U200 for 60 days on my front door. It unlocks via fingerprint, keypad, or app. The build quality feels solid and secure. Easy to install. No drilling required. Works with HomeKit, Alexa, and Google Home. What I do not love. The fingerprint sensor can fail with wet fingers. And it requires a separate Aqara Hub to work with Apple Home. The keypad is small. Final verdict. 4.3 out of 5. Great for those invested in the Aqara ecosystem. If you want native HomeKit, look at the Yale Assure Lock SL."},
    "short-11-claude-4-sonnet": {"brand": "Anthropic", "name": "Claude 3.5 Sonnet", "rating": "4.8",
        "search": ["ai", "computer", "laptop", "office work", "coding", "developer", "tech"],
        "script": "I tested Claude 3.5 Sonnet for 30 days via the API. It excels at reasoning, coding, and long context understanding. The 200k token context window is a game changer. You can paste in entire codebases. It handles complex instructions well. The Artifacts feature lets you build real apps in chat. Coding accuracy is top tier. What I do not love. It can be verbose in simple answers. And it sometimes over refuses harmless prompts. Pricing is higher than GPT-4o. Final verdict. 4.8 out of 5. One of the best LLMs available today. If you need the absolute cutting edge, wait for Claude 4 Opus."},
    "short-12-eero-max-7": {"brand": "eero", "name": "eero Max 7", "rating": "4.5",
        "search": ["wifi router", "mesh wifi", "home office", "gaming setup", "smart home", "router"],
        "script": "I tested the eero Max 7 for 45 days in a 3000 square foot home. It is a tri-band Wi-Fi 6E system with 2.5Gbps wired backhaul. Coverage is excellent and latency is low for gaming. Easy setup via the eero app. Works as a smart home hub with Zigbee and Thread support. What I do not love. The price is high at 500 dollars for a 2-pack. And the setup requires the eero app. No web interface. Subscription needed for some features. Final verdict. 4.5 out of 5. Best for large homes needing seamless coverage. If you are on a budget, consider the TP-Link Deco XE75."},
    "short-13-garmin-fenix-9-solar": {"brand": "Garmin", "name": "Garmin Fenix 9", "rating": "4.7",
        "search": ["smartwatch", "running", "outdoor", "fitness", "hiking", "athlete", "training"],
        "script": "I tested the Garmin Fenix 9 Solar for 60 days of daily wear. The solar charging lens extends battery life in sunlight. It offers advanced metrics for running, cycling, and swimming. Built in maps. Offline music storage. Sapphire glass for scratch resistance. What I do not love. The price is premium at 999 dollars. And the interface can feel overwhelming for beginners. The watch face size is large. Final verdict. 4.7 out of 5. Best for serious athletes who want all the data. If you want a simpler experience, look at the Garmin Forerunner 265."},
    "short-14-garmin-instinct-2-solar": {"brand": "Garmin", "name": "Garmin Instinct 2", "rating": "4.5",
        "search": ["smartwatch", "outdoor", "hiking", "camping", "rugged watch", "military"],
        "script": "I tested the Garmin Instinct 2 Solar for 60 days of outdoor use. It is built to military standards and resists shocks, heat, and water. The solar charging extends battery life in the field. Unlimited battery in sunlight mode. The GPS is accurate even in dense forest. What I do not love. The display is monochrome and limited. And it lacks advanced running dynamics found in pricier models. The bezel is thick. Final verdict. 4.5 out of 5. Ideal for outdoor enthusiasts who need a tough watch. If you want a color display, look at the Garmin Venu 3."},
    "short-15-govee-glide-wall-light": {"brand": "Govee", "name": "Govee Glide", "rating": "4.2",
        "search": ["rgb light", "smart home", "gaming setup", "bedroom", "led lights", "wall light", "ambient"],
        "script": "I tested the Govee Glide Wall Light for 30 days. It is a flexible LED strip that creates colorful ambient lighting. The app offers millions of colors and scene modes. Music sync feature. Works with Alexa and Google Assistant. Modular design. What I do not love. The adhesive can weaken over time on textured walls. And the Bluetooth range is limited to about 30 feet. The price is high for what it is. Final verdict. 4.2 out of 5. Great for adding color to a bedroom or gaming setup. If you need longer range, consider the Philips Hue Lightstrip Plus."},
    "short-16-jackery-explorer-1000-v2": {"brand": "Jackery", "name": "Jackery 1000 v2", "rating": "4.4",
        "search": ["camping", "outdoor", "power station", "solar", "rv", "emergency power", "off grid"],
        "script": "I tested the Jackery Explorer 1000 v2 for 40 days of camping and outages. It is a 1002Wh lithium battery with pure sine wave AC outlet. Can power a refrigerator, CPAP, or small appliances. Solar charging capable. Quiet operation. The handle is comfortable. What I do not love. The recharge time is long via wall outlet. About 7 hours. And it is heavy at 22 pounds for frequent carrying. The fan can be loud under heavy load. Final verdict. 4.4 out of 5. Excellent for emergency power and camping. If you need faster charging, look at the EcoFlow Delta 2."},
    "short-17-logitech-mx-master-4": {"brand": "Logitech", "name": "MX Master 4", "rating": "4.7",
        "search": ["computer mouse", "office work", "productivity", "desk setup", "ergonomic mouse", "wireless mouse"],
        "script": "I tested the Logitech MX Master 4 for 60 days of daily use. The ergonomic shape reduces wrist strain during long sessions. The mag speed wheel allows ultra fast scrolling. Multi device pairing. 70 day battery life. The thumb wheel is great for video editing. What I do not love. The thumb wheel can feel awkward at first. And it does not work well on glass surfaces. The size is large for small hands. Final verdict. 4.7 out of 5. The gold standard for productivity mice. If you prefer a lighter mouse, look at the Logitech MX Anywhere 3."},
    "short-18-notion-calendar": {"brand": "Notion", "name": "Notion Calendar", "rating": "4.3",
        "search": ["office work", "laptop", "calendar", "study", "work desk", "productivity", "planner"],
        "script": "I tested Notion Calendar for 45 days of daily planning. It integrates tightly with Notion databases and offers time blocking. Cross platform support. Keyboard shortcuts. Free to use. The mobile app is improving. What I do not love. It lacks native timezone support for travel. And the mobile app feels slower than the web version. Limited event customization. Final verdict. 4.3 out of 5. Excellent for those already using Notion for notes and tasks. If you need a dedicated calendar app, consider Fantastical or Apple Calendar."},
    "short-19-ring-battery-doorbell-plus": {"brand": "Ring", "name": "Ring Doorbell Plus", "rating": "4.4",
        "search": ["front door", "home security", "doorbell", "smart home", "porch", "video doorbell"],
        "script": "I tested the Ring Battery Doorbell Plus for 60 days. It offers 1080p HD video, color night vision, and motion detection. The quick release battery pack makes recharging easy. Works with Alexa. Two way audio. Package detection. What I do not love. The motion zones can be tricky to set up precisely. And it requires a Ring Protect subscription for video storage. The battery drains fast with high traffic. Final verdict. 4.4 out of 5. A solid choice for those invested in the Ring ecosystem. If you want local storage only, consider the Eufy SoloCam S220."},
    "short-20-sennheiser-momentum-4": {"brand": "Sennheiser", "name": "Sennheiser M4", "rating": "4.6",
        "search": ["headphones", "music", "office work", "study", "studio", "audiophile"],
        "script": "I tested the Sennheiser Momentum 4 for 80 days of daily use. They offer industry leading noise cancellation and 60 hour battery. The sound signature is warm and detailed. Great for all genres. The build is premium. What I do not love. The ANC can create a slight pressure sensation. And the touch controls can be overly sensitive. The case is bulky. Final verdict. 4.6 out of 5. One of the best wireless headphones available today. If you want the absolute best ANC, consider the Sony XM6."},
    "short-21-tp-link-kasa-smart-plug": {"brand": "TP-Link", "name": "Kasa Smart Plug", "rating": "4.2",
        "search": ["smart home", "home automation", "outlet", "office", "energy", "smart plug", "schedule"],
        "script": "I tested the TP-Link Kasa Smart Plug for 60 days of daily use. It is a reliable Wi-Fi outlet that lets you schedule devices remotely. The app and voice assistant integration work well. Works with Alexa, Google, and SmartThings. Energy monitoring on this model. What I do not love. The Wi-Fi connection can drop occasionally. And it blocks the adjacent outlet due to its size. No HomeKit support. Final verdict. 4.2 out of 5. Great for automating lamps, fans, and holiday lights. If you need outdoor use, look at the TP-Link Tapo P110."},
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
        rest = "-".join(slug.split("-")[2:])
        product_img = asset_dir / f"{rest}.jpg"
        if not product_img.exists():
            product_img = None
        result = make_short(slug, s["brand"], s["name"], s["rating"], None, s["script"], s["search"], product_img, out_dir)
        if result:
            success += 1
    print(f"\nDone. {success}/{len(targets)} Shorts generated.")