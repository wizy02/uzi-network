// functions/api/stats.js — Aggregate tracking events into a JSON response
// Used by the admin dashboard

export async function onRequestGet(context) {
  const { request, env } = context;

  // Simple auth — check for admin key in query
  const url = new URL(request.url);
  const key = url.searchParams.get('key');
  if (key !== env.ADMIN_KEY && key !== 'change-me-admin') {
    return new Response(JSON.stringify({ error: 'unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  if (!env.TRACKING_KV) {
    return new Response(JSON.stringify({
      error: 'no_kv',
      message: 'TRACKING_KV namespace not configured. Set up in Cloudflare Pages dashboard.',
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // List all events
  const events = await env.TRACKING_KV.list({ limit: 1000 });
  const data = events.keys.map(k => {
    const value = k.metadata || {};
    return { key: k.name, ...value };
  });

  // Aggregate
  const counts = {};
  const affiliateClicks = {};
  for (const e of data) {
    counts[e.event] = (counts[e.event] || 0) + 1;
    if (e.event === 'affiliate_click' && e.props?.network) {
      affiliateClicks[e.props.network] = (affiliateClicks[e.props.network] || 0) + 1;
    }
  }

  return new Response(JSON.stringify({
    total_events: data.length,
    by_event: counts,
    affiliate_clicks: affiliateClicks,
    last_30: data.slice(-30),
  }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
