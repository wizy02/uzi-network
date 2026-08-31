import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

// https://astro.build/config
// We use 'hybrid' so we can keep static pages but emit a Cloudflare Pages
// Function for /api/subscribe. The bulk of the site is still statically
// pre-rendered. Each non-static page opts in with `export const prerender = false`.
export default defineConfig({
  site: 'https://uzi.network.store',
  output: 'static',
  integrations: [
    tailwind({ applyBaseStyles: true }),
    sitemap(),
  ],
  markdown: {
    shikiConfig: { theme: 'github-dark' },
  },
  build: {
    inlineStylesheets: 'auto',
  },
  compressHTML: true,
  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'viewport',
  },
});