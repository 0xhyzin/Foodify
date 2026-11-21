import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { Readable } from 'node:stream';
import { afterEach, beforeEach, test } from 'node:test';
import handler from '../api/proxy.mjs';

const initialFetch = globalThis.fetch;
const initialOrigin = process.env.FOODIFY_API_ORIGIN;
const initialSecret = process.env.FRONTEND_PROXY_SECRET;
let calls;

beforeEach(() => {
  process.env.FOODIFY_API_ORIGIN = 'https://api.example.test';
  delete process.env.FRONTEND_PROXY_SECRET;
  calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push({ url, options });
    return Response.json({ data: { ok: true } });
  };
});

afterEach(() => {
  globalThis.fetch = initialFetch;
  for (const [key, value] of [
    ['FOODIFY_API_ORIGIN', initialOrigin],
    ['FRONTEND_PROXY_SECRET', initialSecret],
  ]) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
});

async function invoke({ method = 'GET', path = 'restaurants', query, body, chunks = [], headers = {}, url } = {}) {
  const request = Readable.from(chunks);
  Object.assign(request, {
    method,
    url: url ?? `/api/proxy?foodify_path=${encodeURIComponent(path)}`,
    query,
    headers,
  });
  if (body !== undefined) request.body = body;
  const response = {
    statusCode: 200,
    headers: {},
    setHeader(name, value) { this.headers[name.toLowerCase()] = value; },
    end(value) { this.body = value === undefined ? '' : value.toString(); },
  };
  await handler(request, response);
  return response;
}

test('forwards catalog filters to the fixed backend and removes rewrite parameters', async () => {
  const response = await invoke({
    query: { foodify_path: 'restaurants' },
    url: '/api/proxy?foodify_path=restaurants&path=restaurants&limit=20&search=%D9%82%D9%87%D9%88%D8%A9',
  });
  assert.equal(response.statusCode, 200);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url.origin, 'https://api.example.test');
  assert.equal(calls[0].url.pathname, '/api/v1/restaurants');
  assert.equal(calls[0].url.searchParams.get('search'), 'قهوة');
  assert.equal(calls[0].url.searchParams.get('limit'), '20');
  assert.equal(calls[0].url.searchParams.has('foodify_path'), false);
  assert.equal(calls[0].url.searchParams.has('path'), false);
  assert.equal(calls[0].options.redirect, 'manual');
  assert.equal(response.headers['cache-control'], 'no-store');
});

test('forwards authentication, cookies, browser marker and idempotency without arbitrary headers', async () => {
  const response = await invoke({
    method: 'POST', path: 'checkout', body: { restaurant_id: 'demo' },
    headers: {
      authorization: 'Bearer demo-access', cookie: 'foodify_refresh=demo-refresh',
      origin: 'https://frontend.example.test', 'content-type': 'application/json',
      'x-foodify-client': 'web', 'idempotency-key': 'demo-checkout-key',
      'x-forwarded-host': 'attacker.example', 'x-foodify-proxy-signature': 'forged',
    },
  });
  assert.equal(response.statusCode, 200);
  const { options } = calls[0];
  assert.equal(options.headers.get('authorization'), 'Bearer demo-access');
  assert.equal(options.headers.get('cookie'), 'foodify_refresh=demo-refresh');
  assert.equal(options.headers.get('origin'), 'https://frontend.example.test');
  assert.equal(options.headers.get('x-foodify-client'), 'web');
  assert.equal(options.headers.get('idempotency-key'), 'demo-checkout-key');
  assert.equal(options.headers.has('x-forwarded-host'), false);
  assert.equal(options.headers.has('x-foodify-proxy-signature'), false);
  assert.deepEqual(JSON.parse(options.body.toString()), { restaurant_id: 'demo' });
});

test('signs the platform client IP and never forwards a browser supplied signature', async () => {
  process.env.FRONTEND_PROXY_SECRET = 'demo-proxy-secret-with-at-least-32-characters';
  await invoke({ headers: { 'x-forwarded-for': '203.0.113.9, 10.0.0.1', 'x-foodify-proxy-signature': 'forged' } });
  const headers = calls[0].options.headers;
  const timestamp = headers.get('x-foodify-proxy-time');
  const expected = createHmac('sha256', process.env.FRONTEND_PROXY_SECRET)
    .update(`${timestamp}\nGET\n/api/v1/restaurants\n203.0.113.9`).digest('hex');
  assert.equal(headers.get('x-foodify-proxy-ip'), '203.0.113.9');
  assert.equal(headers.get('x-foodify-proxy-signature'), expected);
});

test('does not sign an invalid client IP', async () => {
  process.env.FRONTEND_PROXY_SECRET = 'demo-proxy-secret-with-at-least-32-characters';
  await invoke({ headers: { 'x-forwarded-for': 'not-an-ip' } });
  assert.equal(calls[0].options.headers.has('x-foodify-proxy-signature'), false);
});

test('forwards multiple refresh cookies and safe upstream response headers', async () => {
  globalThis.fetch = async () => new Response('{"error":{"code":"rate_limit_exceeded"}}', {
    status: 429,
    headers: [
      ['Set-Cookie', 'foodify_refresh=one; HttpOnly; Secure; SameSite=Lax'],
      ['Set-Cookie', 'another=value; HttpOnly; Secure'],
      ['Retry-After', '60'], ['X-Request-Id', 'demo-request'],
      ['WWW-Authenticate', 'Bearer'], ['Content-Type', 'application/json'],
    ],
  });
  const response = await invoke();
  assert.equal(response.statusCode, 429);
  assert.equal(response.headers['set-cookie'].length, 2);
  assert.equal(response.headers['retry-after'], '60');
  assert.equal(response.headers['x-request-id'], 'demo-request');
  assert.equal(response.headers['www-authenticate'], 'Bearer');
});

test('rejects duplicate API paths and path traversal without contacting the backend', async () => {
  for (const options of [
    { url: '/api/proxy?foodify_path=orders&foodify_path=restaurants' },
    { query: { foodify_path: ['orders', 'restaurants'] } },
    { path: '../secrets' }, { path: 'orders?url=https://attacker.example' },
  ]) {
    const response = await invoke(options);
    assert.equal(response.statusCode, 400);
    assert.equal(JSON.parse(response.body).error.code, 'invalid_request');
  }
  assert.equal(calls.length, 0);
});

test('rejects missing, HTTP, credentialed and path-bearing backend origins', async () => {
  for (const origin of ['', 'http://api.example.test', 'https://user:pass@api.example.test', 'https://api.example.test/private']) {
    process.env.FOODIFY_API_ORIGIN = origin;
    const response = await invoke();
    assert.equal(response.statusCode, 503);
    assert.equal(JSON.parse(response.body).error.code, 'service_unavailable');
  }
  assert.equal(calls.length, 0);
});

test('rejects unsupported HTTP methods before contacting the backend', async () => {
  const response = await invoke({ method: 'TRACE' });
  assert.equal(response.statusCode, 405);
  assert.match(response.headers.allow, /POST/);
  assert.equal(calls.length, 0);
});

test('limits parsed and streamed request bodies to one MiB', async () => {
  const oversized = Buffer.alloc(1_048_577, 'x');
  for (const options of [{ body: oversized }, { chunks: [oversized] }]) {
    const response = await invoke({ method: 'POST', ...options });
    assert.equal(response.statusCode, 413);
    assert.equal(JSON.parse(response.body).error.code, 'request_too_large');
  }
  assert.equal(calls.length, 0);
});

test('does not forward an unexpected backend redirect', async () => {
  globalThis.fetch = async () => new Response(null, { status: 303, headers: { Location: 'https://other.example' } });
  const response = await invoke();
  assert.equal(response.statusCode, 502);
  assert.equal(response.headers.location, undefined);
  assert.equal(JSON.parse(response.body).error.code, 'service_unavailable');
});

test('returns a safe retryable error when the backend connection fails', async () => {
  globalThis.fetch = async () => { throw new Error('private connection details'); };
  const response = await invoke();
  assert.equal(response.statusCode, 503);
  assert.equal(response.body.includes('private connection details'), false);
  assert.ok(JSON.parse(response.body).error.request_id);
});

test('preserves a successful empty response for logout', async () => {
  globalThis.fetch = async () => new Response(null, { status: 204 });
  const response = await invoke({ method: 'POST', path: 'auth/browser/logout' });
  assert.equal(response.statusCode, 204);
  assert.equal(response.body, '');
});
