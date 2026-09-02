#!/usr/bin/env python3
"""
Uzi Network — Masterclass Lesson Audio Producer (single-lesson)
"""
import os
import re
import json
import urllib.request
import sys
import time
from pathlib import Path

OUT_DIR = Path("/home/ubuntu/projects/uzi-network/public/audio/masterclass")
OUT_DIR.mkdir(parents=True, exist_ok=True)

env_path = Path.home() / ".hermes" / ".social-credentials"
for line in env_path.read_text().splitlines():
    if line.startswith("export ELEVENLABS_API_KEY="):
        os.environ["ELEVENLABS_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

api_key = os.environ["ELEVENLABS_API_KEY"]
VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17"

target = int(sys.argv[1]) if len(sys.argv) > 1 else None
src = open("/home/ubuntu/projects/uzi-network/src/pages/masterclass/[slug].astro").read()
pattern = re.compile(r"(\d+):\s*\{[^}]*?transcript:\s*`([^`]+)`", re.DOTALL)

for num, transcript in pattern.findall(src):
    if target and int(num) != target:
        continue
    clean = re.sub(r'\s+', ' ', transcript).strip()
    out_path = OUT_DIR / f"lesson-{num}.mp3"
    if out_path.exists() and out_path.stat().st_size > 10000:
        print(f"Lesson {num}: cached ({out_path.stat().st_size//1024} KB)")
        continue
    print(f"Lesson {num}: {len(clean.split())} words...")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    payload = {
        "text": clean,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(),
                headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                with open(out_path, "wb") as f:
                    f.write(resp.read())
            print(f"  ✓ {out_path.stat().st_size//1024} KB")
            break
        except Exception as e:
            print(f"  ! Attempt {attempt+1}: {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                print(f"  ✗ Failed after 3 attempts")
