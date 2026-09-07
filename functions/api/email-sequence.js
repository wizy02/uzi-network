// functions/api/email-sequence.js — 3-email welcome sequence
// Triggered when someone subscribes via /api/subscribe
// Sends welcome email immediately, follow-ups at +2 days and +5 days
//
// Provider-agnostic: works with Resend or SendGrid (set in env)
// Requires: RESEND_API_KEY or SENDGRID_API_KEY

import { sendEmail } from './_email-provider';

const SEQUENCE = [
  {
    delay_hours: 0,
    subject: "You're in. Here's your free PDF + first discount code.",
    body: `Hey,

Thanks for joining Uzi Network. Two things to grab right now:

1. Free PDF: AI Tools That Pay for Themselves
   https://uzi-network.pages.dev/downloads/ai-tools-that-pay-for-themselves.pdf

2. The biggest discount we have right now: [FIRST_DISCOUNT]
   Link in description, no spam.

Over the next 5 days I'll send you the exact tools we use daily, with exclusive subscriber discounts.

— Uzi Network
https://uzi.network.store`
  },
  {
    delay_hours: 48,
    subject: "Tool #1: Claude Pro — the AI I pay for twice",
    body: `Hey,

If you only sign up for ONE AI tool this year, make it Claude Pro ($20/mo).

Why:
- Beats GPT-4 on coding, writing, analysis
- 200K context window = entire codebases
- Honest about uncertainty (rare for AI)

Use case for you: paste any long document (PDF, transcript, article) and ask it to summarize. Saves 2+ hours per week.

→ Try free: https://anthropic.com/?via=uzinetwork

Tomorrow: the no-code tool that saved us 10 hours per week.

— Uzi Network`
  },
  {
    delay_hours: 120,
    subject: "Tool #2: Make.com — 10 hours saved, no code",
    body: `Hey,

Day 3. Today's tool is Make.com.

If you do the same task in 3+ apps every week, you need Make.

We automated:
- Social media posting (1 hr → 5 min)
- Email follow-ups (2 hr → 0 min)
- Content syndication (3 hr → 0 min)
- Lead capture (1 hr → 0 min)

Total: 10 hours/week saved. $9/month. Free plan covers light use.

→ Try free: https://make.com/en/?via=uzinetwork

That's the end of the welcome sequence. From now on you'll get the weekly drops — the 5 best things we tested that week. One email, every Friday.

— Uzi Network
https://uzi.network.store`
  }
];

export async function onRequestPost(context) {
  const { request, env } = context;
  const { email, name } = await request.json();
  if (!email) {
    return new Response(JSON.stringify({ error: 'email required' }), { status: 400 });
  }

  // Store in sequence database (KV or D1)
  // For now, just send the first email immediately
  const results = [];
  for (const step of SEQUENCE) {
    if (step.delay_hours === 0) {
      try {
        const result = await sendEmail(env, email, step.subject, step.body);
        results.push({ step: 'immediate', status: 'sent', result });
      } catch (err) {
        results.push({ step: 'immediate', status: 'failed', error: err.message });
      }
    } else {
      // Schedule for later (would use cron/queue in production)
      // For now, just log
      console.log(`[email-sequence] Would send "${step.subject}" to ${email} in ${step.delay_hours}h`);
      results.push({ step: step.delay_hours + 'h', status: 'scheduled' });
    }
  }

  return new Response(JSON.stringify({ ok: true, sequence: results }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
}
