// Read endpoint for analytics dashboard
// Returns aggregated stats from KV

export async function onRequestGet(context: { request: Request; env: any }) {
  const url = new URL(context.request.url);
  const date = url.searchParams.get('date');
  const type = url.searchParams.get('type');
  const days = parseInt(url.searchParams.get('days') || '7');
  const kv = context.env.UZI_ANALYTICS;

  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
  };

  try {
    // Single day total
    if (date) {
      const total = parseInt(await kv.get(`pv:${date}`) || '0');
      return new Response(JSON.stringify({ total }), { headers: corsHeaders });
    }

    // Aggregate over N days by prefix
    if (type) {
      const today = new Date();
      const dates: string[] = [];
      for (let i = days - 1; i >= 0; i--) {
        const d = new Date(today);
        d.setUTCDate(d.getUTCDate() - i);
        dates.push(d.toISOString().slice(0, 10));
      }

      const prefix = type === 'paths' ? 'pv:path' : type === 'sources' ? 'pv:src' : 'pv:dev';
      const counts: Record<string, number> = {};
      for (const d of dates) {
        const list = await kv.list({ prefix: `${prefix}:${d}:` });
        for (const key of list.keys) {
          const v = parseInt(await kv.get(key.name) || '0');
          // Extract the last segment (path or source or device)
          const last = key.name.split(':').pop() || '';
          counts[last] = (counts[last] || 0) + v;
        }
      }

      const items = Object.entries(counts)
        .map(([key, value]) => ({ key, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 20);

      return new Response(JSON.stringify({ items }), { headers: corsHeaders });
    }

    return new Response('Specify date or type', { status: 400 });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: corsHeaders });
  }
}
