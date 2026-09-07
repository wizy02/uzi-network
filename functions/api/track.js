// functions/api/track.js — Track affiliate clicks and conversions
// Stores in Cloudflare KV (or D1 in production)
//
// Events tracked:
// - affiliate_click: User clicked an affiliate link
// - newsletter_signup: User subscribed to the newsletter
// - pro_subscription: User subscribed to Pro tier
// - api_signup: User signed up for the API
// - pdf_download: User downloaded the lead magnet

export async function onRequestPost(context) {
  const { request, env } = context;
  const data = await request.json();

  const event = data.event;
  const props = data.props || {};

  if (!event) {
    return new Response(JSON.stringify({ error: 'event_required' }), { status: 400 });
  }

  const record = {
    event,
    props,
    timestamp: new Date().toISOString(),
    userAgent: request.headers.get('user-agent') || '',
    referer: request.headers.get('referer') || '',
    ip: request.headers.get('cf-connecting-ip') || 'unknown',
    country: request.headers.get('cf-ipcountry') || 'unknown',
  };

  // Store in KV if available
  if (env.TRACKING_KV) {
    const key = `${event}:${Date.now()}:${Math.random().toString(36).slice(2, 8)}`;
    await env.TRACKING_KV.put(key, JSON.stringify(record), {
      expirationTtl: 60 * 60 * 24 * 90, // 90 days
    });
  }

  // Forward to Plausible if configured
  if (env.PLAUSIBLE_API_KEY) {
    try {
      await fetch('https://plausible.io/api/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': record.userAgent,
          'X-Forwarded-For': record.ip,
        },
        body: JSON.stringify({
          name: event,
          url: props.url || 'https://uzi.network.store',
          domain: 'uzi.network.store',
          props,
        }),
      });
    } catch {
      // Plausible might be down — don't fail the request
    }
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
