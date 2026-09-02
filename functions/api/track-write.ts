// Cloudflare Pages Function: receives pageview beacons
// Stores aggregates in KV (free tier: 100k reads/day, 1k writes/day)
// The /admin/analytics page reads from KV and renders a dashboard

export async function onRequestPost(context: { request: Request; env: any }) {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };

  if (context.request.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  try {
    const data: any = await context.request.json();
    if (!data?.path) return new Response('bad', { status: 400 });

    const ua = (data.ua || '').toLowerCase();
    if (/bot|crawl|spider|preview/i.test(ua)) {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    let device = 'desktop';
    if (/mobile|android|iphone|ipod/.test(ua)) device = 'mobile';
    else if (/tablet|ipad/.test(ua)) device = 'tablet';

    const ref = (data.ref || '').toLowerCase();
    let source = 'direct';
    if (ref.includes('google.')) source = 'google';
    else if (ref.includes('youtube.')) source = 'youtube';
    else if (ref.includes('tiktok.')) source = 'tiktok';
    else if (ref.includes('twitter.') || ref.includes('x.com')) source = 'twitter';
    else if (ref.includes('facebook.') || ref.includes('fb.')) source = 'facebook';
    else if (ref.includes('reddit.')) source = 'reddit';
    else if (ref.includes('instagram.')) source = 'instagram';
    else if (ref.includes('pinterest.')) source = 'pinterest';
    else if (ref.includes('bing.')) source = 'bing';
    else if (ref) source = 'other';

    // Today's date key (UTC)
    const today = new Date().toISOString().slice(0, 10);
    const kv = context.env.UZI_ANALYTICS;

    // Increment counters
    await Promise.all([
      kv.put(`pv:${today}`, String((parseInt(await kv.get(`pv:${today}`) || '0') + 1))),
      kv.put(`pv:path:${today}:${data.path}`, String((parseInt(await kv.get(`pv:path:${today}:${data.path}`) || '0') + 1))),
      kv.put(`pv:src:${today}:${source}`, String((parseInt(await kv.get(`pv:src:${today}:${source}`) || '0') + 1))),
      kv.put(`pv:dev:${today}:${device}`, String((parseInt(await kv.get(`pv:dev:${today}:${device}`) || '0') + 1))),
    ]);

    return new Response(null, { status: 204, headers: corsHeaders });
  } catch {
    return new Response('bad', { status: 400 });
  }
}

export async function onRequestGet() {
  return new Response('Method not allowed', { status: 405 });
}
