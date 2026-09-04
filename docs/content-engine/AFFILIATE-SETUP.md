# Affiliate Setup — Current State

## Amazon Associates
- **Associate ID:** uzinetwork20-20
- **Tag format:** `?tag=uzinetwork20-20` (or per-product like `uzi-macbook-m5-20`)
- **Status:** Live. All review pages use this tag.
- **URL pattern:** `https://www.amazon.com?tag=uzinetwork20-20`

## Per-product tags (already set in frontmatter)
- macbook-pro-m5 → uzi-macbook-m5-20
- anker-737-power-bank → uzi-anker-737-20
- ... (each review has its own)

## Tracking
- Plausible analytics tracks `affiliate_click` events
- Each click logs slug + network

## What this means for video production
- Every video CTA should link to https://uzi.network.store/reviews/{slug}
- The slug pages have the actual Amazon/direct affiliate links with our tag
- We don't need to encode affiliate URLs in the video itself — just the short URL

## Sites
- Live: https://uzi.network.store
- All review pages: https://uzi.network.store/reviews/{slug}
