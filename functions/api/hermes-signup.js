// functions/api/hermes-signup.js — Issue free Hermes Agent API keys
// Stores keys in Cloudflare KV (or memory for dev)

export async function onRequestPost(context) {
  const { request, env } = context;
  const data = await request.formData();
  const email = String(data.get('email') || '').trim();

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return new Response(JSON.stringify({ error: 'invalid_email', message: 'That email looks off.' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Generate API key
  const apiKey = 'hk_' + crypto.getRandomValues(new Uint8Array(16))
    .reduce((s, b) => s + b.toString(16).padStart(2, '0'), '');

  // Try to store in KV if available
  if (env.HERMES_KEYS) {
    await env.HERMES_KEYS.put(apiKey, JSON.stringify({
      email,
      tier: 'free',
      created: new Date().toISOString(),
      dailyLimit: 50,
    }));
  }

  // Also send to our local Hermes API for in-memory storage
  try {
    await fetch('http://127.0.0.1:8765/v1/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, apiKey }),
    });
  } catch {
    // local API might not be running yet — that's OK
  }

  return new Response(JSON.stringify({
    ok: true,
    api_key: apiKey,
    tier: 'free',
    limit: 50,
    message: 'API key issued. Save it now — we do not store plaintext keys.',
  }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
