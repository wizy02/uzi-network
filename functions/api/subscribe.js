// Cloudflare Pages Function: POST /api/subscribe
// Triggered by the newsletter form on every page.
//
// POST form-encoded: { email: string, source?: string }
// Returns: { ok: boolean, message: string }
//
// Provider selection is driven by env vars. Set one of:
//   MAILCHIMP_API_KEY, MAILCHIMP_LIST_ID, MAILCHIMP_SERVER_PREFIX
//   CONVERTKIT_API_KEY, CONVERTKIT_FORM_ID
//   BUTTONDOWN_API_KEY
//   RESEND_API_KEY, RESEND_AUDIENCE_ID
//
// If no provider env is set, we log to console (visible in CF Pages logs)
// and return success — so the form works during dev without a provider.

export async function onRequestPost(context) {
  const { request, env } = context;

  // Basic CSRF/origin check
  const origin = request.headers.get('origin');
  const allowed = ['uzi.network.store', 'www.uzi.network.store', 'localhost:4321'];
  if (origin && !allowed.some(h => origin.includes(h))) {
    return new Response(JSON.stringify({ ok: false, message: 'Bad origin.' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let email = '';
  let source = 'homepage';
  const ct = request.headers.get('content-type') || '';
  try {
    if (ct.includes('application/json')) {
      const j = await request.json();
      email = (j.email || '').trim();
      source = j.source || source;
    } else {
      const f = await request.formData();
      email = String(f.get('email') || '').trim();
      source = String(f.get('source') || source);
    }
  } catch {
    return badRequest('Could not parse body.');
  }

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return badRequest('That email looks off. Try again.');
  }

  // Provider routing
  try {
    if (env.MAILCHIMP_API_KEY && env.MAILCHIMP_LIST_ID && env.MAILCHIMP_SERVER_PREFIX) {
      await subscribeMailchimp(env, email, source);
    } else if (env.CONVERTKIT_API_KEY && env.CONVERTKIT_FORM_ID) {
      await subscribeConvertKit(env, email, source);
    } else if (env.BUTTONDOWN_API_KEY) {
      await subscribeButtondown(env, email, source);
    } else if (env.RESEND_API_KEY && env.RESEND_AUDIENCE_ID) {
      await subscribeResend(env, email, source);
    } else {
      // No provider — dev fallback: log and accept.
      console.log('[subscribe:dev]', { email, source, ts: new Date().toISOString() });
    }
  } catch (err) {
    console.error('[subscribe] provider error', err);
    return new Response(JSON.stringify({
      ok: false,
      message: 'Saved locally but the email service hiccuped. Try again or email us.',
    }), { status: 502, headers: { 'Content-Type': 'application/json' } });
  }

  return new Response(JSON.stringify({
    ok: true,
    message: "You're in. Check your inbox in a minute.",
  }), { status: 200, headers: { 'Content-Type': 'application/json' } });
}

// Also support GET for health-checks
export async function onRequestGet() {
  return new Response(JSON.stringify({ ok: true, message: 'POST { email } to subscribe.' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

function badRequest(message) {
  return new Response(JSON.stringify({ ok: false, message }), {
    status: 400,
    headers: { 'Content-Type': 'application/json' },
  });
}

// --- Providers ---

async function subscribeMailchimp(env, email, source) {
  const url = `https://${env.MAILCHIMP_SERVER_PREFIX}.api.mailchimp.com/3.0/lists/${env.MAILCHIMP_LIST_ID}/members`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${btoa('anystring:' + env.MAILCHIMP_API_KEY)}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email_address: email,
      status: 'subscribed',
      tags: ['uzi-network', source],
    }),
  });
  if (!res.ok && res.status !== 400) { // 400 = already subscribed
    throw new Error(`Mailchimp ${res.status}`);
  }
}

async function subscribeConvertKit(env, email, source) {
  const res = await fetch(`https://api.convertkit.com/v3/forms/${env.CONVERTKIT_FORM_ID}/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      api_key: env.CONVERTKIT_API_KEY,
      email,
      tags: [source],
    }),
  });
  if (!res.ok) throw new Error(`ConvertKit ${res.status}`);
}

async function subscribeButtondown(env, email, source) {
  const res = await fetch('https://api.buttondown.email/v1/subscribers', {
    method: 'POST',
    headers: {
      'Authorization': `Token ${env.BUTTONDOWN_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, tags: [source] }),
  });
  if (!res.ok) throw new Error(`Buttondown ${res.status}`);
}

async function subscribeResend(env, email, source) {
  const res = await fetch(`https://api.resend.com/audiences/${env.RESEND_AUDIENCE_ID}/contacts`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, unsubscribed: false }),
  });
  if (!res.ok) throw new Error(`Resend ${res.status}`);
}