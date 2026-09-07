#!/usr/bin/env python3
"""
find_sponsor_emails.py — Use Hunter.io to find partner/marketing emails at target companies.

Usage:
    1. Sign up at https://hunter.io (free: 50 credits/month)
    2. Get API key from https://hunter.io/api-keys
    3. Save: export HUNTER_API_KEY='your_key'
    4. Run: python3 find_sponsor_emails.py

Output: docs/strategy/sponsor-emails.csv
"""
import os
import sys
import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

API_KEY = os.environ.get("HUNTER_API_KEY")
if not API_KEY:
    print("ERROR: HUNTER_API_KEY not set")
    print("Sign up at https://hunter.io, get a key, then:")
    print("  export HUNTER_API_KEY='your_key'")
    sys.exit(1)

# 30 target companies with their domains
COMPANIES = [
    ("Anthropic", "anthropic.com"),
    ("Jasper AI", "jasper.ai"),
    ("Make.com", "make.com"),
    ("Surfer SEO", "surferseo.com"),
    ("Copy.ai", "copy.ai"),
    ("Writesonic", "writesonic.com"),
    ("Pictory", "pictory.ai"),
    ("ElevenLabs", "elevenlabs.io"),
    ("Notion", "notion.so"),
    ("Perplexity", "perplexity.ai"),
    ("Vercel", "vercel.com"),
    ("Linear", "linear.app"),
    ("Raycast", "raycast.com"),
    ("Superhuman", "superhuman.com"),
    ("Loom", "loom.com"),
    ("Figma", "figma.com"),
    ("Cursor", "cursor.sh"),
    ("Warp", "warp.dev"),
    ("Arc Browser", "arc.net"),
    ("Mem", "mem.ai"),
    ("Descript", "descript.com"),
    ("Framer", "framer.com"),
    ("Webflow", "webflow.com"),
    ("Bubble", "bubble.io"),
    ("Retool", "retool.com"),
    ("Zapier", "zapier.com"),
    ("Airtable", "airtable.com"),
    ("Calendly", "calendly.com"),
    ("Stripe Press", "stripe.com"),
    ("Perplexity", "perplexity.ai"),
]


def find_partnerships_email(domain, retries=2):
    """Find the partnerships/marketing/affiliate email at a domain."""
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&limit=10&api_key={API_KEY}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "UziNetwork/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 429 and retries > 0:
            time.sleep(2)
            return find_partnerships_email(domain, retries - 1)
        return {"error": f"HTTP {e.code}", "body": e.read().decode()[:200]}
    except Exception as e:
        return {"error": str(e)}


def main():
    output = Path("/home/ubuntu/projects/uzi-network/docs/strategy/sponsor-emails.csv")
    output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Finding partnership emails for {len(COMPANIES)} companies...")
    print(f"Free tier: 50 credits. Each call = 1 credit.")
    print()

    results = []
    for name, domain in COMPANIES[:30]:
        data = find_partnerships_email(domain)
        if "data" in data:
            emails = data["data"].get("emails", [])
            # Find partnerships/marketing/affiliate role
            best = None
            for e in emails:
                role = (e.get("position") or "").lower()
                value = (e.get("value") or "").lower()
                if any(k in role for k in ["partner", "affiliate", "marketing", "growth", "business"]):
                    best = e
                    break
                if any(k in value for k in ["partner", "affiliate", "marketing", "hello@", "info@"]):
                    best = e
                    break
            # Fall back to first
            if not best and emails:
                best = emails[0]
            if best:
                results.append({
                    "company": name,
                    "domain": domain,
                    "email": best.get("value"),
                    "name": f"{best.get('first_name', '')} {best.get('last_name', '')}".strip(),
                    "role": best.get("position", ""),
                    "score": best.get("confidence", 0),
                })
                print(f"  ✓ {name}: {best.get('value')} ({best.get('position', 'no role')})")
            else:
                results.append({"company": name, "domain": domain, "email": "", "name": "", "role": "", "score": 0})
                print(f"  - {name}: no emails found")
        else:
            results.append({"company": name, "domain": domain, "email": "", "name": "", "role": "", "score": 0, "error": data.get("error", "")})
            print(f"  ✗ {name}: {data.get('error', 'unknown')}")
        time.sleep(1)  # Rate limit

    # Write CSV
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "domain", "email", "name", "role", "score"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    print(f"\n✓ Saved to {output}")
    print(f"  Total found: {sum(1 for r in results if r.get('email'))}/{len(results)}")
    print(f"  Best targets: {sorted([r for r in results if r.get('email')], key=lambda x: -x.get('score', 0))[:5]}")


if __name__ == "__main__":
    main()
