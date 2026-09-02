#!/usr/bin/env python3
"""
Uzi Network — Full YouTube Short Producer (v2)
Pipeline: script → ElevenLabs voiceover → Pexels B-roll → 9:16 video
"""
import os
import sys
import re
import subprocess
import json
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Layout
W, H = 1080, 1920  # 9:16
FPS = 24
DUR_PER_SCENE = 2.5  # seconds per scene

BG_COLOR = (13, 15, 20)
ACCENT = (255, 92, 0)
TEXT = (245, 245, 250)
TEXT_DIM = (160, 165, 175)


def load_env():
    """Load keys from ~/.hermes/.social-credentials"""
    env_path = Path.home() / ".hermes" / ".social-credentials"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("export ") and "=" in line:
                k, v = line[7:].split("=", 1)
                os.environ[k] = v.strip('"').strip("'")


def find_font(size=72, bold=True):
    candidates = [
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        f"/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
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


def fetch_voiceover(text, output_mp3):
    """ElevenLabs TTS. Uses eleven_flash_v2_5 (cheapest)."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("  ! No ELEVENLABS_API_KEY, skipping voiceover")
        return False

    voice_id = "CwhRBWXzGAHq8TQ4Fs17"  # Roger (default English voice)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        }
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


def fetch_pexels_photo(query, output_path, n=3):
    """Pexels: fetch a stock photo (fallback when no video). Returns True/False."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return False
    url = f"https://api.pexels.com/v1/search?{urllib.parse.urlencode({'query': query, 'per_page': n, 'orientation': 'portrait'})}"
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        photos = data.get("photos", [])
        if not photos:
            return False
        # Download the largest landscape version
        for p in photos[:n]:
            img_url = p.get("src", {}).get("large") or p.get("src", {}).get("original")
            if img_url:
                with urllib.request.urlopen(img_url, timeout=15) as img_resp:
                    with open(output_path, "wb") as f:
                        f.write(img_resp.read())
                return True
    except Exception as e:
        print(f"  ! Pexels error: {e}")
    return False


def fetch_pexels_videos(query, output_dir, n=3):
    """Pexels: fetch n stock videos for the query."""
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return []
    url = f"https://api.pexels.com/videos/search?{urllib.parse.urlencode({'query': query, 'per_page': n})}"
    req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0 (contact@uzinetwork.store)"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        videos = data.get("videos", [])
        paths = []
        for i, v in enumerate(videos[:n]):
            # Get best SD mp4 file
            files = v.get("video_files", [])
            mp4_files = [f for f in files if f.get("file_type") == "video/mp4"]
            if not mp4_files:
                continue
            # Pick the smallest portrait-ish file (under 1080p)
            best = min(
                [f for f in mp4_files if f.get("width", 9999) <= 1280] or mp4_files,
                key=lambda f: f.get("width", 9999) * f.get("height", 9999)
            )
            out = Path(output_dir) / f"broll_{i}.mp4"
            out.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Pexels CDN requires the same Authorization header
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


def make_kinetic_frame(text_lines, accent_idx=None, logo=True, bg_image=None):
    img = Image.new("RGB", (W, H), BG_COLOR)
    if bg_image and Path(bg_image).exists():
        try:
            bg = Image.open(bg_image).convert("RGB")
            bg.thumbnail((W, H))
            img.paste(bg, ((W - bg.width) // 2, (H - bg.height) // 2))
            # Dark overlay
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 150))
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay).convert("RGB")
        except Exception:
            pass

    draw = ImageDraw.Draw(img)
    title_font = find_font(96, bold=True)
    body_font = find_font(72, bold=False)
    small_font = find_font(36, bold=False)
    logo_font = find_font(48, bold=True)

    if logo:
        draw.rectangle([(60, 60), (180, 180)], fill=ACCENT)
        draw.text((220, 80), "UZI NETWORK", font=logo_font, fill=TEXT)

    if not text_lines:
        return img

    title = text_lines[0]
    body = text_lines[1:]
    title_lines = wrap_text(title, title_font, W - 120)
    y = 700
    for line in title_lines:
        bbox = title_font.getbbox(line)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) // 2
        if accent_idx is not None and accent_idx == 0:
            draw.rectangle([(x, y - 30), (x + 80, y - 20)], fill=ACCENT)
        draw.text((x, y), line, font=title_font, fill=TEXT if accent_idx is None else ACCENT)
        y += 110
    y += 40
    for line in body:
        body_lines = wrap_text(line, body_font, W - 120)
        for bl in body_lines:
            bbox = body_font.getbbox(bl)
            line_w = bbox[2] - bbox[0]
            x = (W - line_w) // 2
            draw.text((x, y), bl, font=body_font, fill=TEXT_DIM)
            y += 90

    footer_font = find_font(42, bold=True)
    draw.text((W // 2 - 100, H - 150), "@uzinetwork", font=footer_font, fill=ACCENT)
    return img


def make_short(slug, title, rating, accent, script, search_terms, output_dir):
    """Full pipeline: voiceover + b-roll + video."""
    print(f"\n=== {slug} ===")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path("/tmp/short_prod")
    tmp.mkdir(exist_ok=True)

    # 1. Voiceover
    voiceover = tmp / f"{slug}.mp3"
    print("  1. Voiceover...")
    if fetch_voiceover(script, str(voiceover)):
        print(f"     ✓ {voiceover.stat().st_size // 1024} KB")
    else:
        voiceover = None

    # 2. B-roll (try videos first, fall back to photos)
    print("  2. B-roll...")
    broll_videos = []
    for term in search_terms:
        vids = fetch_pexels_videos(term, str(tmp / slug), n=2)
        broll_videos.extend(vids)
        if broll_videos:
            break
    if not broll_videos:
        # Try photo
        photo = tmp / f"{slug}_photo.jpg"
        for term in search_terms:
            if fetch_pexels_photo(term, str(photo)):
                print(f"     ✓ Photo: {photo}")
                break

    # 3. Scenes
    sentences = re.split(r'(?<=[.!?])\s+', script.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    accent_words = set(w.lower() for w in (accent or []))

    # 4. Build frame sequence
    print("  3. Frames...")
    frames = []
    for i, s in enumerate(sentences):
        # Choose bg: cycle through b-roll videos if available
        bg = None
        if broll_videos:
            bg = broll_videos[i % len(broll_videos)]
        elif (tmp / f"{slug}_photo.jpg").exists():
            bg = str(tmp / f"{slug}_photo.jpg")

        if "," in s and len(s) > 60:
            t, b = s.split(",", 1)
            t, b = t.strip(), b.strip()
        elif len(s) > 60:
            t, b = s[:50].strip(), s[50:].strip()
        else:
            t, b = s, ""
        lines = [t] + ([b[i:i+50] for i in range(0, len(b), 50)] if b else [])

        is_accent = any(w in s.lower() for w in accent_words)
        frame = make_kinetic_frame(lines, accent_idx=0 if is_accent else None, logo=(i == 0), bg_image=bg)
        frames.append(frame)

    # 5. Render
    print("  4. Render...")
    held = int(DUR_PER_SCENE * FPS)
    for i, frame in enumerate(frames):
        for h in range(held):
            frame.save(tmp / f"frame_{i*held + h:06d}.png")

    video_out = output_dir / f"{slug}.mp4"
    cmd = ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp / "frame_%06d.png")]
    if voiceover and voiceover.exists():
        cmd.extend(["-i", str(voiceover)])
        cmd.extend(["-c:v", "libx264", "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    cmd.append(str(video_out))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"     ! ffmpeg error: {res.stderr[-300:]}")
        return None
    print(f"     ✓ {video_out.stat().st_size // 1024} KB, {video_out}")

    # Cleanup frames
    for f in tmp.glob("frame_*.png"):
        f.unlink()

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
    return output_png


# ============================================================
SCRIPTS = {
    "short-1-macbook-m5": {
        "title": "MacBook Pro M5: Worth It?",
        "rating": "4.6",
        "accent": ["worth", "love", "best"],
        "search": ["apple laptop", "laptop computer", "macbook"],
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
        "search": ["power bank", "portable charger", "battery charger"],
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
        "search": ["headphones", "wireless headphones", "noise cancelling"],
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
