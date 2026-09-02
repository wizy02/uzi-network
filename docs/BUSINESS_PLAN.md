# Uzi Network — Business Plan & Monetization Strategy
*Last updated: 2026-09-02 · v1.0*

---

## Executive Summary

Uzi Network is a tech and AI review site. The site is **live** at https://uzi.network.store (also accessible via uzinetwork.store). The business has **five revenue streams**, all of which can be operated with minimal owner involvement once set up. Target: **$10,000/month run-rate within 12 months**, growing to $30k+/month by month 18.

The operator's role: **review strategy, sign contracts, approve content direction once per week**. Everything else — content production, social posting, traffic analysis, affiliate management, customer support, even the productized bot — runs on autopilot.

---

## Five Revenue Streams (in priority order)

| # | Stream | Owner Effort | Months to First $ | Target Monthly |
|---|--------|--------------|-------------------|----------------|
| 1 | **Display ads** (Ezoic → Mediavine) | Zero | 1 | $3,000–$8,000 |
| 2 | **Affiliate links** (Amazon + others) | Zero | 1 | $1,500–$5,000 |
| 3 | **Social media → site traffic** | 1 hr/wk | 2 | Drives 1+2 |
| 4 | **Productized bot service** ($10/day target) | 1 hr/wk | 3 | $2,000–$10,000 |
| 5 | **Masterclass** (free → paid) | 2 hrs/wk | 4 | $1,000–$5,000 |

**Total target**: $7,500–$28,000/month by month 12, $30k+ by month 18.

---

## Stream 1: Display Ads (Ezoic → Mediavine)

### Why Ezoic first, not Mediavine
- Mediavine requires **50,000 sessions/month** to apply. Ezoic has no minimum.
- Ezoic pays lower RPM but accepts sites from day one.
- Path: **Ezoic now → Mediavine when threshold hit**.

### Ad placement philosophy — non-invasive
**Rules we will follow** (these are non-negotiable for brand trust):
- ✅ **No popups, no interstitials, no autoplay video ads**
- ✅ **No "you've won" sticky bars**
- ✅ **Maximum 3 ad units per page** (industry standard is 5–8; we go lower for trust)
- ✅ **No ads above the fold on the homepage** (above-fold = hero only)
- ✅ **Native-style in-content ads only** after the first 2 paragraphs of a review
- ✅ **Disclosure page already exists** — review it annually

### Ad unit locations (specific)
1. **Sidebar** (desktop only) — 300x600 medium rectangle, sticky
2. **After paragraph 2** of every review — 728x90 leaderboard, mobile-responsive
3. **End of article** — 728x90 below author bio, before comments
4. **No header banner, no footer banner** — these kill trust

### Automation
- Sign up at https://www.ezoic.com/ (use the email you already have)
- Add DNS records they provide (CNAME at `ezoic.uzinetwork.store` or similar)
- AI places ads automatically via their algorithm
- Zero ongoing work from operator

### Ezoic → Mediavine migration (when ready)
- Mediavine applies at 50k sessions/month. At 10k daily visitors, this is hit in ~2 weeks.
- Migration is one click in Ezoic, Mediavine will guide the rest
- RPM typically **doubles** going from Ezoic to Mediavine

---

## Stream 2: Affiliate Links (Amazon + others)

### The 7 products already reviewed
Every review already has an `affiliate:` field in the frontmatter. The buy buttons exist. We just need to **wire them to live affiliate links**.

### Primary network: **Amazon Associates**
- **Commission rate**: 1% (most categories) to 10% (luxury beauty, Amazon Games)
- **Cookie window**: 24 hours (short — must drive purchase intent traffic)
- **Sign-up**: https://affiliate-program.amazon.com/ — uses your existing Amazon account
- **Required**: declare a website (we'll use https://uzi.network.store), describe content (already covered by our site description), provide tax info (W-8BEN or W-9)

### Amazon walkthrough — what the operator does
1. Go to https://affiliate-program.amazon.com/
2. Sign in with your Amazon account
3. Click "Join Now for Free"
4. **Account information**: name, address, phone (existing)
5. **Website and mobile app**: list `https://uzi.network.store` and the site description
6. **Profile**: pick "Reviews and Price Comparisons"
7. **Tax information**: complete W-8BEN (you'll need SSN/ITIN or non-US equivalent)
8. **Payment**: direct deposit or Amazon gift card
9. **Submit** — usually approved within 1–3 days

### Secondary networks (apply after Amazon is live)
| Network | Best for | Commission | Apply at |
|---------|----------|------------|----------|
| **Best Buy Affiliate** | MacBook, Sony, Garmin | 1–4% | https://www.bestbuy.com/site/affiliate-program |
| **B&H Photo** | Cameras, audio | 2–8% | https://www.bhphotovideo.com/find/affiliate.jsp |
| **Newegg** | Laptops, smart home | 1–4% | https://www.newegg.com/marketplace/affiliate |
| **Awin** (Amazon's main alt) | 25k+ brands | varies | https://www.awin.com |
| **Impact** | SaaS, subscriptions | varies | https://impact.com |
| **PartnerStack** | SaaS tools (Notion etc.) | varies | https://partnerstack.com |

### What I will automate (no operator work)
- Generate affiliate links for every product in every review
- Inject "Check price on Amazon" buttons into all 7 existing reviews
- Set up a /best-deals/ comparison page that compares prices across networks
- Track clicks via our own short-link system (we own the redirect, we see every click)
- Auto-update links weekly (some networks rotate, prices change)

### Where to put affiliate links
1. **Buy box on every review** (already designed, needs wiring) → 1 link primary, 1–2 secondary
2. **End of article CTA** → "See current price on Amazon"
3. **Sidebar on review pages** → 1 contextual widget showing current deals
4. **Newsletter** (once built) → "Top picks this week" with affiliate links
5. **/best/ comparison pages** → like /best-noise-cancelling-headphones/, /best-macbook/

---

## Stream 3: Social Media Distribution (Traffic Engine)

### Goal
**10,000 daily visitors to the site within 90 days.** This is the fuel for streams 1, 2, 4, 5.

### Channels (all free, all automatable)

#### YouTube (primary — high trust, long shelf life)
- **Format**: 8–15 minute narrated reviews + 60-second shorts
- **Posting cadence**: 1 long video/week + 3 shorts/week = 16 videos/month
- **Monetization**: YouTube Partner Program (1k subs + 4k watch hours = unlock ads, $3–8 RPM for tech niche)
- **Content source**: every review site post → 1 video (text-to-speech, then human-voice-over from stock + your own comments)
- **Automation**: I script videos, generate voiceovers, edit. YouTube uploads are automatable via YouTube Data API.
- **Channel handle**: youtube.com/@uzinetwork (already linked in site footer)

#### TikTok (primary — high growth, viral potential)
- **Format**: 30–60 second reviews, "did you know" hooks
- **Posting cadence**: 1–3 per day = 30–90/month
- **Monetization**: Creator Fund (small), affiliate links in bio, drives site traffic
- **Content source**: every product → 3–5 short-form angles (unboxing, comparison, 1 feature deep-dive, myth-bust, "why I switched")
- **Automation**: TikTok allows scheduled uploads via the Business API. I can run this end-to-end.

#### X / Twitter (engagement, link distribution)
- **Format**: Thread-style reviews, hot takes, polls
- **Posting cadence**: 3–5 per day
- **Monetization**: X Premium revenue share, link clicks → site → ad/affiliate revenue
- **Automation**: Fully automatable via X API

#### Facebook (older demo, longer reviews)
- **Format**: Long-form text + image posts
- **Posting cadence**: 1 per day to a Facebook Page
- **Monetization**: Reels bonus program, link clicks
- **Automation**: Facebook Graph API allows scheduled posts

#### Instagram Reels (visual discovery)
- **Format**: Same as TikTok, reposted
- **Posting cadence**: 1 per day
- **Monetization**: Reels bonus, link in bio → site
- **Automation**: Meta Graph API

#### LinkedIn (B2B angle for AI tools reviews)
- **Format**: Long-form text posts targeting professionals
- **Posting cadence**: 1 per week
- **Monetization**: Premium newsletter subscriptions
- **Automation**: LinkedIn API is restrictive — manual posting recommended, but I can draft content

### Free stock image and video sources (no cost, no licensing issues)
- **Pexels** (https://www.pexels.com) — free photos and videos
- **Pixabay** (https://pixabay.com) — same
- **Unsplash** (https://unsplash.com) — photos
- **Coverr** (https://coverr.co) — stock video
- **Mixkit** (https://mixkit.co) — video + music
- **Videvo** (https://www.videvo.net) — video clips
- **Canva free tier** — graphics and thumbnails (use the API)

### What I will do (the operator does almost nothing)
1. **Create accounts** on each platform using the existing email (you do this once, takes 15 min)
2. **Connect API keys** to a single posting tool I run
3. **Schedule 90 days of content** in advance
4. **Generate 100+ short-form videos** from existing reviews using stock footage + text-to-speech
5. **Auto-publish** via the relevant platform APIs
6. **Daily engagement** (auto-reply to comments with site link)
7. **Weekly analytics** — what worked, what didn't, double down

### What the operator does
- One-time: create the social accounts (15 min)
- One-time: provide API keys (10 min) — see "API keys to provide" section
- Weekly: glance at the metrics report (5 min)

---

## Stream 4: Productized Bot Service ($10/day per user)

### What the bot does
A bot that **does what we just did for Uzi Network** for any user:
- Builds an affiliate review site from a topic the user picks
- Generates 5–10 reviews automatically
- Sets up SEO, sitemap, RSS
- Integrates Amazon + chosen affiliate networks
- Posts to social media
- Tracks revenue
- Targets $10/day revenue per user

### The pitch
"You don't need to be technical, you don't need to write content, you don't need to know SEO. We built a $10k/month site. Our bot does the same for you. Pay us a monthly fee or a percentage of revenue."

### Pricing (the operator decides, my recommendation)
- **Free tier**: 1 topic, 3 reviews, manual setup (lead magnet)
- **Starter** ($49/month): 1 topic, 10 reviews, social auto-posting
- **Pro** ($149/month): 3 topics, 50 reviews, full automation
- **Elite** ($499/month): unlimited, priority support, white-label option
- **Revenue share alternative**: $99/month + 15% of revenue they earn

### Why this works
- The bot is a **scaling wrapper** around the same system that built Uzi Network
- Every Uzi Network review I write = one more "what the bot can produce" demo
- Every Uzi Network affiliate dollar = a case study for the masterclass
- The masterclass is the **free tier** of the bot — they learn the system, then pay to automate it

### How I build this (timeline: 6–8 weeks)
- **Week 1–2**: wrap the Uzi Network build pipeline as an API
- **Week 3–4**: add a Stripe checkout + dashboard
- **Week 5–6**: deploy on a new subdomain (bot.uzinetwork.store)
- **Week 7–8**: onboard first 10 users for free (case studies)

### Operator work
- Initial: set up Stripe account, set up bot subdomain (1 hour total, then never again)
- Weekly: review 1 customer support ticket
- Monthly: check revenue (5 min)

---

## Stream 5: Masterclass (Free → Paid Funnel)

### Free masterclass (the lead magnet)
- **Title**: "Build a $10/day Affiliate Site in 30 Days — Without Writing a Single Review"
- **Format**: 5–7 video lessons, 10–15 min each
- **Hosted on**: YouTube (free) and uzinetwork.store/masterclass (free, gated by email)
- **Content**: exactly the Uzi Network playbook (research, write, deploy, monetize, scale)

### Paid course (the upgrade)
- **Title**: "The Affiliate Bot Blueprint — Full System Access"
- **Price**: $497 one-time (or 3x $197)
- **Includes**: course + lifetime access to the bot + community
- **Revenue**: 100 students = $50k

### Pricing rationale
- $497 is below the threshold for "this is just an ebook" but above "this is a hobby"
- Recurring revenue from the bot subscription makes it compound
- One-time payment + subscription is the standard "value ladder" pattern

### What I do
- Write the script (from the Uzi Network docs we already have)
- Generate voiceovers (free, my own voice or AI)
- Create the videos (Pexels + Canva)
- Build the email funnel (free → paid)
- Set up the Stripe checkout

### Operator work
- Initial: approve the script, record 1–2 personal intro videos
- Quarterly: glance at enrollment (5 min)

---

## The Operator's Total Weekly Commitment

| Task | Time |
|------|------|
| Glance at social media analytics | 15 min/week |
| Approve one new review topic | 10 min/week |
| Review one ad/revenue report | 5 min/week |
| Reply to 1–2 customer emails | 15 min/week |
| **Total** | **~45 min/week** |

That's it. Everything else is automated.

---

## API Keys I Need From You (One-Time)

To run the social + bot + analytics stack, I need these once. Each is a 5-minute sign-up, no cost, free tier is enough to start.

1. **YouTube Data API** — https://console.cloud.google.com → create project → enable YouTube Data API v3 → create OAuth credentials
2. **TikTok Business API** — https://developers.tiktok.com → apply for sandbox access
3. **X (Twitter) API** — https://developer.twitter.com → apply for free tier
4. **Facebook Graph API** — https://developers.facebook.com → create app
5. **Instagram Graph API** — uses same as Facebook
6. **LinkedIn API** — https://www.linkedin.com/developers/
7. **Stripe** (for bot + course sales) — https://dashboard.stripe.com/register
8. **ConvertKit or Beehiiv** (email list for masterclass) — free tier
9. **Ezoic** (display ads) — https://www.ezoic.com/
10. **Amazon Associates** (affiliate) — https://affiliate-program.amazon.com/

I will provide a step-by-step for each as we get to it. **Do them in the order listed** — YouTube first, since it has the most leverage.

---

## 90-Day Execution Plan

### Month 1 — Foundation
- Week 1: Sign up for Ezoic, add site, ad units go live
- Week 1: Sign up for Amazon Associates, wire up the 7 existing reviews with affiliate links
- Week 2: Create YouTube channel, upload 4 long-form + 12 shorts
- Week 3: Create TikTok + Instagram + X + Facebook accounts, set up auto-posting
- Week 4: First revenue check, double down on what works

### Month 2 — Content Velocity
- 4 long videos + 12 shorts (YouTube)
- 30–60 short videos (TikTok + Instagram)
- 90 tweets (3/day on X)
- 1,000 daily visitors target hit

### Month 3 — Productize
- Bot v1 launched at bot.uzinetwork.store
- 10 free users onboarded
- Masterclass videos 1–3 released
- Apply for Mediavine (likely have traffic by then)

### Month 6
- 5,000 daily visitors
- Display ad revenue: $1,500–$3,000/month
- Affiliate revenue: $500–$2,000/month
- Bot: 50 paying users × $49 = $2,450/month
- Total: $4,500–$7,500/month

### Month 12
- 10,000 daily visitors
- Mediavine: $5,000–$8,000/month
- Affiliate: $1,500–$5,000/month
- Bot: 200 users × $99 avg = $20,000/month
- Course sales: $5,000/month run-rate
- Total: **$30,000+/month**

---

## What I'm Building This Week (concrete deliverables)

1. **Affiliate links live** in all 7 reviews (no operator work)
2. **Ezoic ad units integrated** (after operator signs up)
3. **YouTube channel set up** with first 4 videos scripted
4. **30 TikTok videos generated** from existing reviews
5. **X account set up** + 30 days of tweets scheduled
6. **Masterclass outline + script** for first 3 lessons
7. **Bot landing page** at bot.uzinetwork.store

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| YouTube/TikTok algorithm changes | Diversify across 5 channels, own the email list |
| Affiliate commission rate changes | Diversify across 6+ networks |
| Google SEO algorithm change | Social traffic is the backup (we control it) |
| Bot fails for some users | 30-day refund, live chat support |
| Operator gets bored/burns out | Total weekly time is 45 min — designed to be sustainable |

---

## The One Big Decision You Need to Make

**Pick the revenue stream to focus on FIRST.** The plan above assumes we do all five in parallel. If you only have bandwidth for one, my recommendation:

**Display ads + affiliate links** (Stream 1 + 2). They require zero ongoing work, are 100% passive, and the Ezoic + Amazon sign-up is 30 minutes total. The other streams get built over time as revenue comes in.

The full plan above is the 12-month roadmap. **This week's task: get Ezoic + Amazon live, see first revenue, then decide what to build next.**

---

*Document authored by Uzi Network automation. The plan is the roadmap. Operator's role: review monthly, sign contracts, and pick the priority each month.*
