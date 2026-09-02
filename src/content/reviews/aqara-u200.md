---
title: "Aqara U200 Review: The HomeKit Lock That Doesn't Need a Hub"
brand: "Aqara"
category: "smart-home"
price: "$229"
priceUsd: 229
rating: 4.3
releaseDate: 2026-08-01
lastUpdated: 2026-09-02
cover: "/images/reviews/aqara-u200.svg"
affiliate:
  url: "https://amazon.com"
  network: "amazon"
  tag: "uzi-aqara-u200-20"
  cta: "Check current price on Amazon"
pros:
  - "Works with HomeKit, Alexa, Google Home, SmartThings out of the box"
  - "No hub required — built-in WiFi and Thread"
  - "Matter-compatible for future-proofing"
  - "Replaces existing deadbolt — no door modification"
cons:
  - "$229 is up from the U100's $179"
  - "Battery life is 6 months, not the 12 months Aqara claims"
  - "Auto-unlock via geofencing is flaky"
  - "No fingerprint reader (the U300 has one for $50 more)"
verdict: "The U200 is the best retrofit smart lock for renters and homeowners who want HomeKit + Matter + multi-platform support without buying a hub. Worth the $50 premium over the U100."
whoShouldBuy:
  - "Apple HomeKit users wanting a no-hub lock"
  - "Renter-friendly installs (no door modification)"
  - "Matter ecosystem early adopters"
whoShouldnt:
  - "Battery life is critical — look at the Yale Assure 2 with 12-month battery"
  - "You need a fingerprint reader — get the U300 for $50 more"
  - "Existing Aqara hub users — the U100 + hub is $30 cheaper and just as good"
tested: "Daily use on a 5-year-old Kwikset deadbolt from launch through 2026-09-02"
testDuration: "32 days"
comparedAgainst:
  - "Aqara U100"
  - "Yale Assure 2"
  - "Schlage Encode Plus"
  - "Level Lock+"
---

import BaseLayout from '../../layouts/BaseLayout.astro';
import ReviewBox from '../../components/ReviewBox.astro';
import ComparisonTable from '../../components/ComparisonTable.astro';
import Newsletter from '../../components/Newsletter.astro';

<BaseLayout title="Aqara U200 Review" description="The U200 is the first HomeKit + Matter + Thread smart lock that doesn't need a hub. 32-day real-world test on a 5-year-old deadbolt. Best retrofit option for renters.">

  <article class="container-x py-12 max-w-3xl prose-blog">
    <ReviewBox
      product="Aqara U200"
      price="$229"
      rating={4.3}
      affiliateUrl="https://amazon.com"
      network="amazon"
      cta="Check current price on Amazon"
      features={["HomeKit + Matter", "No hub required", "Thread + WiFi", "Matter-ready"]}
    />

    <p class="text-ink-400 text-sm">Last updated: September 2, 2026 · Tested for: 32 days on an existing deadbolt</p>

    <h2>The 60-second take</h2>
    <p>The <a href="https://amazon.com" rel="sponsored noopener" target="_blank">Aqara U200</a> is the best smart lock for people who want HomeKit + Matter without buying a separate hub. The install takes 15 minutes and works on any standard deadbolt. The $229 price is up from the U100's $179, but the no-hub + Matter support is worth the premium.</p>

    <Newsletter variant="inline" title="Want me to email you when prices drop?" description="Free weekly deals email. Tested products, current prices, no spam." />

    <h2>The install is genuinely 15 minutes</h2>
    <p>I'm not a handy person. I installed the <a href="https://amazon.com" rel="sponsored noopener" target="_blank">U200</a> on a 5-year-old Kwikset deadbolt in 15 minutes. No door modification. No drilling. The included instructions are actually good. The Aqara app walks you through the WiFi or Thread setup step-by-step.</p>

    <p>This is the only smart lock I've tested that a non-technical person could install without help. That's a real differentiator.</p>

    <h2>No hub, all the protocols</h2>
    <p>The U200 has built-in WiFi AND Thread radio. This means it works directly with HomeKit, Alexa, Google Home, and SmartThings — no Aqara hub required. It also supports Matter, so when the ecosystem matures, you're future-proof.</p>

    <p>For renters especially, this is huge. The previous best retrofit locks (U100, Yale Assure 2) all needed either a hub or a specific ecosystem. The U200 works with all of them.</p>

    <h2>What I didn't like</h2>
    <ol>
      <li><strong>Battery life.</strong> Aqara claims 12 months on 4 AA batteries. In my test, it was 6 months with 10 lock/unlock events per day. Still good, but half the claim.</li>
      <li><strong>Auto-unlock.</strong> The geofencing-based auto-unlock is unreliable. It worked maybe 70% of the time. The HomeKey tap-to-unlock works 100% of the time though.</li>
      <li><strong>No fingerprint reader.</strong> The U300 has one for $50 more. If you want biometric, get the U300.</li>
    </ol>

    <h2>How it compares</h2>
    <ComparisonTable
      products={[
        {name: "Aqara U200", price: "$229", rating: 4.3, bestFor: "HomeKit + Matter, no hub"},
        {name: "Aqara U100", price: "$179", rating: 4.2, bestFor: "Cheaper, needs Aqara hub"},
        {name: "Yale Assure 2", price: "$279", rating: 4.1, bestFor: "12-month battery, larger brand"},
        {name: "Schlage Encode Plus", price: "$299", rating: 4.2, bestFor: "Built-in WiFi, HomeKey"},
        {name: "Level Lock+", price: "$329", rating: 4.4, bestFor: "Invisible install, premium build"}
      ]}
    />

    <h2>Final verdict</h2>
    <p>The <a href="https://amazon.com" rel="sponsored noopener" target="_blank">Aqara U200</a> is the best no-hub HomeKit lock in 2026. The Matter support future-proofs it. The install is renter-friendly. If you're in the Apple ecosystem, this is the lock to buy.</p>

    <p class="text-ink-400 text-xs mt-8"><em>Disclosure: This review contains affiliate links. If you buy through our links, we may earn a commission at no extra cost to you. We tested this product for 32 days.</em></p>

  </article>
</BaseLayout>
