#!/usr/bin/env python3
"""
Uzi Network — Product Image Scraper v2
Tries Wikipedia → Brand website → Brand CDN → Pexels
"""
import os
import sys
import json
import re
import urllib.request
import urllib.parse
import shutil
from pathlib import Path

ASSET_DIR = Path("/home/ubuntu/projects/uzi-network/src/assets/reviews")
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# (slug, brand, og_urls, wiki_title, fallback_search)
PRODUCTS = [
    ("macbook-pro-m5", "Apple", ["https://www.apple.com/shop/buy-mac/macbook-pro"], "MacBook Pro", "macbook pro"),
    ("sony-wh-1000xm6", "Sony", ["https://www.sony.com/en/products/headphones/wh-1000xm6", "https://www.sony.com/electronics/headphones/wh-1000xm6"], "Sony WH-1000XM5", "sony wh-1000xm6"),
    ("garmin-fenix-9-solar", "Garmin", ["https://www.garmin.com/en-US/p/1165872/fenix-9-solar"], "Garmin Fenix", "garmin fenix"),
    ("logitech-mx-master-4", "Logitech", ["https://www.logitech.com/en-us/products/mice/mx-master-4.html"], "Logitech", "logitech mx master"),
    ("aqara-u200", "Aqara", ["https://www.aqara.com/us/smart-door-lock-u200"], "Aqara", "aqara smart lock"),
    ("notion-calendar", "Notion", ["https://www.notion.so/product/calendar"], "Notion (productivity software)", "notion calendar app"),
    ("claude-4-sonnet", "Anthropic", ["https://www.anthropic.com/claude"], "Anthropic", "anthropic claude"),
    ("anker-powercore-10k", "Anker", ["https://www.anker.com/products/a1387-powercore-10000"], "Anker Innovations", "anker power bank"),
    ("anker-737-power-bank", "Anker", ["https://www.anker.com/products/737-power-bank"], "Anker Innovations", "anker 737 power bank"),
    ("anker-nano-ii-65w", "Anker", ["https://www.anker.com/products/711-charger"], "Anker Innovations", "anker nano charger"),
    ("anker-727-charging-station", "Anker", ["https://www.anker.com/products/727-charging-station"], "Anker Innovations", "anker charging station"),
    ("anker-543-usb-c-hub", "Anker", ["https://www.anker.com/products/a8380-543-usb-c-hub"], "Anker Innovations", "anker usb c hub"),
    ("anker-soundcore-life-q35", "Anker", ["https://www.anker.com/products/a3033-life-q35"], "Anker Innovations", "soundcore life q35 headphones"),
    ("eero-max-7", "eero", ["https://www.eero.com/products/eero-max-7"], "Eero", "eero router"),
    ("ring-battery-doorbell-plus", "Ring", ["https://ring.com/products/video-doorbells/battery-doorbell-plus"], "Ring (company)", "ring video doorbell"),
    ("tp-link-kasa-smart-plug", "TP-Link", ["https://www.tp-link.com/us/smart-home/kasa/hs103/"], "TP-Link", "kasa smart plug"),
    ("govee-glide-wall-light", "Govee", ["https://us.govee.com/products/glide-wall-light"], "Govee", "govee rgb light"),
    ("apple-airpods-pro-3", "Apple", ["https://www.apple.com/shop/buy-airpods/airpods-pro"], "AirPods Pro", "airpods pro"),
    ("bose-quietcomfort-ultra", "Bose", ["https://www.bose.com/p/headphones/quietcomfort-ultra-headphones"], "Bose Corporation", "bose headphones"),
    ("sennheiser-momentum-4", "Sennheiser", ["https://www.sennheiser-hearing.com/momentum-4"], "Sennheiser", "sennheiser momentum"),
    ("jackery-explorer-1000-v2", "Jackery", ["https://www.jackery.com/products/explorer-1000-v2"], "Jackery", "jackery portable power station"),
    ("garmin-instinct-2-solar", "Garmin", ["https://www.garmin.com/en-US/p/975174/instinct-2-solar"], "Garmin Fenix", "garmin instinct watch"),
]


def fetch_url(url, headers=None, timeout=15):
    headers = headers or {"User-Agent": "Mozilla/5.0 (UziNetwork/1.0; contact@uzinetwork.store)"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers


def get_wikipedia_thumb(wiki_title, width=1000):
    api_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "titles": wiki_title, "prop": "pageimages",
        "format": "json", "piprop": "original|thumbnail",
        "pithumbsize": str(width), "redirects": 1,
    })
    try:
        data, _ = fetch_url(api_url)
        j = json.loads(data.decode())
        pages = j.get("query", {}).get("pages", {})
        for p in pages.values():
            if "original" in p:
                return p["original"]["source"]
            if "thumbnail" in p:
                return p["thumbnail"]["source"]
    except Exception as e:
        print(f"  ! Wiki API: {e}")
    return None


def get_og_image(url):
    try:
        html, _ = fetch_url(url)
        text = html.decode("utf-8", errors="ignore")
        for pat in [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+property=["\']og:image:secure_url["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(1)
    except Exception as e:
        print(f"  ! OG: {e}")
    return None


def get_pexels_photo(query, orientation="portrait"):
    api_key = os.environ.get("PEXELS_API_KEY")
    if not api_key:
        return None
    url = f"https://api.pexels.com/v1/search?{urllib.parse.urlencode({'query': query, 'per_page': 5, 'orientation': orientation})}"
    try:
        req = urllib.request.Request(url, headers={"Authorization": api_key, "User-Agent": "UziNetwork/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        photos = data.get("photos", [])
        if photos:
            # Pick the best looking (largest portrait)
            for p in photos:
                src = p.get("src", {})
                img_url = src.get("portrait") or src.get("large2x") or src.get("large")
                if img_url:
                    return img_url
    except Exception as e:
        print(f"  ! Pexels: {e}")
    return None


def download_to(url, dest):
    try:
        data, _ = fetch_url(url)
        if len(data) < 5000:  # probably a 404 placeholder
            return False
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  ! Download: {e}")
    return False


def fetch_product_image(slug, brand, og_urls, wiki_title, pexels_query):
    out = ASSET_DIR / f"{slug}.jpg"
    if out.exists() and out.stat().st_size > 20000:
        print(f"  ✓ {slug} (cached, {out.stat().st_size // 1024} KB)")
        return True
    print(f"\n=== {slug} ===")

    # 1. Brand website OG image
    for u in og_urls:
        url = get_og_image(u)
        if url and download_to(url, out):
            print(f"  ✓ Brand OG: {out.stat().st_size // 1024} KB")
            return True

    # 2. Wikipedia
    url = get_wikipedia_thumb(wiki_title)
    if url and download_to(url, out):
        # Reject logos (less than 50KB for Wikipedia tends to be a logo)
        if out.stat().st_size > 50000:
            print(f"  ✓ Wikipedia: {out.stat().st_size // 1024} KB")
            return True
        else:
            out.unlink(missing_ok=True)

    # 3. Pexels fallback
    url = get_pexels_photo(pexels_query)
    if url and download_to(url, out):
        print(f"  ✓ Pexels fallback: {out.stat().st_size // 1024} KB")
        return True

    print(f"  ! No image found")
    return False


if __name__ == "__main__":
    # Load Pexels key
    env_path = Path.home() / ".hermes" / ".social-credentials"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("export PEXELS_API_KEY="):
                os.environ["PEXELS_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    targets = [p for p in PRODUCTS if p[0] == which] if which != "all" else PRODUCTS
    found, missing = 0, []
    for slug, brand, og_urls, wiki, query in targets:
        if fetch_product_image(slug, brand, og_urls, wiki, query):
            found += 1
        else:
            missing.append(slug)
    print(f"\nDone. {found}/{len(targets)} images.")
    if missing:
        print(f"Missing: {missing}")
