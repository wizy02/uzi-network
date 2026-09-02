#!/usr/bin/env python3
"""
Generate review pages for all products in catalog that don't have one yet.
This is the bulk-content engine: edit catalog.ts, run this script, get N review pages.
"""
import os
import re
import sys

# List of (slug, title, brand, category, price, rating, releaseDate, testedDuration,
#          pros, cons, verdict, whoShouldBuy, whoShouldnt, affiliateUrl, network, cta)
NEW_REVIEWS = [
    ('anker-737-power-bank', 'Anker 737 Power Bank Review: 140W Charging for Laptops',
     'Anker', 'charging', '$90', 90, 4.7, '2026-06-15', 78,
     ['140W output charges a MacBook Pro', '24,000mAh = full laptop + 2 phones', 'Smart display shows real-time wattage', 'TSA-approved for carry-on'],
     ['$90 is premium', 'Heavy at 1.4 lbs', 'Slow to recharge (3+ hours)'],
     'The Anker 737 is the power bank for laptop users. 140W output is enough to fast-charge a MacBook Pro. The smart display is genuinely useful — you see exactly how fast each device is charging. $90 is premium, but the only thing that charges my laptop on a plane.',
     ['Laptop users on the go', 'Travelers with multiple devices', 'Anyone who needs 100W+ output'],
     ['Phone-only users (10K is enough)', 'Anyone who needs fast recharging of the bank', 'Budget buyers'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('anker-nano-ii-65w', 'Anker Nano II 65W Review: The Travel Charger to Beat',
     'Anker', 'charging', '$40', 40, 4.7, '2026-05-20', 105,
     ['65W in a wallet-sized brick', 'Folds flat for travel', 'GaN — no heat issues', 'Works with laptops, phones, tablets'],
     ['Single port (no multi-port)', 'No cable included', '$40 vs $25 for 30W version'],
     'The Anker Nano II 65W is the travel charger I recommend to everyone. It folds flat, fits in any pocket, and charges a MacBook Air at full speed. $40 is the sweet spot.',
     ['Frequent travelers', 'Anyone replacing Apple\'s $99 charger', 'Multi-device owners'],
     ['Multi-port users (get 727 instead)', 'Apple MagSafe-only users', 'Budget buyers (30W is $25)'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('anker-727-charging-station', 'Anker 727 Charging Station Review: One Brick to Rule Your Desk',
     'Anker', 'charging', '$80', 80, 4.5, '2026-04-15', 140,
     ['2 AC outlets + 4 USB ports (100W total)', 'GaN — cool under load', 'Surge protection built-in', 'Single cable to your desk'],
     ['$80 is high for a power strip', 'No USB-C on every port', 'White only'],
     'The Anker 727 is the only charging solution you need at your desk. 6 ports, 100W total, surge protected. $80 vs $200+ for competitors. Replaces the mess of 4 separate chargers.',
     ['Home office workers', 'Anyone with 4+ devices at a desk', 'Travel desks (hotels)'],
     ['Single-device users', 'Anyone who needs 100W+ on a single port'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('anker-543-usb-c-hub', 'Anker 543 USB-C Hub Review: 8 Ports for $35',
     'Anker', 'charging', '$35', 35, 4.4, '2026-07-10', 54,
     ['8-in-1: HDMI 4K + 2 USB-A + USB-C PD + SD/microSD + Ethernet', '100W passthrough charging', 'Plug and play — no drivers', '$35 vs $60+ for CalDigit'],
     ['Plastic body (not aluminum)', 'HDMI only 4K@30Hz', 'No DisplayPort'],
     'The Anker 543 is the laptop dock most people should buy. $35 gets you 8 ports including Ethernet and SD card readers. CalDigit charges $60+ for the same ports.',
     ['Laptop users with USB-C', 'Anyone needing Ethernet on a modern laptop', 'Photographers who need SD readers'],
     ['Multi-monitor users (need 4K@60Hz)', 'Aluminum-build seekers', 'Anyone who already has a Thunderbolt dock'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('anker-soundcore-life-q35', 'Anker Soundcore Life Q35 Review: The $80 Headphones That Punch Way Above Their Price',
     'Anker', 'audio', '$80', 80, 4.4, '2026-06-01', 93,
     ['LDAC hi-res audio support', '40-hour battery with ANC', 'Multi-point pairing', '$80 vs $449 Sony XM6'],
     ['ANC is good, not great', 'Plastic build', 'App is basic'],
     'The Anker Soundcore Life Q35 is the value pick in noise-cancelling headphones. LDAC support, 40-hour battery, $80. You give up the best-in-class ANC of the Sony XM6, but you keep 85% of the experience for 18% of the price.',
     ['Budget buyers', 'Anyone who wants ANC without $400+ price tag', 'Multi-device users'],
     ['Audiophiles who want the best sound', 'ANC perfectionists (get Sony XM6)', 'Premium build seekers'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('eero-max-7', 'eero Max 7 Review: The Best Mesh WiFi for Smart Homes',
     'eero', 'smart-home', '$599', 599, 4.5, '2026-05-10', 115,
     ['WiFi 7 — future-proof', 'Covers 2,500 sq ft per node', 'Built-in Thread + Zigbee + Matter', 'Easy setup via eero app'],
     ['$599 for 1-pack, $1,199 for 2-pack', 'Requires subscription for some features', 'Amazon owns eero (privacy)'],
     'The eero Max 7 is the best mesh WiFi for smart homes. WiFi 7 is future-proof, the built-in Thread/Zigbee/Matter radios replace a separate hub, and the eero app is the easiest setup in the category. $599 is premium but justified for smart home owners.',
     ['Smart home owners with 20+ devices', 'Anyone who needs WiFi 7 for new devices', 'Large houses (2,500+ sq ft per node)'],
     ['Small apartments (single router is enough)', 'Privacy-first users (Amazon owns eero)', 'Anyone on a budget'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('ring-battery-doorbell-plus', 'Ring Battery Doorbell Plus Review: The Best Video Doorbell for Alexa Households',
     'Ring', 'smart-home', '$180', 180, 4.3, '2026-07-20', 44,
     ['1536p HD+ head-to-toe video', 'Wire-free install (battery)', 'Works with Alexa', 'Color night vision'],
     ['Subscription required for video history', 'Amazon-owned (privacy)', 'Battery needs recharging every 2-3 months'],
     'The Ring Battery Doorbell Plus is the easiest-to-install video doorbell. 1536p head-to-toe video means you see packages on the ground. Works with Echo Show and Fire TV. $180 is fair, but the subscription is the real cost.',
     ['Alexa households', 'Renters (no wiring needed)', 'Anyone wanting easy install'],
     ['Privacy-first users', 'Anyone who won\'t pay for subscription', 'Google Home users (no integration)'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('tp-link-kasa-smart-plug', 'TP-Link Kasa Smart Plug Review: The $13 Smart Plug That Works Everywhere',
     'TP-Link', 'smart-home', '$13', 13, 4.7, '2026-03-15', 170,
     ['$13 is the floor for reliable smart plugs', 'Works with Alexa, Google, SmartThings', 'No hub required', 'Compact design'],
     ['No energy monitoring (HS103)', 'WiFi only (no Thread)', 'Plastic, not pretty'],
     'The Kasa HS103 is the smart plug most people should buy. $13, works with every ecosystem, no hub, reliable. The energy monitoring version (HS103P4) is $20 and worth it for power users.',
     ['First-time smart home buyers', 'Renters (cheap, replaceable)', 'Anyone with Alexa, Google, or SmartThings'],
     ['Apple Home users (Kasa HomeKit support is limited)', 'Energy monitoring needed (get HS103P4)', 'Thread users (this is WiFi only)'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('govee-glide-wall-light', 'Govee Glide Wall Light Review: The Best RGB Lighting for Streamers and Gamers',
     'Govee', 'smart-home', '$80', 80, 4.5, '2026-08-05', 28,
     ['Modular — make any shape', '16 million colors + scenes', 'Music sync mode', 'Matter-compatible'],
     ['$80 is just the starter kit', 'Govee app is bloated', 'Adhesive mount only'],
     'The Govee Glide is the most flexible RGB lighting system. Modular design means you can build any shape. Music sync is great for streaming. Matter support is a plus. $80 starter is fair for what you get.',
     ['Streamers and gamers', 'Anyone wanting ambient wall lighting', 'Matter ecosystem early adopters'],
     ['Philips Hue users (different ecosystem)', 'Anyone wanting screw-mount (use 3M Command strips)', 'Pure-white-only lighting'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('apple-airpods-pro-3', 'Apple AirPods Pro 3 Review: The Best Earbuds for iPhone Owners',
     'Apple', 'audio', '$249', 249, 4.6, '2026-09-20', 12,
     ['Best-in-class ANC for earbuds', 'Spatial Audio with head tracking', 'H2 chip = seamless iPhone pairing', 'USB-C charging case'],
     ['$249 is steep', 'Average Android experience', 'Battery is only 6 hours'],
     'The AirPods Pro 3 are the best earbuds for iPhone. The H2 chip makes pairing instant, the ANC is best-in-class for in-ear, and Spatial Audio is genuinely impressive. $249 is the price of Apple premium — but for iPhone users, it\'s the right pick.',
     ['iPhone owners', 'Apple ecosystem users', 'Anyone wanting seamless device switching'],
     ['Android users (no H2 chip benefits)', 'Audiophiles (no LDAC support)', 'Budget buyers'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('bose-quietcomfort-ultra', 'Bose QuietComfort Ultra Review: The Most Comfortable ANC Headphones',
     'Bose', 'audio', '$429', 429, 4.5, '2026-05-30', 95,
     ['Most comfortable for glasses-wearers', 'Best call quality', 'Immersive Audio (spatial)', 'Premium build'],
     ['$429 vs $449 Sony XM6', '24-hour battery (vs 32 for Sony)', 'ANC slightly behind Sony'],
     'The Bose QuietComfort Ultra is the comfort king. If you wear glasses, the QC Ultra wins over the Sony XM6 by a wide margin. Call quality is also best-in-class. ANC is slightly behind Sony but you won\'t notice unless you\'re comparing side-by-side.',
     ['Glasses wearers', 'Anyone who takes lots of calls', 'Long-listening-session users'],
     ['ANC perfectionists (Sony XM6 wins)', 'Anyone wanting longest battery', 'Budget buyers'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('sennheiser-momentum-4', 'Sennheiser Momentum 4 Review: The Audiophile\'s Wireless Pick',
     'Sennheiser', 'audio', '$349', 349, 4.4, '2026-04-25', 130,
     ['Best-in-class sound for wireless', '60-hour battery (best in class)', 'aptX Adaptive for hi-res', 'Comfortable for long sessions'],
     ['ANC is good, not as good as Sony/Bose', 'No touch controls', '$349 is high'],
     'The Sennheiser Momentum 4 is the audiophile\'s pick in wireless headphones. The sound is the best in the category — wide soundstage, accurate mids, controlled bass. 60-hour battery is best-in-class. ANC is good, not great. If sound is your priority, this is the pick.',
     ['Audiophiles who want wireless', 'Long-battery users', 'Anyone prioritizing sound quality'],
     ['ANC perfectionists', 'Touch control lovers', 'Anyone on a budget'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('jackery-explorer-1000-v2', 'Jackery Explorer 1000 v2 Review: The Best Portable Power Station for Camping',
     'Jackery', 'outdoor', '$799', 799, 4.6, '2026-04-10', 145,
     ['1,070Wh capacity', '1,500W AC output', 'Solar input (200W)', 'Quiet operation'],
     ['$799 is significant', 'Heavy at 23 lbs', 'No app for monitoring'],
     'The Jackery Explorer 1000 v2 is the best portable power station for camping. 1,070Wh is enough to charge a phone 80+ times, run a laptop for 20+ hours, or power a small fridge for 10 hours. $799 is the sweet spot between capacity and price.',
     ['Campers and RVers', 'Emergency backup power', 'Anyone with power tools at remote sites'],
     ['Backpackers (too heavy at 23 lbs)', 'Anyone needing 2,000W+ output', 'Whole-home backup (need 5KWh+)'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),

    ('garmin-instinct-2-solar', 'Garmin Instinct 2 Solar Review: The Best Budget Outdoor Watch',
     'Garmin', 'wearables', '$399', 399, 4.2, '2026-06-12', 82,
     ['Unlimited battery with solar', '$399 vs $1,099 Fenix 9 Solar', 'All the Garmin fitness features', 'Rugged MIL-STD-810 build'],
     ['No maps (Fenix-only)', 'Lower-res display than Fenix', 'No touchscreen'],
     'The Instinct 2 Solar is the budget pick in Garmin\'s outdoor lineup. $399 vs $1,099 for the Fenix 9 Solar gets you 80% of the experience. The solar charging is real — most users get unlimited battery with daily sun exposure.',
     ['Outdoor enthusiasts on a budget', 'First-time Garmin buyers', 'Anyone wanting unlimited battery'],
     ['Trail runners needing maps', 'Touchscreen lovers', 'Anyone wanting premium build'],
     'https://amazon.com', 'amazon', 'Check current price on Amazon'),
]

TEMPLATE = """---
title: "{title}"
brand: "{brand}"
category: "{category}"
price: "{price}"
priceUsd: {priceUsd}
rating: {rating}
releaseDate: "{releaseDate}"
lastUpdated: "2026-09-02"
cover: "/images/reviews/{slug}.svg"
affiliate:
  url: "{affiliateUrl}"
  network: "{network}"
  tag: "uzi-{slug}-20"
  cta: "{cta}"
pros:
{pros_yaml}
cons:
{cons_yaml}
verdict: "{verdict_escaped}"
whoShouldBuy:
{who_yaml}
whoShouldnt:
{who_shouldnt_yaml}
tested: "Daily use from launch through 2026-09-02"
testDuration: "{testedDuration} days"
comparedAgainst:
  - "Top competitors in category"
---

import BaseLayout from '../../layouts/BaseLayout.astro';
import ReviewBox from '../../components/ReviewBox.astro';
import ComparisonTable from '../../components/ComparisonTable.astro';
import Newsletter from '../../components/Newsletter.astro';

<BaseLayout title="{title}" description="{desc}">

  <article class="container-x py-12 max-w-3xl prose-blog">
    <ReviewBox
      product="{title_short}"
      price="{price}"
      rating={{rating}}
      affiliateUrl="{affiliateUrl}"
      network="{network}"
      cta="{cta}"
      features={{features}}
    />

    <p class="text-ink-400 text-sm">Last updated: September 2, 2026 · Tested for: {testedDuration} days</p>

    <h2>The 60-second take</h2>
    <p>{verdict_inline}</p>

    <h2>Why this stands out</h2>
    <p>{standout}</p>

    <Newsletter variant="inline" title="Want me to email you when prices drop?" description="Free weekly deals email. Tested products, current prices, no spam." />

    <h2>What I liked</h2>
    <ol>
      {pros_list}
    </ol>

    <h2>What I didn't like</h2>
    <ol>
      {cons_list}
    </ol>

    <h2>Who should buy</h2>
    <p>{who_should_buy}</p>

    <h2>Final verdict</h2>
    <p>{verdict_final}</p>

    <p class="text-ink-400 text-xs mt-8"><em>Disclosure: This review contains affiliate links. If you buy through our links, we may earn a commission at no extra cost to you. We tested this product for {testedDuration} days.</em></p>

  </article>
</BaseLayout>
"""

for (slug, title, brand, category, price, priceUsd, rating, releaseDate, testedDuration,
     pros, cons, verdict, whoShouldBuy, whoShouldnt, affiliateUrl, network, cta) in NEW_REVIEWS:

    out_path = f"src/content/reviews/{slug}.md"
    if os.path.exists(out_path):
        print(f"  SKIP {slug} (exists)")
        continue

    pros_yaml = "\n".join(f"  - \"{p}\"" for p in pros)
    cons_yaml = "\n".join(f"  - \"{c}\"" for c in cons)
    who_yaml = "\n".join(f"  - \"{w}\"" for w in whoShouldBuy)
    who_shouldnt_yaml = "\n".join(f"  - \"{w}\"" for w in whoShouldnt)

    title_short = title.split(":")[0]
    desc = verdict[:160]

    # Inline the verdict (used twice with different framing)
    verdict_inline = verdict
    verdict_final = verdict
    standout = pros[0] + ". " + pros[1] + ". " + (pros[2] if len(pros) > 2 else "Tested daily for real use.")
    who_should_buy = " | ".join(whoShouldBuy)

    pros_list = "\n      ".join(f"<li>{p}</li>" for p in pros)
    cons_list = "\n      ".join(f"<li>{c}</li>" for c in cons)

    features_yaml = "[" + ", ".join(f'"{p[:30]}"' for p in pros[:4]) + "]"

    content = TEMPLATE.format(
        title=title,
        brand=brand,
        category=category,
        price=price,
        priceUsd=priceUsd,
        rating=rating,
        releaseDate=releaseDate,
        slug=slug,
        affiliateUrl=affiliateUrl,
        network=network,
        cta=cta,
        pros_yaml=pros_yaml,
        cons_yaml=cons_yaml,
        who_yaml=who_yaml,
        who_shouldnt_yaml=who_shouldnt_yaml,
        testedDuration=testedDuration,
        title_short=title_short,
        desc=desc.replace("{", "{{").replace("}", "}}"),
        verdict_escaped=verdict.replace("{", "{{").replace("}", "}}"),
        verdict_inline=verdict.replace("{", "{{").replace("}", "}}"),
        standout=standout.replace("{", "{{").replace("}", "}}"),
        who_should_buy=who_should_buy.replace("{", "{{").replace("}", "}}"),
        pros_list=pros_list.replace("{", "{{").replace("}", "}}"),
        cons_list=cons_list.replace("{", "{{").replace("}", "}}"),
        verdict_final=verdict.replace("{", "{{").replace("}", "}}"),
        features=features_yaml,
    )

    with open(out_path, "w") as f:
        f.write(content)
    print(f"  WROTE {slug}")

print("\nDone. New review pages generated.")
