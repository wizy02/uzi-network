// hermes-api-gateway.js — Public OpenAI-compatible gateway
// Wraps the local Hermes proxy with auth, rate limits, and billing hooks
// Deploys to Cloudflare Pages Functions or runs as standalone Node service
//
// Endpoints:
//   POST /v1/chat/completions  — OpenAI-compatible
//   GET  /v1/models            — list available models
//   GET  /v1/usage             — your usage stats
//
// Auth: Bearer token in Authorization header
// Rate limits: 50 requests/day free, unlimited on paid plans

import { createServer } from 'http';
import { spawn } from 'child_process';

const PORT = process.env.HERMES_API_PORT || 8765;
const HERMES_PROXY = process.env.HERMES_PROXY_URL || 'http://127.0.0.1:8642';
const ADMIN_KEY = process.env.HERMES_API_ADMIN_KEY || 'change-me-admin';

// Simple KV-style usage tracker (in-memory, restart-resets)
// In production: replace with Redis, Cloudflare KV, or Postgres
const usage = new Map(); // key -> { requests: 0, tokens: 0, lastReset: Date.now() }
const KEYS = new Map(); // key -> { tier: 'free' | 'pro', email?: string, created: Date }

// Pre-seed an admin key for testing
KEYS.set(ADMIN_KEY, { tier: 'pro', email: 'admin@uzinetwork.store', created: new Date() });

const FREE_TIER_DAILY_LIMIT = 50;

function getTierLimits(tier) {
  if (tier === 'pro') return { daily: Infinity, monthly: Infinity };
  return { daily: FREE_TIER_DAILY_LIMIT, monthly: 500 };
}

function checkAndIncrement(key, tier) {
  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;
  const record = usage.get(key) ?? { requests: 0, tokens: 0, lastReset: now };

  // Reset daily counter
  if (now - record.lastReset > dayMs) {
    record.requests = 0;
    record.tokens = 0;
    record.lastReset = now;
  }

  const limits = getTierLimits(tier);
  if (record.requests >= limits.daily) {
    return { ok: false, error: 'rate_limit', message: `Daily limit reached (${limits.daily}). Upgrade to Pro for unlimited.` };
  }

  record.requests += 1;
  usage.set(key, record);
  return { ok: true, record };
}

function authRequest(req) {
  const auth = req.headers.authorization;
  if (!auth || !auth.startsWith('Bearer ')) {
    return { ok: false, status: 401, error: 'Missing Authorization header' };
  }
  const key = auth.slice(7);
  const keyInfo = KEYS.get(key);
  if (!keyInfo) {
    return { ok: false, status: 401, error: 'Invalid API key' };
  }
  return { ok: true, key, tier: keyInfo.tier, email: keyInfo.email };
}

async function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

async function proxyToHermes(body) {
  // Forward to local Hermes OpenAI-compatible proxy
  const res = await fetch(`${HERMES_PROXY}/v1/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  return res;
}

const server = createServer(async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Authorization, Content-Type');
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);

  // Public endpoints (no auth)
  if (url.pathname === '/' || url.pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      service: 'Hermes Agent API Gateway',
      version: '1.0',
      endpoints: ['/v1/chat/completions', '/v1/models', '/v1/usage', '/v1/signup'],
      auth: 'Bearer token in Authorization header',
      pricing: {
        free: `${FREE_TIER_DAILY_LIMIT} requests/day`,
        pro: 'Unlimited — $5/mo (coming soon)',
      },
    }));
  }

  if (url.pathname === '/v1/signup' && req.method === 'POST') {
    const body = JSON.parse(await readBody(req));
    const { email } = body;
    if (!email) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'email required' }));
    }
    const newKey = 'hk_' + Math.random().toString(36).slice(2, 18);
    KEYS.set(newKey, { tier: 'free', email, created: new Date() });
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      api_key: newKey,
      tier: 'free',
      limit: FREE_TIER_DAILY_LIMIT,
      docs: 'https://uzinetwork.store/api-docs',
    }));
  }

  if (url.pathname === '/v1/models') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      object: 'list',
      data: [
        { id: 'hermes-agent', object: 'model', owned_by: 'uzinetwork' },
      ],
    }));
  }

  // Authed endpoints
  const auth = authRequest(req);
  if (!auth.ok) {
    res.writeHead(auth.status, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ error: auth.error }));
  }

  if (url.pathname === '/v1/usage') {
    const record = usage.get(auth.key) ?? { requests: 0, tokens: 0, lastReset: Date.now() };
    const limits = getTierLimits(auth.tier);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({
      tier: auth.tier,
      email: auth.email,
      requests_today: record.requests,
      limit_daily: limits.daily,
      limit_remaining: Math.max(0, limits.daily - record.requests),
    }));
  }

  if (url.pathname === '/v1/chat/completions' && req.method === 'POST') {
    const limit = checkAndIncrement(auth.key, auth.tier);
    if (!limit.ok) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: limit.error, message: limit.message }));
    }
    try {
      const body = JSON.parse(await readBody(req));
      const hermesRes = await proxyToHermes(body);
      const data = await hermesRes.text();
      res.writeHead(hermesRes.status, { 'Content-Type': 'application/json' });
      return res.end(data);
    } catch (err) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ error: 'proxy_error', message: err.message }));
    }
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'not found' }));
});

server.listen(PORT, () => {
  console.log(`[hermes-api] listening on http://127.0.0.1:${PORT}`);
  console.log(`[hermes-api] forwarding to ${HERMES_PROXY}`);
  console.log(`[hermes-api] admin key: ${ADMIN_KEY}`);
});
