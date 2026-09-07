// functions/api/_email-provider.js — Send email via Resend or SendGrid
// Set RESEND_API_KEY in Cloudflare Pages env vars
// Or SENDGRID_API_KEY for SendGrid

export async function sendEmail(env, to, subject, body) {
  if (env.RESEND_API_KEY) {
    return await sendViaResend(env, to, subject, body);
  }
  if (env.SENDGRID_API_KEY) {
    return await sendViaSendGrid(env, to, subject, body);
  }
  // Dev mode: log to console
  console.log('[email:dev]', { to, subject, body });
  return { mode: 'dev', to, subject };
}

async function sendViaResend(env, to, subject, body) {
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.RESEND_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      from: 'Uzi Network <hello@uzinetwork.store>',
      to,
      subject,
      text: body,
    }),
  });
  if (!res.ok) {
    throw new Error(`Resend ${res.status}: ${await res.text()}`);
  }
  return await res.json();
}

async function sendViaSendGrid(env, to, subject, body) {
  const res = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.SENDGRID_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: 'hello@uzinetwork.store', name: 'Uzi Network' },
      subject,
      content: [{ type: 'text/plain', value: body }],
    }),
  });
  if (!res.ok) {
    throw new Error(`SendGrid ${res.status}: ${await res.text()}`);
  }
  return { sent: true };
}
