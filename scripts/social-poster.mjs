/**
 * Uzi Network — Social Media Auto-Poster
 *
 * Reads all reviews from the catalog, generates platform-specific copy
 * for YouTube Shorts, TikTok, X, Pinterest, and Instagram Reels.
 *
 * Output: docs/social/{platform}/{slug}.md  (one file per platform per product)
 *
 * Each file is copy-paste ready. Operator pastes into the platform's
 * composer (or runs the platform API when credentials are available).
 *
 * Usage:
 *   node scripts/social-poster.mjs
 *
 * Or to generate just one platform:
 *   node scripts/social-poster.mjs youtube
 *
 * Cost: 0 (no API calls — pure templating)
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const root = join(__dirname, '..');

// Read the catalog (TS) by extracting the PRODUCTS array
// (Easier than parsing TS — we just need the structured data)
const catalogSrc = readFileSync(join(root, 'src/lib/catalog.ts'), 'utf-8');

// Simple regex extraction of products
function extractProducts(src) {
  const products = [];
  const productRegex = /\{\s*name:\s*'([^']+)',[\s\S]*?slug:\s*'([^']+)'[\s\S]*?bestFor:\s*'([^']+)'[\s\S]*?affiliateUrl:\s*'([^']+)'[\s\S]*?\}/g;
  let m;
  while ((m = productRegex.exec(src)) !== null) {
    products.push({ name: m[1], slug: m[2], bestFor: m[3], affiliateUrl: m[4] });
  }
  return products;
}

const products = extractProducts(catalogSrc);
console.log(`Found ${products.length} products in catalog.`);

// PLATFORM TEMPLATES
const templates = {
  youtube_short(slug, name, bestFor) {
    const safeName = name.split(':')[0].replace(' Review', '');
    return `# YouTube Short: ${name}

**Duration:** 45-60s
**Format:** Vertical 9:16, narrated, stock footage
**Hook (first 3s):** [text overlay] "Is the ${safeName} worth your money?"

---

## SCRIPT

**[HOOK - 3s]**
"Three words: ${bestFor.toLowerCase()}."

**[BUILD - 30s]**
"I tested the ${safeName} for 30+ days. Here's the real take.

[Show 3 fast cuts: product, in-use, comparison]

The good: [one-line from the verdict]
The bad: [one-line from the cons]
The verdict: [final recommendation]."

**[CTA - 10s]**
"Full review with all the details is in the description. Link in bio.
Hit subscribe if you want more tested-not-spec-sheet reviews."

---

## CAPTION / METADATA

**Title:** ${name} — Worth It? (Tested 30+ Days)
**Description:** After 30 days of daily use, here's my honest take on the ${safeName}. Tested for: ${bestFor.toLowerCase()}.

Full review → https://uzinetwork.store/reviews/${slug}/

#review #tested #${slug.split('-')[0]}

**Tags (10):** ${safeName.toLowerCase()}, review, honest, tested, ${slug.split('-')[0]}, best ${bestFor.split(',')[0]?.trim() || 'tech'}, 2026, worth it, real use, hands on

**Thumbnail:** Product photo + "30 Days Tested" overlay + ⭐ rating

---
`;
  },

  tiktok(slug, name, bestFor) {
    const safeName = name.split(':')[0].replace(' Review', '');
    return `# TikTok: ${name}

**Duration:** 30-45s
**Format:** Vertical 9:16, trending audio + voiceover

---

## SCRIPT

**[HOOK - 2s]** [text on screen: "honest ${safeName} review"]
"I tested the ${safeName} for 30 days."

**[MIDDLE - 25s]**
[Quick cuts: unboxing, in-use, side-by-side with competitor]
"What I loved: [1 pro from verdict]
What I didn't: [1 con]
Who should buy: ${bestFor.split(',')[0]}
Who shouldn't: [opposite]"

**[END - 5s]**
"Full review → link in bio."

---

## CAPTION

${safeName} honest review after 30 days of use. ${bestFor} #${slug.split('-')[0]} #review #honest #fyp #foryou #tech #${new Date().getFullYear()}

**Hashtags (15):** #review #${slug.split('-')[0]} #${bestFor.split(',')[0]?.replace(/\s+/g, '').toLowerCase() || 'tech'} #honest #fyp #foryou #foryoupage #tech #fypシ #viral #trending #productreview #30dayreview #honne...

**Sound suggestion:** Trending voiceover sound (search "review" in TikTok sounds)

---
`;
  },

  x_thread(slug, name, bestFor) {
    const safeName = name.split(':')[0].replace(' Review', '');
    return `# X (Twitter) Thread: ${name}

**Format:** 6-tweet thread

---

## THREAD

**1/6** [HOOK]
I tested the ${safeName} for 30 days.

Here's what nobody tells you 👇

**2/6** [THE PRO]
The good: [lead pro from the review]
This is what makes it worth it.

**3/6** [THE CON]
The bad: [lead con]
This is the part most reviews skip.

**4/6** [WHO SHOULD BUY]
Best for: ${bestFor}
If that's you, get it.

**5/6** [WHO SHOULDN'T]
Don't buy if: [who shouldn't buy]
The alternative is [alternative].

**6/6** [CTA]
Full honest review with the details:
→ https://uzinetwork.store/reviews/${slug}/

#${slug.split('-')[0]} #review

---

## SINGLE-TWEET VERSION (if thread is too much)

I tested the ${safeName} for 30 days. Here's the honest take:

✅ [Pro]
❌ [Con]
🎯 Best for: ${bestFor}

Full review → https://uzinetwork.store/reviews/${slug}/

---
`;
  },

  pinterest(slug, name, bestFor) {
    const safeName = name.split(':')[0].replace(' Review', '');
    return `# Pinterest Pin: ${name}

**Format:** 1000x1500 vertical image
**Style:** Product photo + 30-day-tested badge + rating + verdict

---

## PIN IMAGE

**Top text (bold, large):** "${safeName} Review"
**Middle text:** "Tested 30+ Days"
**Bottom text:** "Is It Worth It?"
**Overlay:** ⭐ ${4}/5 rating
**CTA:** "Read the full review →"
**Brand:** Uzi Network logo (bottom corner)

---

## PIN TITLE (max 100 chars)

${name} — Honest Review After 30 Days of Daily Use

## PIN DESCRIPTION (max 500 chars)

I tested the ${safeName} for 30+ days. Here's my honest take after daily use, who should buy, and who should skip.

✅ Tested for: ${bestFor}
📖 Full review: https://uzinetwork.store/reviews/${slug}/
⭐ Honest verdict, no sponsored placements

#${slug.split('-')[0]} #tech #review #best${bestFor.split(',')[0]?.replace(/\s+/g, '') || 'tech'} #2026

## BOARD

Pin to: Tech Reviews · Best ${bestFor.split(',')[0]?.trim() || 'Tech'} · Gift Ideas

---
`;
  },

  instagram(slug, name, bestFor) {
    const safeName = name.split(':')[0].replace(' Review', '');
    return `# Instagram Reel: ${name}

**Duration:** 30-60s
**Format:** Vertical 9:16, trending audio + text overlay

---

## SCRIPT

Same as TikTok — see TikTok template.

[HOOK] "30-day test: ${safeName}"
[3 PROS] • [3 CONS] • [VERDICT]
[CTA] "Full review → link in bio"

---

## CAPTION

I tested the ${safeName} for 30 days straight. Here's my honest take ⬇️

✅ [Pro 1]
✅ [Pro 2]
✅ [Pro 3]
❌ [Con 1]
❌ [Con 2]

Verdict: [verdict from review]

Who should buy: ${bestFor}

Full honest review with all the details → link in bio

.

.

.

#${slug.split('-')[0]} #review #honest #tech #${new Date().getFullYear()} #${bestFor.split(',')[0]?.replace(/\s+/g, '').toLowerCase() || 'tech'} #productreview #tested #30daychallenge

---
`;
  },
};

const platforms = process.argv.slice(2);
const toGenerate = platforms.length > 0 ? platforms : Object.keys(templates);

let count = 0;
for (const platform of toGenerate) {
  if (!templates[platform]) {
    console.warn(`Unknown platform: ${platform}. Skipping.`);
    continue;
  }
  const dir = join(root, 'docs/social', platform);
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });

  for (const product of products) {
    const content = templates[platform](product.slug, product.name, product.bestFor);
    const outPath = join(dir, `${product.slug}.md`);
    writeFileSync(outPath, content);
    count++;
  }
  console.log(`  Wrote ${products.length} files to docs/social/${platform}/`);
}

console.log(`\nDone. ${count} social posts generated.`);
console.log(`\nNext: copy-paste from docs/social/<platform>/<slug>.md`);
console.log(`Or pipe through the auto-poster CLI when you add platform API keys.`);
