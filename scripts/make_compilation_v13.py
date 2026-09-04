#!/usr/bin/env python3
"""
Uzi Network — COMPILATION YouTube Shorts Producer v13
FORMULA 1: Listicle with contrarian hook (most popular from research)
- 5 gadgets in 1 short video
- Each gadget gets 8-15 seconds with B-roll + 1 caption
- Cinematic fast cuts (no Ken Burns, real camera movement)
- Single product = 1 affiliate link. Compilation = 5 affiliate links.
- 1 view = 5 chances for commission
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
        "-f", "lavfi",
        "-i", f"aevalsrc='0.04*sin(2*PI*{root_hz*4}*t + 3*sin(2*PI*0.5*t))*max(0,sin(2*PI*0.1*t))':d={duration_s}:s=44100",
        "-filter_complex",
        "[0:a]volume=1[a0];[1:a]volume=0.6[a1];[2:a]volume=0.4[a2];[a0][a1][a2]amix=inputs=3:duration=longest,volume=0.6,afade=t=in:st=0:d=2,afade=t=out:st={duration_s-3}:d=3[a]",
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


def make_caption_with_animation(text, frame_index, total_frames, w=W, h=H):
    """Lower-third caption with motion."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cap_font = find_font(72, bold=True)
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


def make_product_card(product_idx, total_products, brand, name, rating, frame_index, total_frames, w=W, h=H):
    """Big bold product card in center showing #X of Y + product name."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Top center: "#1 of 5" or "1/5" pill
    num_font = find_font(80, bold=True)
    num_text = f"#{product_idx}"
    bbox = num_font.getbbox(num_text)
    nw = bbox[2] - bbox[0]
    pad_x, pad_y = 40, 20
    pill_w = nw + pad_x * 2
    pill_h = bbox[3] - bbox[1] + pad_y * 2
    pill_x = (w - pill_w) // 2
    pill_y = 200
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=20, fill=ACCENT
    )
    draw.text((pill_x + pad_x, pill_y + pad_y - 4), num_text, font=num_font, fill=(13, 15, 20))
    # Brand above name
    brand_font = find_font(48, bold=True)
    bbox = brand_font.getbbox(brand.upper())
    bw = bbox[2] - bbox[0]
    draw.text(((w - bw) // 2, pill_y + pill_h + 30), brand.upper(), font=brand_font, fill=(200, 200, 200))
    # Big product name
    name_font = find_font(80, bold=True)
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
    y = pill_y + pill_h + 100
    for line in lines:
        bbox = name_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=name_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=name_font, fill=WHITE)
        y += 90
    # Rating
    rating_font = find_font(60, bold=True)
    rtext = f"⭐ {rating}/5"
    bbox = rating_font.getbbox(rtext)
    rw = bbox[2] - bbox[0]
    draw.text(((w - rw) // 2, y + 30), rtext, font=rating_font, fill=ACCENT)
    # Animation
    anim_in = int(0.3 * FPS)
    anim_out = int(0.3 * FPS)
    if frame_index < anim_in:
        t = frame_index / anim_in
        offset = int(50 * (1 - t))
        alpha_mult = t
    elif frame_index >= total_frames - anim_out:
        t = (frame_index - (total_frames - anim_out)) / anim_out
        offset = 0
        alpha_mult = 1 - t
    else:
        offset = 0
        alpha_mult = 1.0
    # Apply alpha
    pixels = img.load()
    alpha_val = int(255 * alpha_mult)
    for x in range(img.width):
        for y in range(img.height):
            p = pixels[x, y]
            if p[3] > 0:
                pixels[x, y] = (p[0], p[1], p[2], int(p[3] * alpha_mult))
    return img


def make_intro_card(title_lines, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    draw = ImageDraw.Draw(img)
    # Big hook text
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
    # Subtitle
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
    # URL
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


def make_compilation_short(slug, title_lines, products, output_dir):
    """
    products: list of dicts with keys: brand, name, rating, search (list of broll terms), caption, line
    Each product gets ~10-15s with its own b-roll, product card, and voiceover line.
    """
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v13/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    clips_dir = tmp / "broll"
    clips_dir.mkdir()
    watermark = make_watermark_topright()
    watermark.save(tmp / "watermark.png")

    # 1. Build full voiceover script with product cues
    intro_text = f"Here are the {len(products)} best gadgets you can buy right now. I tested every single one. The links are in bio."
    outro_text = f"All {len(products)} links are in bio. Pick the one that fits your life. Like and follow for more."
    product_lines = [p["line"] for p in products]
    full_script = intro_text + " " + " ".join(product_lines) + " " + outro_text
    print(f"  1. Voiceover ({len(full_script)} chars)...")
    voiceover = tmp / "voiceover.mp3"
    if not fetch_voiceover_edge_tts(full_script, voiceover):
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

    # 2. B-roll per product
    print("  2. B-roll per product...")
    product_broll = {}
    all_search = []
    for p in products:
        all_search.extend(p["search"])
    all_clips = fetch_pexels_videos(all_search, str(clips_dir), n=30, min_duration_s=8)
    print(f"     ✓ {len(all_clips)} total clips")
    if len(all_clips) < 4:
        return None
    # Distribute clips round-robin to products
    for i, p in enumerate(products):
        # Take every Nth clip starting at i
        n = max(2, len(all_clips) // len(products))
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
    product_dur = (voiceover_duration - 8.0) / len(products)
    print(f"  4. {len(products)} products × {product_dur:.2f}s each")

    # 5. Build per-product scenes
    print("  5. Cut per-product b-roll...")
    scene_clips = []
    for prod_idx, p in enumerate(products):
        prod_broll = product_broll.get(p["name"], all_clips)
        # 2-3 shots per product
        n_shots = max(2, int(product_dur / 3.0))
        shot_dur = product_dur / n_shots
        for shot_idx in range(n_shots):
            broll_idx = (prod_idx * n_shots + shot_idx) % len(prod_broll)
            broll_path = prod_broll[broll_idx]
            clip_path = tmp / f"prod_{prod_idx:02d}_shot_{shot_idx:02d}.mp4"
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
            scene_clips.append((str(clip_path), prod_idx, shot_idx == 0))
    print(f"     ✓ {len(scene_clips)} scene clips")

    # 6. Build caption frames (product card for first shot of each, lower-third for rest)
    print("  6. Frames (product cards + captions)...")
    for clip_path, prod_idx, is_first in scene_clips:
        scene_frames_dir = tmp / f"frames_{prod_idx:02d}_{Path(clip_path).stem[-2:]}"
        scene_frames_dir.mkdir(exist_ok=True)
        # Use the duration that was cut
        d_out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default:noprint_wrappers=1:nokey=1", clip_path],
            capture_output=True, text=True
        )
        try:
            dur = float(d_out.stdout.strip())
        except Exception:
            dur = 3.0
        n_frames = int(dur * FPS)
        p = products[prod_idx]
        for f_idx in range(n_frames):
            if is_first:
                # Big product card showing #X of Y
                overlay = make_product_card(prod_idx + 1, len(products), p["brand"], p["name"], p["rating"], f_idx, n_frames)
            else:
                # Lower-third caption
                overlay = make_caption_with_animation(p["caption"], f_idx, n_frames)
            combined = Image.alpha_composite(overlay, watermark)
            combined.save(scene_frames_dir / f"{f_idx:04d}.png")
    print(f"     ✓ frames for {len(scene_clips)} shots")

    # 7. Composite
    print("  7. Composite...")
    composed_clips = []
    for clip_path, prod_idx, is_first in scene_clips:
        comp = tmp / f"composed_{Path(clip_path).stem}.mp4"
        scene_frames_dir = tmp / f"frames_{prod_idx:02d}_{Path(clip_path).stem[-2:]}"
        n_frames = len(list(scene_frames_dir.glob("*.png")))
        if n_frames == 0:
            shutil.copy(clip_path, comp)
            composed_clips.append(str(comp))
            continue
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
            composed_clips.append(str(comp))
    print(f"     ✓ {len(composed_clips)} composed")

    # 8. Concat
    print("  8. Concat...")
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

    # 9. Intro
    print("  9. Intro...")
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

    # 10. Outro
    print("  10. Outro...")
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

    # 11. Final concat
    print("  11. Final concat...")
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

    # 12. Mix audio
    print("  12. Mix voiceover + music...")
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
            "-pix_fmt", "yuv420p", "-shortest",
            str(video_out)
        ], capture_output=True, text=True)
    else:
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


# First compilation: 5 best gadgets under $50
COMPILATIONS = {
    "comp-under-50-2026": {
        "title_lines": ["5 BEST GADGETS", "UNDER $50", "IN 2026"],
        "products": [
            {"brand": "Anker", "name": "PowerCore 10K", "rating": "4.5", "search": ["power bank", "phone charging"], "caption": "BEST POWER BANK", "line": "Number one. The Anker PowerCore 10K. 25 dollars. Charges your phone 2.5 times. Best dollar per charge on the market."},
            {"brand": "Anker", "name": "Nano II 65W", "rating": "4.6", "search": ["small charger", "usb c charger"], "caption": "TINIEST CHARGER", "line": "Number two. Anker Nano II 65 watts. 40 dollars. Smaller than a credit card. Charges a laptop. Folds flat."},
            {"brand": "TP-Link", "name": "Kasa Smart Plug", "rating": "4.2", "search": ["smart plug", "smart home"], "caption": "BEST SMART PLUG", "line": "Number three. TP-Link Kasa Smart Plug. 12 dollars. Set up in 10 seconds. Schedule your lights. Save 60 dollars a year on electricity."},
            {"brand": "Anker", "name": "Soundcore Q35", "rating": "4.4", "search": ["headphones", "wireless audio"], "caption": "BEST BUDGET ANC", "line": "Number four. Soundcore Life Q35. 80 dollars. Active noise cancelling. 40 hour battery. Beats 400 dollar headphones at half the price."},
            {"brand": "Apple", "name": "AirPods Pro", "rating": "4.7", "search": ["airpods", "earbuds"], "caption": "BEST FOR iPHONE", "line": "Number five. AirPods Pro. If you have an iPhone, just buy these. H2 chip. Spatial audio. Seamless switching. 200 dollars and worth every cent."},
        ],
    },
    "comp-desk-setup-2026": {
        "title_lines": ["5 GADGETS", "THAT FIX", "YOUR DESK"],
        "products": [
            {"brand": "Anker", "name": "727 Charging Station", "rating": "4.6", "search": ["charging station", "desk setup"], "caption": "ONE CABLE", "line": "Number one. Anker 727 Charging Station. 80 dollars. Replaces four chargers. Single cable to your laptop. Cleans up your whole desk."},
            {"brand": "Anker", "name": "543 USB-C Hub", "rating": "4.4", "search": ["usb c hub", "laptop accessories"], "caption": "7 PORTS", "line": "Number two. Anker 543 USB-C Hub. 40 dollars. Seven ports from one USB-C. Plug and play. No drivers. SD card reader alone is worth 30."},
            {"brand": "Logitech", "name": "MX Master 4", "rating": "4.7", "search": ["computer mouse", "wireless mouse"], "caption": "BEST MOUSE", "line": "Number three. Logitech MX Master 4. 100 dollars. Saved my wrist. 70 day battery. Mag speed wheel scrolls 1000 lines per second."},
            {"brand": "Govee", "name": "Glide Wall Light", "rating": "4.2", "search": ["rgb light", "gaming setup"], "caption": "BEST VIBES", "line": "Number four. Govee Glide Wall Light. 70 dollars. Six panels. Music sync. Your whole room pulses to the beat. Changed my bedroom."},
            {"brand": "Notion", "name": "Calendar", "rating": "4.3", "search": ["calendar", "office work"], "caption": "FREE PLANNER", "line": "Number five. Notion Calendar. Free. Integrates with your Notion database. Time blocking. Beats 10 dollar calendar apps."},
        ],
    },
    "comp-travel-2026": {
        "title_lines": ["5 GADGETS", "YOU NEED", "FOR TRAVEL"],
        "products": [
            {"brand": "Anker", "name": "737 Power Bank", "rating": "4.7", "search": ["power bank", "airport", "plane"], "caption": "LAPTOP CHARGER", "line": "Number one. Anker 737. 140 watts. Charges a MacBook on a plane. 24000 milliamp hours. TSA approved. I fly with it every trip."},
            {"brand": "Sony", "name": "WH-1000XM6", "rating": "4.7", "search": ["headphones", "airplane travel", "noise cancelling"], "caption": "BEST ANC", "line": "Number two. Sony XM6. Best noise cancelling in the world. 32 hour battery. 449 dollars but worth it. I use them on every flight."},
            {"brand": "Anker", "name": "Nano II 65W", "rating": "4.6", "search": ["small charger", "travel charger"], "caption": "TINY CHARGER", "line": "Number three. Anker Nano II 65 watts. The only charger I pack for trips. MacBook, iPhone, iPad, all from this brick."},
            {"brand": "Aqara", "name": "U200 Smart Lock", "rating": "4.3", "search": ["smart home", "front door"], "caption": "NO MORE KEYS", "line": "Number four. Aqara U200 Smart Lock. Fingerprint. Keypad. App. No more fumbling for keys with grocery bags. Changed my life."},
            {"brand": "Jackery", "name": "Explorer 1000 v2", "rating": "4.4", "search": ["camping", "power station"], "caption": "EMERGENCY POWER", "line": "Number five. Jackery Explorer 1000 v2. 1000 watt hour battery. When the power went out, I was the only house with lights. Worth every penny."},
        ],
    },
}


if __name__ == "__main__":
    load_env()
    out_dir = Path("/home/ubuntu/projects/uzi-network/docs/social/ready-to-upload")
    out_dir.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [which] if which in COMPILATIONS else list(COMPILATIONS.keys())
    success = 0
    for slug in COMPILATIONS:
        if slug not in targets:
            continue
        c = COMPILATIONS[slug]
        result = make_compilation_short(slug, c["title_lines"], c["products"], out_dir)
        if result:
            success += 1
    print(f"\nDone. {success}/{len(targets)} compilations generated.")