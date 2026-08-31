# Local development

## Quick start

```bash
npm install
npm run dev     # http://localhost:4321
```

## Project layout

```
src/
├── components/        Reusable Astro components
│   ├── Header.astro
│   ├── Footer.astro
│   ├── Hero.astro
│   ├── Newsletter.astro   ← uses /api/subscribe
│   ├── Rating.astro       ← star renderer
│   └── ReviewCard.astro
├── content/
│   ├── reviews/        ← product reviews (Markdown + frontmatter)
│   └── blog/           ← blog posts (Markdown + frontmatter)
├── layouts/
│   └── BaseLayout.astro   ← every page uses this
├── lib/
│   └── site.ts        ← site metadata, nav, categories
├── pages/             ← file-based routing
│   ├── index.astro
│   ├── about.astro
│   ├── blog/
│   ├── reviews/
│   │   ├── index.astro
│   │   └── [slug].astro
│   ├── contact.astro
│   ├── disclosure.astro
│   ├── privacy.astro
│   ├── rss.xml.ts
│   └── robots.txt.ts
└── styles/global.css

functions/
└── api/subscribe.js   ← Cloudflare Pages Function (newsletter)

public/
├── favicon.svg
├── og-default.svg
└── images/reviews/    ← product covers

public/fonts/          ← (drop Inter variable font here for self-hosting)
```

## Adding a new review

1. Drop a JPG/PNG/SVG into `public/images/reviews/<slug>.jpg`.
2. Create `src/content/reviews/<slug>.md` with the frontmatter template (copy any existing review).
3. Fill in: `title`, `brand`, `category`, `price`, `rating`, `releaseDate`, `cover`, `affiliate.url`, `pros`, `cons`, `verdict`.
4. Write the body in Markdown.
5. Run `npm run dev` and visit `/reviews/<slug>`.

## Adding a new blog post

1. Create `src/content/blog/<slug>.md`.
2. Frontmatter needs: `title`, `description`, `date`, `tags` (optional), `draft: false` (or `true` to hide).
3. Body in Markdown.

## Categories

Edit `src/lib/site.ts` `CATEGORIES` array. Categories must match the `category` enum in `src/content.config.ts`.

## Deploy

See `docs/deployment.md`.