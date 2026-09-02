// Cloudflare Worker: receives pageview beacons, writes to Analytics Engine
// Free tier: 100,000 events/day, 30-day retention
// Operator can query via the Cloudflare dashboard → Analytics Engine

export interface Env {
  ANALYTICS: AnalyticsEngineDataset;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST' || new URL(request.url).pathname !== '/api/track') {
      return new Response('Not found', { status: 404 });
    }

    try {
      const data: any = await request.json();

      // Validate
      if (!data.path || typeof data.path !== 'string') {
        return new Response('Invalid path', { status: 400 });
      }

      // Parse UA for device category
      const ua = (data.ua || '').toLowerCase();
      let device = 'desktop';
      if (/mobile|android|iphone|ipad|ipod/.test(ua)) device = 'mobile';
      if (/tablet|ipad/.test(ua) && !/mobile/.test(ua)) device = 'tablet';
      if (/bot|crawl|spider/.test(ua)) return new Response(null, { status: 204 });

      // Parse referrer source
      const ref = (data.ref || '').toLowerCase();
      let source = 'direct';
      if (ref.includes('google.')) source = 'google';
      else if (ref.includes('bing.')) source = 'bing';
      else if (ref.includes('duckduckgo.')) source = 'duckduckgo';
      else if (ref.includes('youtube.')) source = 'youtube';
      else if (ref.includes('tiktok.')) source = 'tiktok';
      else if (ref.includes('twitter.') || ref.includes('x.com')) source = 'twitter';
      else if (ref.includes('facebook.') || ref.includes('fb.')) source = 'facebook';
      else if (ref.includes('reddit.')) source = 'reddit';
      else if (ref.includes('instagram.')) source = 'instagram';
      else if (ref.includes('pinterest.')) source = 'pinterest';
      else if (ref) source = 'other';

      // Write to Analytics Engine
      env.ANALYTICS.writeDataPoint({
        blobs: [data.path, source, device],
        doubles: [data.vw || 0, data.vh || 0],
        indexes: [data.path.slice(0, 32)],
      });

      return new Response(null, {
        status: 204,
        headers: { 'Access-Control-Allow-Origin': '*' },
      });
    } catch (err) {
      return new Response('Bad request', { status: 400 });
    }
  },
};
