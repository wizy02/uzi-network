# Cloudflare Pages deployment

This site is configured to deploy to Cloudflare Pages automatically.

## One-time setup

### Option A: Connect via Cloudflare dashboard (recommended)

1. Push this repo to GitHub.
2. Cloudflare dashboard → Workers & Pages → Create application → Pages → Connect to Git.
3. Select the repo.
4. Set:
   - **Build command:** `npm run build`
   - **Build output directory:** `dist`
   - **Node version:** `20` (Settings → Functions → Compatibility flags → set `NODE_VERSION` to `20`)
5. Add custom domain: `uzi.network.store` (already on Cloudflare per the brief).
6. Set environment variables (Settings → Environment variables):
   - `MAILCHIMP_API_KEY` (or whichever provider you pick)
   - `MAILCHIMP_LIST_ID`
   - `MAILCHIMP_SERVER_PREFIX` (e.g. `us12`)
   - *(see `src/functions/api/subscribe.js` for full list)*

That's it. Every push to `main` deploys automatically.

### Option B: CLI deploy (Wrangler)

```bash
npm i -g wrangler
wrangler login
wrangler pages deploy dist --project-name=uzi-network
```

## GitHub Actions deploy (alternative)

The `.github/workflows/deploy.yml` workflow builds and pushes via the Cloudflare API. To enable:

1. Get a Cloudflare API token: https://dash.cloudflare.com/profile/api-tokens → Create Token → Edit Cloudflare Pages template.
2. Get your Account ID from the Cloudflare dashboard sidebar.
3. Add both as GitHub repo secrets: Settings → Secrets and variables → Actions.

## DNS / domain

`uzi.network.store` is already on Cloudflare per the brief. Cloudflare Pages will:
1. Auto-provision a `*.uzi-network.pages.dev` preview URL on first deploy.
2. Add `uzi.network.store` as a custom domain once you attach it in the Pages project settings.

## Environment variables

Production secrets go in Cloudflare dashboard → Pages project → Settings → Environment variables. The `functions/api/subscribe.js` function reads them via `env.MAILCHIMP_API_KEY` etc.

Set up `.dev.vars` for local dev (DO NOT commit this file — see `.gitignore`):

```
MAILCHIMP_API_KEY=your_key_here
MAILCHIMP_LIST_ID=your_list_id
MAILCHIMP_SERVER_PREFIX=us12
```

For local testing with `wrangler pages dev`, the function will use these.

## Email provider switching

The newsletter function (`functions/api/subscribe.js`) auto-detects which provider to use based on which env vars are set:

- **Mailchimp:** set all three of `MAILCHIMP_API_KEY`, `MAILCHIMP_LIST_ID`, `MAILCHIMP_SERVER_PREFIX`
- **ConvertKit:** set `CONVERTKIT_API_KEY` + `CONVERTKIT_FORM_ID`
- **Buttondown:** set `BUTTONDOWN_API_KEY`
- **Resend:** set `RESEND_API_KEY` + `RESEND_AUDIENCE_ID`
- **None:** falls back to console logging (dev only)