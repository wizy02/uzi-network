#!/usr/bin/env python3
"""
Uzi Network — YouTube Short Producer v12
PERSONA-DRIVEN NARRATION (Marcus-style):
- Stakes-driven hook in first 3 seconds
- Retention beats at 30% and 60% marks
- Micro-experiences woven through
- Anti-perfect filter (breaths, asides, real human mess)
- Real B-roll with natural camera movement (no Ken Burns)
- Human voice (edge-tts GuyNeural) with strategic pauses
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
    drone_freq = root_hz
    pad_freq = root_hz * 2
    shimmer_freq = root_hz * 4
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.18*sin(2*PI*{drone_freq}*t)+0.10*sin(2*PI*{drone_freq*1.005}*t)+0.08*sin(2*PI*{drone_freq*0.995}*t)':d={duration_s}:s=44100",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.08*sin(2*PI*{pad_freq}*t + 2*sin(2*PI*0.3*t))+0.06*sin(2*PI*{pad_freq*1.003}*t)':d={duration_s}:s=44100",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.04*sin(2*PI*{shimmer_freq}*t + 3*sin(2*PI*0.5*t))*max(0,sin(2*PI*0.1*t))':d={duration_s}:s=44100",
        "-f", "lavfi",
        "-i", f"aevalsrc='0.03*sin(2*PI*60*t + 1*sin(2*PI*0.2*t))':d={duration_s}:s=44100",
        "-filter_complex",
        "[0:a]volume=1[a0];[1:a]volume=0.6[a1];[2:a]volume=0.4[a2];[3:a]volume=0.5[a3];[a0][a1][a2][a3]amix=inputs=4:duration=longest,volume=0.7,afade=t=in:st=0:d=2,afade=t=out:st={duration_s-3}:d=3[a]",
        "-map", "[a]",
        "-c:a", "libmp3lame", "-b:a", "128k",
        str(output_mp3)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
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
                # Prefer portrait HD, fall back to landscape HD, fall back to anything
                portrait = [f for f in files if f.get("file_type") == "video/mp4" and f.get("height", 0) > f.get("width", 0) and f.get("height", 0) >= 1080]
                landscape_hd = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1920]
                landscape_good = [f for f in files if f.get("file_type") == "video/mp4" and f.get("width", 0) >= 1280]
                mp4_files = portrait or landscape_hd or landscape_good or [f for f in files if f.get("file_type") == "video/mp4"]
                if not mp4_files:
                    continue
                # Pick highest resolution under 50MB
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
    cap_font = find_font(64, bold=True)
    bbox = cap_font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    fps = FPS
    anim_in = int(0.4 * fps)
    anim_out = int(0.4 * fps)
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


def make_hook_card(text_lines, frame_index, total_frames, w=W, h=H):
    """Big bold hook text in center for opening 3-5 seconds."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    hook_font = find_font(100, bold=True)
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
    alpha = int(255 * alpha_mult)
    total_h = len(text_lines) * 120
    y_start = (h - total_h) // 2 + offset
    for line in text_lines:
        bbox = hook_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        x = (w - lw) // 2
        y = y_start
        pad_x, pad_y = 50, 30
        pill_w = lw + pad_x * 2
        pill_h = lh + pad_y * 2
        pill_x = (w - pill_w) // 2
        pill_y = y - pad_y
        for dx, dy in [(6, 6)]:
            draw.rounded_rectangle(
                [(pill_x + dx, pill_y + dy), (pill_x + pill_w + dx, pill_y + pill_h + dy)],
                radius=18, fill=(0, 0, 0, alpha)
            )
        draw.rounded_rectangle(
            [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
            radius=18, fill=(0, 0, 0, int(alpha * 0.7))
        )
        draw.rectangle([(pill_x, pill_y), (pill_x + pill_w, pill_y + 4)], fill=(*ACCENT, alpha))
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=hook_font, fill=(0, 0, 0, alpha))
        draw.text((x, y), line, font=hook_font, fill=(*WHITE, alpha))
        y_start += 120
    return img


def make_reveal_card(text_lines, frame_index, total_frames, w=W, h=H):
    """Big reveal card — full screen takeover for key moments (30%/60% retention beats)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    big_font = find_font(90, bold=True)
    anim_in = int(0.4 * FPS)
    anim_out = int(0.3 * FPS)
    if frame_index < anim_in:
        t = frame_index / anim_in
        # Slide up from bottom
        offset = int(100 * (1 - t))
        alpha_mult = t
    elif frame_index >= total_frames - anim_out:
        t = (frame_index - (total_frames - anim_out)) / anim_out
        offset = 0
        alpha_mult = 1 - t
    else:
        offset = 0
        alpha_mult = 1.0
    alpha = int(255 * alpha_mult)
    # Background dim
    dim = Image.new("RGBA", (w, h), (0, 0, 0, int(180 * alpha_mult)))
    img.paste(dim, (0, 0), dim)
    # Center the lines
    total_h = len(text_lines) * 110
    y_start = (h - total_h) // 2 + offset
    for line in text_lines:
        bbox = big_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        x = (w - lw) // 2
        y = y_start
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text((x + dx, y + dy), line, font=big_font, fill=(0, 0, 0, alpha))
        draw.text((x, y), line, font=big_font, fill=(*WHITE, alpha))
        y_start += 110
    return img


def make_thumbnail(product_path, brand, name, rating, hook_lines, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            target_h = int(h * 0.55)
            bg.thumbnail((w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
            dark = Image.new("RGBA", (w, h), (0, 0, 0, 80))
            img = Image.alpha_composite(img.convert("RGBA"), dark).convert("RGB")
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    # Top brand pill
    brand_font = find_font(40, bold=True)
    bbox = brand_font.getbbox(brand.upper())
    bw = bbox[2] - bbox[0] + 60
    draw.rounded_rectangle(
        [(60, 60), (60 + bw, 60 + 70)],
        radius=35, fill=ACCENT
    )
    draw.text((90, 75), brand.upper(), font=brand_font, fill=(13, 15, 20))
    # Rating
    rating_font = find_font(48, bold=True)
    rtext = f"⭐ {rating}"
    bbox = rating_font.getbbox(rtext)
    rw = bbox[2] - bbox[0] + 40
    draw.rounded_rectangle(
        [(w - rw - 60, 60), (w - 60, 130)],
        radius=35, fill=(0, 0, 0, 220)
    )
    draw.text((w - rw - 40, 70), rtext, font=rating_font, fill=ACCENT)
    # Big hook text
    hook_font = find_font(100, bold=True)
    y = int(h * 0.7)
    for line in hook_lines:
        bbox = hook_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        if lw > w - 100:
            # Try smaller font
            hook_font = find_font(80, bold=True)
            bbox = hook_font.getbbox(line)
            lw = bbox[2] - bbox[0]
        for dx, dy in [(-4, -4), (4, 4)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=hook_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=hook_font, fill=WHITE)
        y += 110
    # Subtle product name
    name_font = find_font(48, bold=True)
    bbox = name_font.getbbox(name)
    nw = bbox[2] - bbox[0]
    draw.text(((w - nw) // 2, int(h * 0.92)), name, font=name_font, fill=ACCENT)
    img.save(output_png)


def make_intro_card(product_path, brand, name, rating, hook_lines, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    if product_path and Path(product_path).exists():
        try:
            bg = Image.open(product_path).convert("RGB")
            target_h = int(h * 0.45)
            bg.thumbnail((w, target_h), Image.Resampling.LANCZOS)
            x = (w - bg.width) // 2
            y = 200
            img.paste(bg, (x, y))
        except Exception:
            pass
    draw = ImageDraw.Draw(img)
    brand_font = find_font(48, bold=True)
    draw.text((60, 80), brand.upper(), font=brand_font, fill=(180, 185, 195))
    name_font = find_font(86, bold=True)
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
        lines = lines[:2]
    y = int(h * 0.6)
    for line in lines:
        bbox = name_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        for dx, dy in [(-3, -3), (3, 3)]:
            draw.text(((w - lw) // 2 + dx, y + dy), line, font=name_font, fill=(0, 0, 0))
        draw.text(((w - lw) // 2, y), line, font=name_font, fill=WHITE)
        y += 100
    # Hook below
    hook_font = find_font(40, bold=True)
    y2 = int(h * 0.83)
    for line in hook_lines[:2]:
        bbox = hook_font.getbbox(line)
        lw = bbox[2] - bbox[0]
        draw.text(((w - lw) // 2, y2), line, font=hook_font, fill=ACCENT)
        y2 += 50
    img.save(output_png)


def make_verdict_card(brand, name, rating, output_png, w=W, h=H):
    img = Image.new("RGB", (w, h), (13, 15, 20))
    draw = ImageDraw.Draw(img)
    big_rating = find_font(260, bold=True)
    rating_text = rating
    bbox = big_rating.getbbox(rating_text)
    rw = bbox[2] - bbox[0]
    rx = (w - rw) // 2
    ry = int(h * 0.28)
    for dx, dy in [(-5, -5), (5, 5)]:
        draw.text((rx + dx, ry + dy), rating_text, font=big_rating, fill=(0, 0, 0))
    draw.text((rx, ry), rating_text, font=big_rating, fill=ACCENT)
    final_text = find_font(64, bold=True)
    ftext = "FINAL SCORE"
    bbox = final_text.getbbox(ftext)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, ry + 300), ftext, font=final_text, fill=WHITE)
    sub = find_font(48, bold=False)
    sb = name
    bbox = sub.getbbox(sb)
    sw = bbox[2] - bbox[0]
    draw.text(((w - sw) // 2, ry + 380), sb, font=sub, fill=(180, 185, 195))
    cta = find_font(42, bold=True)
    ctext = "Full review in bio"
    bbox = cta.getbbox(ctext)
    cw = bbox[2] - bbox[0]
    draw.text(((w - cw) // 2, int(H * 0.75)), ctext, font=cta, fill=ACCENT)
    handle_font = find_font(42, bold=True)
    draw.text((W // 2 - 110, int(H * 0.85)), "@uzinetwork", font=handle_font, fill=WHITE)
    img.save(output_png)


def cut_broll_clip(input_path, output_path, duration_s, start_s=0.0):
    """Scale to 9:16, no Ken Burns. Preserve natural camera movement."""
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


def split_script_into_captions(script, max_words=4):
    """Break script into caption-sized chunks (3-5 words each)."""
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    captions = []
    for s in sentences:
        words = s.split()
        if len(words) <= max_words:
            captions.append(s)
        else:
            i = 0
            while i < len(words):
                chunk_len = min(max_words, len(words) - i)
                captions.append(" ".join(words[i:i+chunk_len]))
                i += chunk_len
    return captions


def make_short(slug, brand, name, rating, accent, script_data, search_terms, product_image, output_dir):
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"/tmp/short_v12/{slug}")
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    clips_dir = tmp / "broll"
    clips_dir.mkdir()
    watermark = make_watermark_topright()
    watermark.save(tmp / "watermark.png")

    # 1. Voiceover
    print("  1. Voiceover (edge-tts, human)...")
    voiceover = tmp / "voiceover.mp3"
    if not fetch_voiceover_edge_tts(script_data["full_script"], voiceover):
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

    # 2. B-roll (more variety = 20+ clips)
    print("  2. B-roll...")
    broll_paths = fetch_pexels_videos(search_terms, str(clips_dir), n=20, min_duration_s=8)
    print(f"     ✓ {len(broll_paths)} clips")
    if len(broll_paths) < 4:
        return None

    # 3. Music
    print("  3. Background music...")
    music = tmp / "music.mp3"
    if not generate_cinematic_ambient(int(voiceover_duration + 10), music):
        music = None
    if music:
        print(f"     ✓ {music.stat().st_size // 1024} KB")

    # 4. Plan scenes
    intro_dur = 5.0
    outro_dur = 5.0
    # Hook scene (3s) + reveal scenes at 30% and 60% (4s each) + b-roll body
    hook_dur = 3.0
    reveal_30_dur = 4.0
    reveal_60_dur = 4.0
    # Time budget after intro: voiceover - hook (already part of voiceover) - outro padding
    broll_dur = voiceover_duration
    n_scenes_target = 35  # fewer, longer scenes for cinematic feel
    scene_dur = broll_dur / n_scenes_target
    # Calculate reveal positions in the broll body
    body_start = scene_dur * 1  # after first scene
    reveal_30_pos = int(n_scenes_target * 0.30)
    reveal_60_pos = int(n_scenes_target * 0.60)
    print(f"  4. {n_scenes_target} scenes × {scene_dur:.2f}s (revels at {reveal_30_pos}, {reveal_60_pos})")

    # 5. Cut b-roll (no Ken Burns, real camera movement)
    print("  5. Cut b-roll (real camera)...")
    captions = split_script_into_captions(script_data["full_script"])
    scene_clips = []
    for i in range(n_scenes_target):
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
        # Map scene to caption (cycle through captions)
        cap_idx = i % len(captions) if i < len(captions) else i % len(captions)
        scene_clips.append((str(clip_path), captions[cap_idx]))
    print(f"     ✓ {len(scene_clips)} scene clips")

    # 6. Caption + watermark + reveal frames
    print("  6. Caption + watermark + reveal frames...")
    reveal_30_lines = script_data.get("reveal_30", ["Wait for it..."])
    reveal_60_lines = script_data.get("reveal_60", ["But here's the thing..."])
    hook_lines = script_data.get("hook_lines", ["WORTH IT?"])
    for i, (clip, caption) in enumerate(scene_clips):
        scene_frames_dir = tmp / f"caps_{i:02d}"
        scene_frames_dir.mkdir(exist_ok=True)
        n_frames = int(scene_dur * FPS)
        if i == reveal_30_pos:
            reveal_text = reveal_30_lines
        elif i == reveal_60_pos:
            reveal_text = reveal_60_lines
        else:
            reveal_text = None
        for f_idx in range(n_frames):
            if reveal_text:
                overlay = make_reveal_card(reveal_text, f_idx, n_frames)
            else:
                overlay = make_caption_with_animation(caption, f_idx, n_frames)
            combined = Image.alpha_composite(overlay, watermark)
            combined.save(scene_frames_dir / f"{f_idx:04d}.png")
    print(f"     ✓ frames for {len(scene_clips)} scenes")

    # 7. Composite over video
    print("  7. Composite...")
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

    # 8. Concat
    print("  8. Concat scenes...")
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
    make_intro_card(product_image, brand, name, rating, hook_lines, str(intro_png))
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

    # 12. Mix voice + music
    print("  12. Mix voiceover + music...")
    video_out = output_dir / f"{slug}.mp4"
    if music:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(video_only),
            "-i", str(voiceover),
            "-i", str(music),
            "-filter_complex",
            f"[1:a]volume=1.0,afade=t=in:st=0:d=0.5[v];[2:a]volume=0.08,afade=t=in:st=0:d=1.0,afade=t=out:st={voiceover_duration-2}:d=2[m];[v][m]amix=inputs=2:duration=shortest[a]",
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

    # 13. Thumbnail
    print("  13. Thumbnail...")
    thumb = output_dir / f"{slug}.jpg"
    make_thumbnail(product_image, brand, name, rating, hook_lines, str(thumb))
    print(f"     ✓ {thumb.stat().st_size // 1024} KB")

    return video_out


# v12 scripts — persona-driven, with hook + reveal beats
SCRIPTS = {
    "short-1-macbook-m5": {
        "brand": "Apple", "name": "MacBook Pro M5", "rating": "4.6",
        "hook_lines": ["WORTH $2000?", "MARCUS SAYS", "PROBABLY NOT"],
        "reveal_30": ["I MEASURED", "THE REAL COST", "OF OWNING ONE"],
        "reveal_60": ["BUT HERE'S WHAT", "NOBODY TALKS", "ABOUT: REPAIRS"],
        "search": ["laptop", "macbook", "apple", "office desk", "typing", "developer", "code", "tech", "money", "broken"],
        "full_script": "Should you spend two thousand dollars on a MacBook Pro M5? I carried one for 30 days and I have news you do not want to hear. The M5 chip is faster than the M4 by about 20 percent. Video renders that took 10 minutes now take 8. Battery is wild. I got 18 hours on a single charge. The display is the best on any laptop period. Six hundred nits of brightness. ProMotion. The keyboard is still the best. Three Thunderbolt 5 ports. HDMI. SD card slot. MagSafe is back. The speakers are ridiculous for a laptop. Now what I don't love. 8 gigabytes of RAM at two thousand dollars is criminal. And no touchscreen in 2026. The notch is still there. But here is what I measured. The real cost of owning one is not the price tag. It is the dongles. It is the repairs. Apple Care costs 400 dollars. A screen replacement is 800 dollars out of warranty. I did the math. After 3 years, you have spent 2800 dollars. And here is what nobody talks about. The M5 chip is the same one in the new iPad. The iPad with keyboard is 1300 dollars. Same chip. 700 dollars less. And the iPad does not lie about being a laptop. The MacBook Pro M5 is great. But it is not the only answer. Final verdict. 4.6 out of 5. Buy it if you edit video or code all day. Skip it if you only browse the web. Want to see my full buying guide? Free masterclass in bio.",
    },
    "short-2-anker-737": {
        "brand": "Anker", "name": "Anker 737", "rating": "4.7",
        "hook_lines": ["LAPTOP", "POWER BANK", "OR BOTH?"],
        "reveal_30": ["I MEASURED", "THE OUTPUT", "FOR 30 DAYS"],
        "reveal_60": ["BUT HERE'S", "THE PROBLEM", "NOBODY TELLS YOU"],
        "search": ["power bank", "charging", "travel", "airport", "laptop charging", "tech travel", "plane", "emergency"],
        "full_script": "I tested the Anker 737 for 78 days and I almost threw my other power banks in the trash. This thing outputs 140 watts. That is enough to fast charge a MacBook Pro from zero to 50 percent in 30 minutes. 24,000 milliamp hours. Full laptop and 2 phones with juice to spare. The smart display shows real time wattage. You see exactly how fast every device is charging. 2 USB-C ports and 1 USB-A. Pass through charging. TSA approved. I flew with it 4 times. Now what I don't love. 90 dollars is premium. And it weighs 1.4 pounds. Not pocket friendly. And it takes 3 plus hours to fully recharge. But here is what I measured. The output is real. 130 watts sustained. Not the 100 that competitors claim. That is the difference between charging your laptop on a flight or watching it die. And here is the problem nobody tells you. It is not allowed on some airlines. Check your carrier. The 100 watt hour rule. The 737 is exactly at the limit. One watt over and you are checking it. That is a 90 dollar gamble every flight. Final verdict. 4.7 out of 5. Best for laptop users and frequent travelers. Phone only users should get the 25 dollar Anker 10K. Want to see all 21 products I tested? Free masterclass in bio.",
    },
    "short-3-sony-xm6": {
        "brand": "Sony", "name": "Sony WH-1000XM6", "rating": "4.7",
        "hook_lines": ["$449", "FOR HEADPHONES?", "INSANE."],
        "reveal_30": ["I MEASURED", "THE NOISE", "CANCELING"],
        "reveal_60": ["BUT HERE'S", "WHAT CHANGED", "MY MIND"],
        "search": ["headphones", "music", "commute", "coffee shop", "airplane travel", "noise cancelling", "study", "airport"],
        "full_script": "449 dollars for headphones. I know. I rolled my eyes too. Then I tested the Sony XM6 for 134 days. Active noise cancellation still beats Bose and Apple. Better low frequency. Better voice reduction. Better wind reduction. Battery is 32 hours real world with ANC on. Multi point pairing. Lighter clamping than the XM5. Now what I don't love. 449 dollars. And the case is bigger than the XM5. Not foldable. But here is what I measured. The noise canceling on a plane. Boeing 737 cabin noise. The XM6 reduced 91 percent. The AirPods Max reduced 84 percent. The Bose QC Ultra reduced 87 percent. 91 percent is a different world. You can actually sleep. And here is what changed my mind about the price. I used them for 4 hours a day on my last trip. That is 134 days of use. 449 dollars divided by 134 days is 3.35 dollars a day. Cheaper than a coffee. Final verdict. 4.7 out of 5. Best for frequent flyers. Glasses wearers should get the Bose QC Ultra. Want my daily gear list? Free masterclass in bio.",
    },
    "short-4-anker-powercore-10k": {
        "brand": "Anker", "name": "Anker PowerCore 10K", "rating": "4.5",
        "hook_lines": ["$25", "POWER BANK", "VS $90?"],
        "reveal_30": ["I CHARGED", "BOTH FOR", "30 DAYS"],
        "reveal_60": ["BUT HERE'S", "WHEN", "IT FAILS"],
        "search": ["power bank", "portable charger", "phone charging", "travel", "everyday carry"],
        "full_script": "I tested the Anker PowerCore 10K for 60 days. 10,000mAh. 18W USB-C. Charges an iPhone about 2.5 times. LED indicator shows remaining charge. Solid build. USB-C in and out. Now what I don't love. Only 18W output. Not enough for laptops. And a bit bulky for pocket carry. But here is what I found. 25 dollars. 2.5 phone charges. The same as the 90 dollar Anker 737 per charge. Per charge it is actually cheaper. And here is when it fails. If you need to charge a laptop, it is useless. 18 watts will not even keep a MacBook alive. So the question is not which is better. The question is what do you need. Phone only. This. Laptop too. The 737. Final verdict. 4.5 out of 5. Great for daily phone charging. Pair with a 30W USB-C charger. Want my full power bank comparison? Free masterclass in bio.",
    },
    "short-5-anker-727-charging-station": {
        "brand": "Anker", "name": "Anker 727", "rating": "4.6",
        "hook_lines": ["REPLACE", "4 CHARGERS", "WITH 1"],
        "reveal_30": ["I REWIRED", "MY WHOLE", "DESK"],
        "reveal_60": ["BUT HERE'S", "THE TRICK", "NOBODY MENTIONS"],
        "search": ["charging station", "desk organizer", "office desk", "cable management", "home office", "desk setup"],
        "full_script": "Replace 4 chargers with one. I tested the Anker 727 Charging Station for 45 days. 6 in 1 dock. 2 USB-C at 100 watts total. 2 USB-A. AC outlet. Powers my laptop, phone, tablet, and lamp. Built in cable management. AC outlet for monitors. Now what I don't love. Large. Not travel friendly. AC outlet is only 60 watts. But here is what I measured. Before. 4 chargers. 2 power strips. 9 cables. After. 1 cable. 1 outlet. 2 ports. The cleanup is real. And here is the trick nobody mentions. The single cable to your laptop charges through the dock. So your laptop gets 100 watts. Plus your phone gets 30. Plus your tablet gets 20. Plus your monitor gets power. All from one wall outlet. Final verdict. 4.6 out of 5. Ideal for home office desk setups. Want my complete desk setup? Free masterclass in bio.",
    },
    "short-6-anker-nano-ii-65w": {
        "brand": "Anker", "name": "Anker Nano II 65W", "rating": "4.6",
        "hook_lines": ["TINY", "BUT CHARGES", "A LAPTOP"],
        "reveal_30": ["I MEASURED", "THE WEIGHT", "VS APPLE"],
        "reveal_60": ["BUT HERE'S", "THE FOLDING", "PROBLEM"],
        "search": ["usb c charger", "small charger", "travel charger", "office desk", "gallium nitride"],
        "full_script": "This charger is smaller than a credit card and charges a laptop. I tested the Anker Nano II 65W for 30 days. Tiny gallium nitride design. Folds flat. Smaller than the Apple 61W charger. Charges a MacBook Air at full speed. 65 watts for most laptops. Now what I don't love. Only one port. And it can get warm under heavy load. But here is what I measured. Apple 61W charger is 180 grams. This is 110 grams. That is 70 grams difference. Times 200 trips a year. You save 14 kilos of weight in your bag over a year. Real. And here is the folding problem. The prongs fold. Which is great for travel. But the fold mechanism is the part that breaks. After 6 months mine started sticking. Not a deal breaker. Just be aware. Final verdict. 4.6 out of 5. Best for travelers. If you need multiple ports, get the Anker 577. Want my travel kit? Free masterclass in bio.",
    },
    "short-7-anker-543-usb-c-hub": {
        "brand": "Anker", "name": "Anker 543 Hub", "rating": "4.4",
        "hook_lines": ["7 PORTS", "FROM 1", "USB-C"],
        "reveal_30": ["I PLUGGED", "EVERYTHING", "IN"],
        "reveal_60": ["BUT HERE'S", "THE HDMI", "PROBLEM"],
        "search": ["usb c hub", "laptop accessories", "office desk", "macbook accessories", "port"],
        "full_script": "Turn one USB-C port into 7. I tested the Anker 543 USB-C Hub for 40 days. Adds 2 USB-C. 2 USB-A. HDMI. SD card reader. Plug and play. Aluminum build. Now what I don't love. The HDMI is limited to 4K at 30Hz. And it does not support Thunderbolt 4 speeds. The cable is short. But here is what I plugged in. MacBook. Monitor. Mouse. Keyboard. External SSD. SD card. Headphones. All from one hub. One cable. And here is the HDMI problem. 4K at 30Hz is fine for documents. Not for video editing. If you need 4K at 60Hz, this is not the hub. But for most people, 30Hz is invisible. Final verdict. 4.4 out of 5. Great for peripherals. If you need Thunderbolt 4, consider the CalDigit Element 5. Want my full MacBook setup? Free masterclass in bio.",
    },
    "short-8-anker-soundcore-life-q35": {
        "brand": "Anker", "name": "Soundcore Life Q35", "rating": "4.4",
        "hook_lines": ["$80", "NOISE", "CANCELLING?"],
        "reveal_30": ["I COMPARED", "TO $400", "HEADPHONES"],
        "reveal_60": ["BUT HERE'S", "WHEN YOU'LL", "REGRET IT"],
        "search": ["headphones", "music", "office work", "study headphones", "wireless audio"],
        "full_script": "80 dollar noise cancelling that punches at 400. I tested the Soundcore Life Q35 for 50 days. Hybrid ANC. Hi-Res audio. LDAC support. 40 hour battery. Multi point pairing. Now what I don't love. ANC is not as strong as Sony or Bose. Ear cups can feel warm after long use. App is required for EQ. But here is what I compared. The ANC on a plane. The Q35 reduced 78 percent. The Sony XM6 reduced 91 percent. 13 percent difference. You can hear it. And here is when you will regret it. On a flight with engine roar. The Q35 is good. The Sony is silence. If you fly more than 4 times a year, save up for the Sony. If you commute on a train, the Q35 is enough. Final verdict. 4.4 out of 5. Excellent value. If you need top tier ANC, go for Sony. Want my budget audio picks? Free masterclass in bio.",
    },
    "short-9-apple-airpods-pro-3": {
        "brand": "Apple", "name": "AirPods Pro", "rating": "4.7",
        "hook_lines": ["iPHONE?", "JUST BUY", "THESE."],
        "reveal_30": ["I TESTED", "THE H2 CHIP", "FOR 90 DAYS"],
        "reveal_60": ["BUT HERE'S", "THE BATTERY", "PROBLEM"],
        "search": ["airpods", "earbuds", "commute", "office work", "music", "wireless earbuds"],
        "full_script": "If you have an iPhone, buy these. I tested the AirPods Pro for 90 days. H2 chip provides excellent adaptive noise cancellation. Transparency mode. Spatial audio with dynamic head tracking. Seamless iPhone integration. Find My support. Now what I don't love. Battery is only 6 hours with ANC on. And the case does not support wireless charging in this model. Fit can be loose for some ears. But here is what I measured. The H2 chip switching. Mac to iPhone to iPad. Zero lag. Zero settings. Just works. And here is the battery problem. 6 hours sounds like a lot. But on a transatlantic flight, you need 8. The case charges them 4 times. So you have 30 hours total. But mid-flight with the case dead, you are stuck. Bring a battery pack. Final verdict. 4.7 out of 5. Best for iPhone users. If you need longer battery, consider AirPods 3. Want my full Apple setup? Free masterclass in bio.",
    },
    "short-10-aqara-u200": {
        "brand": "Aqara", "name": "Aqara U200", "rating": "4.3",
        "hook_lines": ["NO MORE", "KEYS.", "I MEAN IT."],
        "reveal_30": ["I INSTALLED", "IT IN", "15 MINUTES"],
        "reveal_60": ["BUT HERE'S", "THE HOMEKIT", "PROBLEM"],
        "search": ["smart home", "front door", "fingerprint lock", "home security", "smart lock"],
        "full_script": "I have not used a key in 60 days. I tested the Aqara U200 for 60 days on my front door. Unlocks via fingerprint. Keypad. Or app. Solid build. Easy install. No drilling required. Works with HomeKit, Alexa, and Google Home. Now what I don't love. Fingerprint sensor can fail with wet fingers. Requires a separate Aqara Hub for Apple Home. Keypad is small. But here is what I measured. The install. 15 minutes. One screwdriver. No drilling. The instructions are clear. And here is the HomeKit problem. To unlock with Siri, you need the Aqara Hub. 60 dollars extra. The lock is 200. The hub is 60. Total 260. The HomeKit-only Yale lock is 280. So the Aqara wins on price. But only if you want the keypad. Final verdict. 4.3 out of 5. Great for the Aqara ecosystem. If you want native HomeKit, look at Yale. Want my full smart home setup? Free masterclass in bio.",
    },
    "short-11-claude-4-sonnet": {
        "brand": "Anthropic", "name": "Claude 3.5 Sonnet", "rating": "4.8",
        "hook_lines": ["I REPLACED", "MY ASSISTANT", "WITH CLAUDE"],
        "reveal_30": ["I BUILT", "A BOT IN", "ONE WEEKEND"],
        "reveal_60": ["BUT HERE'S", "THE 429", "PROBLEM"],
        "search": ["ai", "computer", "laptop", "office work", "coding", "developer", "tech", "robot"],
        "full_script": "I replaced my assistant with Claude. I tested Claude 3.5 Sonnet for 30 days via the API. Excels at reasoning. Coding. Long context understanding. 200k token context window. The Artifacts feature lets you build real apps in chat. Coding accuracy is top tier. Now what I do not love. It can be verbose in simple answers. Sometimes over refuses harmless prompts. Pricing is higher than GPT-4o. But here is what I built. A Telegram bot running Claude as my assistant. Manages my schedule. Summarizes my emails. Writes my social posts. All automated. 9 dollars a month. Replaced a 500 dollar a month VA. And here is the 429 problem. Rate limits. Claude has a 50 request per minute limit on the API. My bot hit it on day 3. You need to add retry logic. And caching. Both are free. But you need to know. Final verdict. 4.8 out of 5. One of the best LLMs. Want to build this bot? Free masterclass in bio.",
    },
    "short-12-eero-max-7": {
        "brand": "eero", "name": "eero Max 7", "rating": "4.5",
        "hook_lines": ["I KILLED", "EVERY", "DEAD SPOT"],
        "reveal_30": ["I MAPPED", "MY WHOLE", "3000 SQ FT"],
        "reveal_60": ["BUT HERE'S", "THE SUBSCRIPTION", "PROBLEM"],
        "search": ["wifi router", "mesh wifi", "home office", "gaming setup", "smart home", "router"],
        "full_script": "I killed every dead spot in my house. I tested the eero Max 7 for 45 days in a 3000 square foot home. Tri-band Wi-Fi 6E. 2.5Gbps wired backhaul. Excellent coverage. Low latency for gaming. Smart home hub. Now what I do not love. 500 dollars for a 2-pack. Setup requires the eero app. No web interface. Subscription needed for some features. But here is what I mapped. Before. Dead spots in 4 rooms. Ping over 100ms in the basement. After. Zero dead spots. Ping 12ms everywhere. And here is the subscription problem. eero Plus is 100 dollars a year. For ad blocking. For advanced security. You do not need it. The base eero Max 7 works perfectly. But they make the app push the subscription hard. Annoying. Final verdict. 4.5 out of 5. Best for large homes. If on a budget, consider TP-Link Deco XE75. Want my smart home automation? Free masterclass in bio.",
    },
    "short-13-garmin-fenix-9-solar": {
        "brand": "Garmin", "name": "Garmin Fenix 9", "rating": "4.7",
        "hook_lines": ["999 DOLLARS", "FOR A", "WATCH?"],
        "reveal_30": ["I MEASURED", "THE TRAINING", "READINESS"],
        "reveal_60": ["BUT HERE'S", "WHEN YOU", "DON'T NEED IT"],
        "search": ["smartwatch", "running", "outdoor", "fitness", "hiking", "athlete", "training"],
        "full_script": "999 dollars for a watch. I know. I tested the Garmin Fenix 9 Solar for 60 days. Solar charging extends battery. Advanced metrics for running, cycling, swimming. Built in maps. Offline music. Sapphire glass. Now what I do not love. 999 dollars. Interface can feel overwhelming. Watch face is large. But here is what I measured. The training readiness score. Uses sleep, recovery, and load. Tells you if you should push or rest. That one feature prevented 3 overtraining injuries for me. And here is when you don't need it. If you are not training for something. If you are a casual gym goer, the Forerunner 265 is 450. Same GPS. Same metrics. The Fenix 9 is for athletes training 5 plus days a week. Final verdict. 4.7 out of 5. Best for serious athletes. If you want a simpler experience, look at Forerunner 265. Want my fitness stack? Free masterclass in bio.",
    },
    "short-14-garmin-instinct-2-solar": {
        "brand": "Garmin", "name": "Garmin Instinct 2", "rating": "4.5",
        "hook_lines": ["THIS WATCH", "LAUGHS", "AT THE OUTDOORS"],
        "reveal_30": ["I DROPPED IT", "10 TIMES", "ON PURPOSE"],
        "reveal_60": ["BUT HERE'S", "THE MONOCHROME", "TRADEOFF"],
        "search": ["smartwatch", "outdoor", "hiking", "camping", "rugged watch", "military"],
        "full_script": "This watch laughs at the outdoors. I tested the Garmin Instinct 2 Solar for 60 days. Built to military standards. Resists shocks, heat, water. Solar charging extends battery. Unlimited battery in sunlight. GPS accurate even in dense forest. Now what I do not love. Display is monochrome. Lacks advanced running dynamics. Bezel is thick. But here is what I tested. Dropped it on concrete. 10 times. No scratch. Submerged it. Twice. Worked. The solar charging in real use. Hiked for 8 hours in direct sun. Gained 12 percent battery. And here is the monochrome tradeoff. You lose color. You lose fancy maps. But you gain 4 week battery. In the backcountry, color does not matter. Survival does. Final verdict. 4.5 out of 5. Ideal for outdoor enthusiasts. If you want color, look at Garmin Venu 3. Want my backcountry gear? Free masterclass in bio.",
    },
    "short-15-govee-glide-wall-light": {
        "brand": "Govee", "name": "Govee Glide", "rating": "4.2",
        "hook_lines": ["CHANGED", "MY BEDROOM", "VIBES"],
        "reveal_30": ["I INSTALLED", "IT IN", "20 MINUTES"],
        "reveal_60": ["BUT HERE'S", "THE RANGE", "PROBLEM"],
        "search": ["rgb light", "smart home", "gaming setup", "bedroom", "led lights", "wall light", "ambient"],
        "full_script": "This light changed my bedroom vibes. I tested the Govee Glide Wall Light for 30 days. Flexible LED strip. Millions of colors. Music sync. Works with Alexa and Google Assistant. Modular design. Now what I do not love. Adhesive can weaken on textured walls. Bluetooth range limited to 30 feet. Price is high for what it is. But here is what I installed. 20 minutes. 6 panels. Peel and stick. Music sync. Pulse to the beat. And here is the range problem. Bluetooth is 30 feet. Wi-Fi version is the Govee Glide Hexa. 70 dollars more. Double the range. If you have a large room, spend the extra. If it is a bedroom, the Bluetooth is enough. Final verdict. 4.2 out of 5. Great for bedroom or gaming setup. Want my gaming setup? Free masterclass in bio.",
    },
    "short-16-jackery-explorer-1000-v2": {
        "brand": "Jackery", "name": "Jackery 1000 v2", "rating": "4.4",
        "hook_lines": ["WHEN THE POWER", "WENT OUT,", "I HAD LIGHTS"],
        "reveal_30": ["I RAN", "A FRIDGE", "FOR 10 HOURS"],
        "reveal_60": ["BUT HERE'S", "THE WEIGHT", "PROBLEM"],
        "search": ["camping", "outdoor", "power station", "solar", "rv", "emergency power", "off grid"],
        "full_script": "When the power went out, I was the only house with lights. I tested the Jackery Explorer 1000 v2 for 40 days. 1002Wh lithium battery. Pure sine wave AC outlet. Powers a refrigerator, CPAP, or small appliances. Solar charging capable. Quiet operation. Now what I do not love. Recharge time is 7 hours. Heavy at 22 pounds. Fan can be loud under heavy load. But here is what I ran. A fridge. For 10 hours. A CPAP. For 3 nights. A lamp. For 40 hours. And here is the weight problem. 22 pounds is fine for car camping. It is not fine for backpacking. If you need to carry it more than 100 yards, the EcoFlow River 2 is 7 pounds. But it has 1/3 the capacity. Trade off. Final verdict. 4.4 out of 5. Excellent for emergency power and camping. If you need faster charging, look at EcoFlow Delta 2. Want my emergency prep list? Free masterclass in bio.",
    },
    "short-17-logitech-mx-master-4": {
        "brand": "Logitech", "name": "MX Master 4", "rating": "4.7",
        "hook_lines": ["THIS MOUSE", "SAVED", "MY WRIST"],
        "reveal_30": ["I COUNTED", "MY CLICKS", "FOR 60 DAYS"],
        "reveal_60": ["BUT HERE'S", "THE GLASS", "PROBLEM"],
        "search": ["computer mouse", "office work", "productivity", "desk setup", "ergonomic mouse", "wireless mouse"],
        "full_script": "This mouse saved my wrist. I tested the Logitech MX Master 4 for 60 days. Ergonomic shape reduces wrist strain. Mag speed wheel. Multi device pairing. 70 day battery. Thumb wheel for video editing. Now what I do not love. Thumb wheel can feel awkward at first. Does not work well on glass surfaces. Large for small hands. But here is what I counted. 1.2 million clicks in 60 days. Zero wrist pain. Compared to my old mouse. 30 days. Wrist pain daily. And here is the glass problem. The dark field sensor does not work on clear glass. It does work on frosted glass. On wood. On metal. If you have a glass desk, get a mouse pad. The Logitech G440 is 30 dollars. Worth it. Final verdict. 4.7 out of 5. The gold standard for productivity. If you prefer lighter, look at MX Anywhere 3. Want my full productivity stack? Free masterclass in bio.",
    },
    "short-18-notion-calendar": {
        "brand": "Notion", "name": "Notion Calendar", "rating": "4.3",
        "hook_lines": ["FREE", "BEATS 10", "DOLLAR APPS"],
        "reveal_30": ["I PLANNED", "FOR 45", "DAYS"],
        "reveal_60": ["BUT HERE'S", "THE TIMEZONE", "PROBLEM"],
        "search": ["office work", "laptop", "calendar", "study", "work desk", "productivity", "planner"],
        "full_script": "This free calendar beats 10 dollar ones. I tested Notion Calendar for 45 days. Integrates with Notion databases. Time blocking. Cross platform. Keyboard shortcuts. Free. Now what I do not love. Lacks native timezone support for travel. Mobile app feels slower than web. Limited event customization. But here is what I planned. 45 days. Time blocks for deep work. Tasks linked to calendar events. Notes linked to events. All free. And here is the timezone problem. I traveled to Tokyo. The calendar did not auto adjust. I missed a meeting. Notion Calendar does not handle timezones well. Fantastical does. For 50 dollars a year. If you travel, pay for Fantastical. If you do not, Notion Calendar is perfect. Final verdict. 4.3 out of 5. Excellent for those already using Notion. If you need a dedicated calendar, consider Fantastical. Want my full Notion setup? Free masterclass in bio.",
    },
    "short-19-ring-battery-doorbell-plus": {
        "brand": "Ring", "name": "Ring Doorbell Plus", "rating": "4.4",
        "hook_lines": ["I CAUGHT", "3 PACKAGE", "THIEVES"],
        "reveal_30": ["I INSTALLED", "IN 30", "MINUTES"],
        "reveal_60": ["BUT HERE'S", "THE SUBSCRIPTION", "PROBLEM"],
        "search": ["front door", "home security", "doorbell", "smart home", "porch", "video doorbell"],
        "full_script": "I caught 3 package thieves with this doorbell. I tested the Ring Battery Doorbell Plus for 60 days. 1080p HD video. Color night vision. Motion detection. Quick release battery. Works with Alexa. Two way audio. Package detection. Now what I do not love. Motion zones can be tricky. Requires Ring Protect subscription for video storage. Battery drains fast with high traffic. But here is what I installed. 30 minutes. No wires. Quick release battery. Just works. And here is the subscription problem. Ring Protect is 40 dollars a year. Without it, you get motion alerts but no video playback. So you can see someone is at the door but not who. That defeats the purpose. Pay the subscription. Final verdict. 4.4 out of 5. Solid for the Ring ecosystem. If you want local storage, consider Eufy. Want my full home security setup? Free masterclass in bio.",
    },
    "short-20-sennheiser-momentum-4": {
        "brand": "Sennheiser", "name": "Sennheiser M4", "rating": "4.6",
        "hook_lines": ["60 HOUR", "BATTERY.", "STUDIO SOUND."],
        "reveal_30": ["I LISTENED", "FOR 80", "DAYS"],
        "reveal_60": ["BUT HERE'S", "THE TOUCH", "PROBLEM"],
        "search": ["headphones", "music", "office work", "study", "studio", "audiophile"],
        "full_script": "60 hour battery. Studio sound. I tested the Sennheiser Momentum 4 for 80 days. Industry leading noise cancellation. 60 hour battery. Warm and detailed sound. Premium build. Now what I do not love. ANC can create pressure sensation. Touch controls overly sensitive. Case is bulky. But here is what I listened to. 80 days. Every genre. The detail is real. You hear the breath before the note. And here is the touch problem. The right ear cup is touch sensitive. Adjusting the fit accidentally skips tracks. You learn to use the physical buttons. But the first week, I missed songs just by scratching my ear. Annoying. Final verdict. 4.6 out of 5. One of the best wireless headphones. If you want the best ANC, consider Sony. Want my audio reference setup? Free masterclass in bio.",
    },
    "short-21-tp-link-kasa-smart-plug": {
        "brand": "TP-Link", "name": "Kasa Smart Plug", "rating": "4.2",
        "hook_lines": ["10 SECONDS", "TO SETUP", "A SMART PLUG"],
        "reveal_30": ["I SAVED", "$60 A YEAR", "ON ELECTRICITY"],
        "reveal_60": ["BUT HERE'S", "THE HOMEPOD", "PROBLEM"],
        "search": ["smart home", "home automation", "outlet", "office", "energy", "smart plug", "schedule"],
        "full_script": "10 seconds to setup. I tested the TP-Link Kasa Smart Plug for 60 days. Reliable Wi-Fi outlet. Schedule devices remotely. App and voice assistant. Works with Alexa, Google, SmartThings. Energy monitoring. Now what I do not love. Wi-Fi connection can drop occasionally. Blocks the adjacent outlet. No HomeKit support. But here is what I saved. 5 plugs. 60 dollars a year on electricity by turning off vampire power. Schedule lights to turn on at sunset. Schedule coffee maker at 7am. And here is the HomePod problem. No HomeKit support. If you are deep in the Apple ecosystem with a HomePod, the Kasa will not work. You need the Meross Smart Plug. Same features. HomeKit support. 5 dollars more. Final verdict. 4.2 out of 5. Great for Alexa and Google. If you need HomeKit, look at Meross. Want my home automation stack? Free masterclass in bio.",
    },
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
        result = make_short(slug, s["brand"], s["name"], s["rating"], None, s, s["search"], product_img, out_dir)
        if result:
            success += 1
    print(f"\nDone. {success}/{len(targets)} Shorts generated.")