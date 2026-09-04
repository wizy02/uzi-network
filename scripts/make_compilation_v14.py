#!/usr/bin/env python3
"""
Uzi Network — COMPILATION v14 with REAL product photos
Each product gets:
- 5s: Full-screen product photo with #X of 5, brand, name, rating
- 4-5s: B-roll shot 1
- 4-5s: B-roll shot 2
- 4-5s: B-roll shot 3
- 5s: Outro card with all links
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
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

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


def fetch_voiceover_edge_tts(text, output_mp3, voice=VOICE, rate="+0%", pitch="-2Hz"):
    import edge_tts
    async def run():
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(output_mp3))
    asyncio.run(run())
    return output_mp3.exists() and output_mp3.stat().st_size > 1000


def generate_cinematic_ambient(duration_s, output_mp3):
    seed = random.randint(1, 10000)
    random.seed(seed)
    root_hz = random.choice([110, 130.81, 146.83, 164.81, 174.61, 196, 220])
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.18*sin(2*PI*{root_hz}*t)+0.10*sin(2*PI*{root_hz*1.005}*t)+0.08*sin(2*PI*{root_hz*0.995}*t)':d={duration_s}:s=44100",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.08*sin(2*PI*{root_hz*2}*t + 2*sin(2*PI*0.3*t))+0.06*sin(2*PI*{root_hz*2*1.003}*t)':d={duration_s}:s=44100",
        "-filter_complex",
        "[0:a][1:a]amix=inputs=2:duration=longest,volume=0.5,afade=t=in:st=0:d=2,afade=t=out:st={duration_s-3}:d=3[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(output_mp3)
    ]
    subprocess.run(cmd, capture_output=True, text=True)
    return Path(output_mp3).exists() and Path(output_mp3).stat().st_size > 1000


def fetch_pexels_videos(query, output_dir, n=20, min_duration_s=8):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    all_paths = []
    queries = query if isinstance(query, list) else [query]
    for q in queries:
        if len(all_paths) >= n:
            break
        url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode({'query': q, 'per_page': 30, 'orientation': 'portrait'})}"
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
                portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0) and f.get("height", 0) >= 1080]
                landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1920]
                landscape_good = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
                mp4_files = portrait or landscape_hd or landscape_good or [f for f in files if f.get("file_type") == "video/mp4"]
                if not mp4_files:
                    continue
                candidates = sorted(mp4_files, key=lambda f: -f.get("width", 0) * f.get("height", 0))
                best = None
                for c in candidates:
                    if c.get("width", 0) * c.get("height", 0) <= 1920 * 1080 * 1.5:
                        best = c
                        break
                if not best:
                    best = candidates[-1] if candidates else None
                if not best:
                    continue
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


def make_watermark_topright(w=W, h=H):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = find_font(28, bold=True)
    text = "@uzinetwork"
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pad = 14
    pill_x = w - text_w - pad * 2 - 40
    pill_y = 40
    pill_w = text_w + pad * 2
    pill_h = text_h + pad * 2
    for dx, dy in [(3, 3)]:
        draw.rounded_rectangle(
            [(pill_x + dx, pill_y + dy), (pill_x + pill_w + dx, pill_y + pill_h + dy)],
            radius=8, fill=(0, 0, 0, 100)
        )
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=8, fill=(0, 0, 0, 180)
    )
    draw.rectangle([(pill_x, pill_y), (pill_x + 4, pill_y + pill_h)], fill=ACCENT)
    draw.text((pill_x + pad - 4, pill_y + pad - 4), text, font=font, fill=(*WHITE, 240))
    return img


def make_product_photo_frame(product_path, brand, name, rating, product_idx, total_products, frame_index, total_frames, w=W, h=H):
    """Full-screen product photo with brand pill, name overlay, and #X of Y badge."""
    img = Image.new("RGB", (w, h), (13, 15, 20))
    if product_path and Path(product_path).exists():
        try:
            # Load product image
            bg = Image.open(product_path).convert("RGB")
            # Center it in the upper 60% of the screen
            target_h = int(h * 0.6)
            target_w = int(w * 0.85)
            bg.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            # Background fill (subtle gradient)
            img.paste(bg, (x, y))
            # Slight dark overlay for contrast
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 40))
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    # #1 of 5 badge top center
    num_font = find_font(64, bold=True)
    num_text = f"#{product_idx} OF {total_products}"
    bbox = num_font.getbbox(num_text)
    nw = bbox[2] - bbox[0]
    pad_x, pad_y = 32, 14
    pill_w = nw + pad_x * 2
    pill_h = bbox[3] - bbox[1] + pad_y * 2
    pill_x = (w - pill_w) // 2
    pill_y = 80
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=20, fill=ACCENT
    )
    draw.text((pill_x + pad_x, pill_y + pad_y - 4), num_text, font=num_font, fill=(13, 15, 20))
    # Brand below photo
    brand_font = find_font(48, bold=True)
    brand_y = int(h * 0.7)
    bbox = brand_font.getbbox(brand.upper())
    bw = bbox[2] - bbox[0]
    # Shadow
    for dx, dy in [(-3, -3), (3, 3)]:
        draw.text(((w - bw) // 2 + dx, brand_y + dy), brand.upper(), font=brand_font, fill=(0, 0, 0))
    draw.text(((w - bw) // 2, brand_y), brand.upper(), font=brand_font, fill=(200, 200, 200))
    # Product name
    name_font = find_font(76, bold=True)
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
    if len(lines) > 2:
        lines = lines[:2]
    y = brand_y + 70
    for line in lines:
        bbox = name_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=name_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=name_font, fill=WHITE)
        y += 90
    # Rating
    rating_font = find_font(56, bold=True)
    rtext = f"⭐ {rating}/5"
    bbox = rating_font.getbbox(rtext)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, y + 20), rtext, font=rating_font, fill=ACCENT)
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
    anim_in = int(0.3 * fps)
    anim_out = int(0.3 * fps)
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
    y = h - 320 - 50 + offset
    x = (w - text_w) // 2
    pad_x, pad_y = 32, 16
    pill_w = text_w + pad_x * 2
    pill_h = text_h + pad_y * 2
    pill_x = (w - pill_w) // 2
    pill_y = y - pad_y
    for dx, dy in [(4, 4)]:
        draw.rounded_rectangle(
            [(pill_x + dx, pill_y + dy), (pill_x + pill_w + dx, pill_y + pill_h + dy)],
            radius=12, fill=(0, 0, 0, alpha)
        )
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=12, fill=(0, 0, 0, alpha)
    )
    draw.rectangle([(pill_x, pill_y), (pill_x + 4, pill_y + pill_h)], fill=ACCENT)
    for dx, dy in [(-2, -2), (2, 2)]:
        draw.text((x + dx, y + dy), text, font=cap_font, fill=(0, 0, 0, alpha))
    draw.text((x, y), text, font=cap_font, fill=(*WHITE, alpha))
    return img


def make_intro_card(title_lines, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    draw = ImageDraw.Draw(img)
    hook_font = find_font(110, bold=True)
    y = int(h * 0.35)
    for line in title_lines:
        bbox = hook_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        if lw > w - 100:
            hook_font = find_font(80, bold=True)
            bbox = hook_font.getbbox(line)
            lw = bbox[2] - bbox[0]
        for dx, dy in [(-5, -5), (5, 5)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=hook_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=hook_font, fill=WHITE)
        y += 130
    sub_font = find_font(56, bold=True)
    sub = "@uzinetwork"
    bbox = sub_font.getbbox(sub)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, int(h * 0.85)), sub, font=sub_font, fill=ACCENT)
    img.save(output_png)


def make_outro_card(total_products, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    draw = ImageDraw.Draw(img)
    title_font = find_font(96, bold=True)
    title = f"ALL {total_products} LINKS"
    bbox = title_font.getbbox(title)
    tw = bbox[2] - bbox[0]
    for dx, dy in [(-4, -4), (4, 4)]:
        draw.text(((w - tw) // 2 + dx, int(h * 0.3) + dy), title, font=title_font, fill=(0, 0, 0))
    draw.text(((w - tw) // 2, int(h * 0.3)), title, font=title_font, fill=ACCENT)
    sub_font = find_font(56, bold=True)
    sub = "in bio"
    bbox = sub_font.getbbox(sub)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, int(h * 0.45)), sub, font=sub_font, fill=WHITE)
    url_font = find_font(40, bold=True)
    url = "uzi.network.store"
    bbox = url_font.getbbox(url)
    uw = bbox[2] - bbox[0]
    draw.text(((w - uw) // 2, int(h * 0.6)), url, font=url_font, fill=ACCENT)
    cta_font = find_font(48, bold=True)
    cta = "Tap to get the full reviews"
    bbox = cta_font.getbbox(cta)
    cw = bbox[2] - bbox[0]
    draw.text(((w - cw) // 2, int(h * 0.75)), cta, font=cta_font, fill=WHITE)
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


def make_product_photo_video(product_path, brand, name, rating, product_idx, total_products, output_path, duration_s=5.0):
    """Render the product photo as a still video segment with overlay text."""
    if not product_path or not Path(product_path).exists():
        return False
    tmp_dir = Path("/tmp/short_v14_frames")
    tmp_dir.mkdir(exist_ok=True, parents=True)
    # Render N frames
    n_frames = int(duration_s * FPS)
    for i in range(n_frames):
        frame = make_product_photo_frame(product_path, brand, name, rating, product_idx, total_products, i, n_frames)
        frame.save(tmp_dir / f"prod_{product_idx}_{i:04d}.jpg", quality=95)
    # Encode
    subprocess.run([
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(tmp_dir / f"prod_{product_idx}_%04d.jpg"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(output_path)
    ], capture_output=True, text=True)
    # Cleanup frames
    for f in tmp_dir.glob(f"prod_{product_idx}_*.jpg"):
        f.unlink()
    return Path(output_path).exists() and Path(output_path).stat().st_size > 0


def make_compilation_short(slug, title_lines, products, output_dir, asset_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v14/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    clips_dir = tmp / "broll"
    clips_dir.mkdir()
    watermark = make_watermark_topright()
    watermark.save(tmp / "watermark.png")

    # 1. Voiceover
    intro_text = f"Here are the {len(products)} best gadgets you can buy right now. I tested every single one. The links are in bio."
    outro_text = f"All {len(products)} links are in bio. Pick the one that fits your life. Like and follow for more."
    product_lines = [p["line"] for p in products]
    full_script = intro_text + " " + " ".join(product_lines) + " " + outro_text
    print(f"  1. Voiceover ({len(full_script)} chars)...")
    voiceover = tmp / "voiceover.mp3"
    if not fetch_voiceover_edge_tts(full_script, voiceover):
        return None
    dur_out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(voiceover)],
        capture_output=True, text=True
    )
    voiceover_duration = float(dur_out.stdout.strip())
    print(f"     ✓ {voiceover.stat().st_size // 1024} KB, {voiceover_duration:.1f}s")

    # 2. B-roll per product
    print("  2. B-roll per product...")
    all_search = []
    for p in products:
        all_search.extend(p["search"])
    all_clips = fetch_pexels_videos(all_search, str(clips_dir), n=30, min_duration_s=8)
    print(f"     ✓ {len(all_clips)} total clips")
    if len(all_clips) < 4:
        return None
    product_broll = {}
    for i, p in enumerate(products):
        n = max(3, len(all_clips) // len(products))
        product_broll[p["name"]] = [all_clips[j] for j in range(i, len(all_clips), max(1, len(all_clips) // len(products)))][:n]

    # 3. Music
    print("  3. Background music...")
    music = tmp / "music.mp3"
    if not generate_cinematic_ambient(int(voiceover_duration + 10), music):
        music = None
    if music:
        print(f"     ✓ {music.stat().st_size // 1024} KB")

    # 4. Plan timing
    intro_dur = 4.0
    outro_dur = 4.0
    photo_dur = 5.0  # product photo stays for 5s
    # Total b-roll per product = product_dur - photo_dur
    product_dur = (voiceover_duration - 8.0) / len(products)
    broll_per_product = max(6.0, product_dur - photo_dur)
    n_shots = 3
    shot_dur = broll_per_product / n_shots
    print(f"  4. {len(products)} products × photo {photo_dur}s + 3 shots × {shot_dur:.1f}s")

    # 5. Build per-product clips
    print("  5. Build product segments...")
    product_segments = []  # List of clip paths per product
    for prod_idx, p in enumerate(products):
        # 5a. Product photo segment
        photo_clip = tmp / f"photo_{prod_idx:02d}.mp4"
        product_img_path = Path(asset_dir) / f"{p['slug']}.jpg"
        if product_img_path.exists():
            make_product_photo_video(str(product_img_path), p["brand"], p["name"], p["rating"], prod_idx + 1, len(products), str(photo_clip), photo_dur)
            product_segments.append([str(photo_clip)])
            print(f"     ✓ {p['name']}: photo + {n_shots} shots")
        else:
            print(f"     ! {p['name']}: no product image at {product_img_path}")
            product_segments.append([])
            continue
        # 5b. B-roll shots
        prod_broll = product_broll.get(p["name"], all_clips)
        for shot_idx in range(n_shots):
            broll_idx = (prod_idx * n_shots + shot_idx) % len(prod_broll)
            broll_path = prod_broll[broll_idx]
            clip_path = tmp / f"broll_{prod_idx:02d}_{shot_idx:02d}.mp4"
            d_out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default:noprint_wrappers=1:nokey=1", broll_path],
                capture_output=True, text=True
            )
            try:
                src_dur = float(d_out.stdout.strip())
            except Exception:
                src_dur = shot_dur + 1
            max_start = max(0, src_dur - shot_dur - 0.5)
            start = random.uniform(0, max_start) if max_start > 0 else 0
            cut_broll_clip(broll_path, str(clip_path), shot_dur, start)
            if clip_path.exists() and clip_path.stat().st_size > 0:
                product_segments[prod_idx].append(str(clip_path))
    print(f"     ✓ {sum(len(s) for s in product_segments)} total clips")

    # 6. Build caption frames for b-roll shots
    print("  6. Caption frames for b-roll...")
    all_composed = []
    for prod_idx, p in enumerate(products):
        segments = product_segments[prod_idx]
        for seg_idx, clip_path in enumerate(segments):
            if seg_idx == 0:
                # Product photo - no caption overlay
                all_composed.append(clip_path)
                continue
            # B-roll shot - add caption
            shot_idx = seg_idx - 1
            d_out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default:noprint_wrappers=1:nokey=1", clip_path],
                capture_output=True, text=True
            )
            try:
                dur = float(d_out.stdout.strip())
            except Exception:
                dur = 2.0
            n_frames = int(dur * FPS)
            scene_frames_dir = tmp / f"frames_{prod_idx:02d}_{shot_idx:02d}"
            scene_frames_dir.mkdir(exist_ok=True)
            caption = p.get(f"shot_{shot_idx}_caption", p["caption"])
            for f_idx in range(n_frames):
                overlay = make_caption_with_animation(caption, f_idx, n_frames)
                combined = Image.alpha_composite(overlay, watermark)
                combined.save(scene_frames_dir / f"{f_idx:04d}.png")
            # Composite
            comp = tmp / f"composed_{prod_idx:02d}_{shot_idx:02d}.mp4"
            subprocess.run([
                "ffmpeg", "-y",
                "-i", clip_path,
                "-framerate", str(FPS),
                "-i", str(scene_frames_dir / "%04d.png"),
                "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
                str(comp)
            ], capture_output=True, text=True)
            if comp.exists():
                all_composed.append(str(comp))
    print(f"     ✓ {len(all_composed)} clips ready")

    # 7. Concat all
    print("  7. Concat all clips...")
    broll_concat = tmp / "broll_concat.mp4"
    concat_list = tmp / "concat.txt"
    with open(concat_list, "w") as f:
        for c in all_composed:
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
    make_intro_card(title_lines, str(intro_png))
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
    make_outro_card(len(products), str(outro_png))
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
        "-movflags", "+faststart",  # <-- key for browser playback
        str(video_only)
    ], capture_output=True, text=True)

    # 11. Mix audio
    print("  11. Mix voiceover + music...")
    video_out = output_dir / f"{slug}.mp4"
    if music:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_only),
            "-i", str(voiceover),
            "-i", str(music),
            "-filter_complex",
            f"[1:a]volume=1.0,afade=t=in:st=0:d=0.5[v];[2:a]volume=0.06,afade=t=in:st=0:d=1.0,afade=t=out:st={voiceover_duration-2}:d=2[m];[v][m]amix=inputs=2:duration=shortest[a]",
            "-map", "0:v",
            "-map", "[a]",
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_only),
            "-i", str(voiceover),
            "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)

    if video_out.exists():
        size = video_out.stat().st_size
        d = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_out)],
            capture_output=True, text=True
        )
        duration = float(d.stdout.strip() or 0)
        print(f"     ✓ {size//1024//1024} MB, {duration:.1f}s")
    return video_out


# Same 3 compilations but with slugs that match the asset filenames
COMPILATIONS = {
    "comp-under-50-2026-v14": {
        "title_lines": ["5 BEST GADGETS", "UNDER $50", "IN 2026"],
        "products": [
            {"slug": "anker-powercore-10k", "brand": "Anker", "name": "PowerCore 10K", "rating": "4.5", "search": ["power bank", "phone charging"], "caption": "BEST POWER BANK", "shot_0_caption": "Charges 2.5 times", "shot_1_caption": "LED indicator", "shot_2_caption": "$25 only", "line": "Number one. The Anker PowerCore 10K. 25 dollars. Charges your phone 2.5 times. Best dollar per charge on the market."},
            {"slug": "anker-nano-ii-65w", "brand": "Anker", "name": "Nano II 65W", "rating": "4.6", "search": ["small charger", "usb c charger"], "caption": "TINIEST CHARGER", "shot_0_caption": "Smaller than a card", "shot_1_caption": "Folds flat", "shot_2_caption": "65 watts", "line": "Number two. Anker Nano II 65 watts. 40 dollars. Smaller than a credit card. Charges a laptop. Folds flat."},
            {"slug": "tp-link-kasa-smart-plug", "brand": "TP-Link", "name": "Kasa Smart Plug", "rating": "4.2", "search": ["smart plug", "smart home"], "caption": "BEST SMART PLUG", "shot_0_caption": "10 second setup", "shot_1_caption": "Schedule devices", "shot_2_caption": "$12 only", "line": "Number three. TP-Link Kasa Smart Plug. 12 dollars. Set up in 10 seconds. Schedule your lights. Save 60 dollars a year on electricity."},
            {"slug": "anker-soundcore-life-q35", "brand": "Anker", "name": "Soundcore Q35", "rating": "4.4", "search": ["headphones", "wireless audio"], "caption": "BEST BUDGET ANC", "shot_0_caption": "Active NC", "shot_1_caption": "40 hour battery", "shot_2_caption": "$80 only", "line": "Number four. Soundcore Life Q35. 80 dollars. Active noise cancelling. 40 hour battery. Beats 400 dollar headphones at half the price."},
            {"slug": "apple-airpods-pro-3", "brand": "Apple", "name": "AirPods Pro", "rating": "4.7", "search": ["airpods", "earbuds"], "caption": "BEST FOR iPHONE", "shot_0_caption": "H2 chip", "shot_1_caption": "Spatial audio", "shot_2_caption": "Seamless switching", "line": "Number five. AirPods Pro. If you have an iPhone, just buy these. H2 chip. Spatial audio. Seamless switching. 200 dollars and worth every cent."},
        ],
    },
}


if __name__ == "__main__":
    load_env()
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_dir = "/home/ubuntu/projects/uzi-network/src/assets/reviews"
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in COMPILATIONS else list(COMPILATIONS.keys())
    success = 0
    for slug in COMPILATIONS:
        if slug not in targets:
            continue
        c = COMPILATIONS[slug]
        result = make_compilation_short(slug, c["title_lines"], c["products"], out_dir, asset_dir)
        if result:
            success += 1
    print(f"\nDone. {success}/{len(targets)} compilations generated.")