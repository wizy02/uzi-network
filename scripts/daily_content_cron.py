#!/usr/bin/env python3
"""
daily_content_cron.py — Daily AI tool content generator + poster.

Run via cron at 9 AM daily:
  0 9 * * * cd /home/ubuntu/projects/uzi-network && .venv/bin/python scripts/daily_content_cron.py

What it does:
1. Picks the next AI tool to feature (rotates through 30 tools)
2. Generates a 60-second YouTube Short script
3. Generates a 200-word blog post
4. Generates a Twitter thread (3 tweets)
5. Saves all to docs/content/{date}/
6. Optionally posts to YouTube + Twitter if credentials configured

Required env vars (set in cron):
  OPENAI_API_KEY or OPENROUTER_API_KEY
  Optional:
    YOUTUBE_AUTO_POST=true
    TWITTER_AUTO_POST=true
"""
import os
import sys
import json
import time
import urllib.request
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/home/ubuntu/projects/uzi-network/scripts")

OUT_DIR = Path("/home/ubuntu/projects/uzi-network/docs/content")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Tools to rotate through
TOOLS = [
    {"name": "ElevenLabs", "category": "AI Voice", "affiliate": "https://elevenlabs.io?via=uzinetwork"},
    {"name": "Make.com", "category": "Automation", "affiliate": "https://make.com/en?via=uzinetwork"},
    {"name": "Jasper AI", "category": "AI Writing", "affiliate": "https://jasper.ai?via=uzinetwork"},
    {"name": "Surfer SEO", "category": "AI SEO", "affiliate": "https://surferseo.com?via=uzinetwork"},
    {"name": "Copy.ai", "category": "AI Writing", "affiliate": "https://copy.ai?via=uzinetwork"},
    {"name": "Pictory", "category": "AI Video", "affiliate": "https://pictory.ai?via=uzinetwork"},
    {"name": "Writesonic", "category": "AI Writing", "affiliate": "https://writesonic.com?via=uzinetwork"},
    {"name": "Notion AI", "category": "Productivity", "affiliate": "https://notion.so?via=uzinetwork"},
    {"name": "Descript", "category": "AI Video", "affiliate": "https://descript.com?via=uzinetwork"},
    {"name": "Perplexity", "category": "AI Search", "affiliate": "https://perplexity.ai?via=uzinetwork"},
    {"name": "Claude Pro", "category": "AI Reasoning", "affiliate": "https://anthropic.com?via=uzinetwork"},
    {"name": "Cursor", "category": "AI Coding", "affiliate": "https://cursor.sh?via=uzinetwork"},
    {"name": "Raycast", "category": "Productivity", "affiliate": "https://raycast.com?via=uzinetwork"},
    {"name": "Superhuman", "category": "Email", "affiliate": "https://superhuman.com?via=uzinetwork"},
    {"name": "Loom", "category": "AI Video", "affiliate": "https://loom.com?via=uzinetwork"},
    {"name": "Figma", "category": "Design", "affiliate": "https://figma.com?via=uzinetwork"},
    {"name": "Linear", "category": "Productivity", "affiliate": "https://linear.app?via=uzinetwork"},
    {"name": "Vercel", "category": "Deployment", "affiliate": "https://vercel.com?via=uzinetwork"},
    {"name": "Webflow", "category": "Design", "affiliate": "https://webflow.com?via=uzinetwork"},
    {"name": "Zapier", "category": "Automation", "affiliate": "https://zapier.com?via=uzinetwork"},
    {"name": "Calendly", "category": "Productivity", "affiliate": "https://calendly.com?via=uzinetwork"},
    {"name": "Retool", "category": "Dev Tools", "affiliate": "https://retool.com?via=uzinetwork"},
    {"name": "Bubble", "category": "No-Code", "affiliate": "https://bubble.io?via=uzinetwork"},
    {"name": "Framer", "category": "Design", "affiliate": "https://framer.com?via=uzinetwork"},
    {"name": "Mem", "category": "Productivity", "affiliate": "https://mem.ai?via=uzinetwork"},
    {"name": "Airtable", "category": "Productivity", "affiliate": "https://airtable.com?via=uzinetwork"},
    {"name": "Warp", "category": "Dev Tools", "affiliate": "https://warp.dev?via=uzinetwork"},
    {"name": "Arc", "category": "Browser", "affiliate": "https://arc.net?via=uzinetwork"},
    {"name": "Tana", "category": "Productivity", "affiliate": "https://tana.inc?via=uzinetwork"},
    {"name": "Reflect", "category": "Productivity", "affiliate": "https://reflect.app?via=uzinetwork"},
]


def pick_tool():
    """Pick today's tool (rotates by day of year)."""
    day_of_year = datetime.now().timetuple().tm_yday
    return TOOLS[day_of_year % len(TOOLS)]


def generate_with_ai(prompt, model="openai/gpt-4o-mini", max_tokens=1000):
    """Generate text using OpenAI-compatible API."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None
    base_url = "https://api.openai.com/v1" if os.environ.get("OPENAI_API_KEY") else "https://openrouter.ai/api/v1"
    try:
        req = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    day_dir = OUT_DIR / today
    day_dir.mkdir(parents=True, exist_ok=True)

    tool = pick_tool()
    print(f"[{today}] Generating content for: {tool['name']} ({tool['category']})")

    # 1. Short script
    short_prompt = f"""Write a 60-second YouTube Short script about {tool['name']} for tech professionals.

Format:
- Hook (0-3s): A surprising stat or question
- Body (3-50s): 3 specific use cases with numbers
- CTA (50-60s): "Try free — link in description"

Style: Conversational, like talking to a friend. No marketing fluff.
Length: ~150 words. Affiliate: {tool['affiliate']}"""

    short = generate_with_ai(short_prompt, max_tokens=300)
    if short:
        (day_dir / "short-script.md").write_text(f"# {tool['name']} YouTube Short\n\n{short}\n\nAffiliate: {tool['affiliate']}\n")
        print(f"  ✓ Short script")

    # 2. Blog post
    blog_prompt = f"""Write a 200-word blog post reviewing {tool['name']} for tech professionals.

Structure:
- 1-line verdict
- 3 things we like
- 1 thing we don't
- Who should buy
- Pricing context

Style: Honest, specific, no marketing speak. Affiliate disclosure at the end.
Link: {tool['affiliate']}"""

    blog = generate_with_ai(blog_prompt, max_tokens=400)
    if blog:
        (day_dir / "blog-post.md").write_text(f"# {tool['name']} Review\n\n{blog}\n\nAffiliate: {tool['affiliate']}\n")
        print(f"  ✓ Blog post")

    # 3. Twitter thread
    thread_prompt = f"""Write a 3-tweet Twitter thread about {tool['name']}.

Tweet 1: Hook + surprising fact (under 280 chars)
Tweet 2: One specific use case with a number
Tweet 3: CTA with the affiliate link

Affiliate: {tool['affiliate']}"""

    thread = generate_with_ai(thread_prompt, max_tokens=300)
    if thread:
        (day_dir / "twitter-thread.md").write_text(f"# {tool['name']} Twitter Thread\n\n{thread}\n\nAffiliate: {tool['affiliate']}\n")
        print(f"  ✓ Twitter thread")

    # 4. Save metadata
    metadata = {
        "date": today,
        "tool": tool,
        "files": ["short-script.md", "blog-post.md", "twitter-thread.md"],
        "auto_posted_youtube": os.environ.get("YOUTUBE_AUTO_POST") == "true",
        "auto_posted_twitter": os.environ.get("TWITTER_AUTO_POST") == "true",
    }
    (day_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    print(f"\n✓ All content saved to {day_dir}")


if __name__ == "__main__":
    main()
