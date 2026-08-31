# Uzi Network

Real reviews. Real tests. Real tech. An affiliate-driven tech and AI review site.

🌐 [uzi.network.store](https://uzi.network.store)

## Stack

- **Astro 5** — static-first, ships near-zero JS
- **Tailwind CSS** — utility styling
- **MDX** — Markdown for reviews and blog
- **Cloudflare Pages** — hosting + functions + CDN
- **TypeScript** — strict mode

## Quick start

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # outputs to dist/
```

## Project structure

```
src/
├── components/        Reusable .astro components
├── content/
│   ├── reviews/       Product reviews (one .md per product)
│   └── blog/          Blog posts (one .md per post)
├── layouts/           Page layouts (BaseLayout.astro)
├── lib/               Shared config and helpers
├── pages/             File-based routes
└── styles/global.css  Tailwind + custom design tokens

functions/
└── api/subscribe.js   Cloudflare Pages Function: newsletter signup

public/
├── favicon.svg
├── og-default.svg
└── images/reviews/    Product cover images
```

## Deploy

See `docs/deployment.md`. One-time Cloudflare setup + automated git push.

## Add content

See `docs/local-development.md`. New reviews: drop a `.md` in `src/content/reviews/`.

## Operations

See `docs/runbook.md`. Daily/weekly/monthly/quarterly checklists.

## Monetization

See `docs/monetization-research.md`. The current ad-network playbook.

## License

© 2026 Uzi Network. All rights reserved.