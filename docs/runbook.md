# Uzi Network — Runbook

This is the operations document. Whoever runs Uzi Network day-to-day should keep this updated.

## Daily (5 minutes)

- [ ] Check Cloudflare Pages deploy status (should be all green)
- [ ] Skim email inbox (hello@uzi.network.store, partners@, privacy@)
- [ ] Check affiliate dashboard for any spikes or drops

## Weekly (30 minutes, every Monday)

- [ ] Publish 1 new review (or queue next week's)
- [ ] Send the newsletter (Friday morning, US time)
- [ ] Check Google Search Console for indexing issues
- [ ] Glance at Plausible Analytics for top pages and referrers

## Monthly (2 hours, first Monday)

- [ ] Audit ad network performance (RPM by network, by traffic source)
- [ ] Check affiliate network dashboards — which programs paid out
- [ ] Update `docs/monetization-research.md` if anything shifted
- [ ] Review top 10 pages by traffic — what can be improved?
- [ ] Refresh one underperforming review (add new info, update verdict)
- [ ] Check backlinks (Cloudflare Analytics or Ahrefs free)

## Quarterly (4 hours, first Monday of Q1/Q2/Q3/Q4)

- [ ] **Full network audit** — re-read `docs/monetization-research.md`, update with current RPMs
- [ ] Apply to next-tier ad network if traffic qualifies
- [ ] Review and refresh the homepage — featured strip, category strips
- [ ] Add 2-3 new categories if content warrants
- [ ] Refresh the "about" and disclosure pages
- [ ] Read 2-3 competitor sites — what's working for them?
- [ ] Plan next quarter's content calendar

## Annually

- [ ] Renew domain (auto-renew on Cloudflare, but verify)
- [ ] Annual affiliate disclosure update (FTC requires annual review)
- [ ] Tax prep: collect all 1099s from networks
- [ ] Big retro: what's working, what's not, what to kill

## Editorial standards

Every review must have:

1. **8+ weeks** of real use before publishing (unless explicitly noted)
2. **Hands-on testing** — must own or borrow the product
3. **Independent verdict** — no paid placement, ever
4. **Affiliate disclosure** — visible on the page (FTC requirement)
5. **Updated date** — refresh reviews older than 6 months
6. **Honest cons** — every review has at least 2 things we don't love

### Quality bar

If you can't write a 1,500+ word review with 4+ specific pros and 2+ specific cons, don't publish it. **Thin content damages the brand.**

## Content cadence

| Type | Frequency | Owner |
|---|---|---|
| New review | 1/week | Editor |
| Blog post (monetization / industry) | 2/month | Editor |
| Newsletter | 1/week (Friday) | Editor |
| Social post (FB/TT/YT) | Daily | Marketer |
| Quarterly ad audit | 1/quarter | Editor |

## When something breaks

### Site is down

1. Check Cloudflare status: https://www.cloudflarestatus.com/
2. Check Pages deploy log: Dashboard → Workers & Pages → uzi-network → Deployments
3. If deploy broke, revert to last green deploy
4. If CF Pages is down, switch DNS to a backup host (we don't have one — TODO)

### Affiliate links broken

1. Check the network dashboard for status
2. Most networks have redirects — broken links usually mean expired IDs
3. Update frontmatter, redeploy (no build needed, just static + redeploy)

### Email signup stopped working

1. Check Cloudflare Pages → Functions → Logs for the `/api/subscribe` endpoint
2. Most common: expired provider API key
3. Rotate key, redeploy (env var change auto-redeploys)

### Traffic spike (good or bad)

- **Good:** check if Cloudflare cached everything; review may need a feature to handle it
- **Bad:** check if the spike is bot traffic; Cloudflare's bot protection usually catches it

## Open questions / TODOs

- [ ] Set up Cloudflare Analytics (Plausible is a paid alternative if we want better data)
- [ ] Decide on email provider (Mailchimp default; ConvertKit recommended for content sites)
- [ ] Legal entity for invoicing networks
- [ ] Backup host for emergencies
- [ ] Sponsored content policy (none yet — write one)

---

Keep this file updated. The site will outlive this conversation; this runbook shouldn't.