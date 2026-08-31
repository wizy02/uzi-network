import type { APIRoute } from 'astro';

export const GET: APIRoute = ({ site }) => {
  const sitemap = new URL('sitemap-index.xml', site ?? 'https://uzi.network.store').toString();
  return new Response(
    `User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: ${sitemap}\n`,
    { headers: { 'Content-Type': 'text/plain' } }
  );
};