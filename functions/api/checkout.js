// functions/api/checkout.js — Create a Lemon Squeezy checkout session
// Docs: https://docs.lemonsqueezy.com/api/checkout

export async function onRequestPost(context) {
  const { request, env } = context;

  // Required env vars (set in Cloudflare Pages)
  const apiKey = env.LEMONSQUEEZY_API_KEY;
  const storeId = env.LEMONSQUEEZY_STORE_ID;
  const variantId = env.LEMONSQUEEZY_VARIANT_ID;

  if (!apiKey || !storeId || !variantId) {
    return new Response(JSON.stringify({
      error: 'not_configured',
      message: 'Lemon Squeezy not configured. Add LEMONSQUEEZY_API_KEY, STORE_ID, VARIANT_ID in Cloudflare Pages env vars.',
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Create checkout
  const checkoutRes = await fetch('https://api.lemonsqueezy.com/v1/checkouts', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/vnd.api+json',
      'Accept': 'application/vnd.api+json',
    },
    body: JSON.stringify({
      data: {
        type: 'checkouts',
        attributes: {
          checkout_data: {
            custom: {
              user_id: crypto.randomUUID(),
            },
          },
          product_options: {
            redirect_url: 'https://uzi.network.store/pro/success',
          },
        },
        relationships: {
          store: { data: { type: 'stores', id: storeId } },
          variant: { data: { type: 'variants', id: variantId } },
        },
      },
    }),
  });

  if (!checkoutRes.ok) {
    return new Response(JSON.stringify({
      error: 'lemonsqueezy_error',
      message: `Lemon Squeezy ${checkoutRes.status}: ${await checkoutRes.text()}`,
    }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const data = await checkoutRes.json();
  const url = data.data?.attributes?.url;

  if (!url) {
    return new Response(JSON.stringify({ error: 'no_url' }), {
      status: 502,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ url }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
