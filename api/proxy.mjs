/** Transport only: forward the frontend's API calls to the independent FastAPI service. */
import { createHmac, randomUUID } from 'node:crypto';
import { isIP } from 'node:net';

const allowedMethods = new Set(['GET', 'POST', 'PATCH', 'PUT', 'DELETE', 'OPTIONS']);
const maxBodyBytes = 1_048_576;

function fail(response, status, code, message) {
  response.statusCode = status;
  response.setHeader('Content-Type', 'application/json');
  response.setHeader('Cache-Control', 'no-store');
  response.end(JSON.stringify({ error: { code, message, details: null, request_id: randomUUID() } }));
}

function apiOrigin() {
  const url = new URL(process.env.FOODIFY_API_ORIGIN || '');
  if (url.protocol !== 'https:' || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
    throw new Error('FOODIFY_API_ORIGIN must be an HTTPS origin.');
  }
  return url.origin;
}

async function readBody(request) {
  if (request.method === 'GET' || request.method === 'OPTIONS') return undefined;
  let body;
  if (request.body !== undefined) {
    body = Buffer.isBuffer(request.body) ? request.body
      : Buffer.from(typeof request.body === 'string' ? request.body : JSON.stringify(request.body));
  } else {
    const chunks = [];
    let size = 0;
    for await (const chunk of request) {
      const buffer = Buffer.from(chunk);
      size += buffer.length;
      if (size > maxBodyBytes) throw new RangeError('Request body too large.');
      chunks.push(buffer);
    }
    body = Buffer.concat(chunks);
  }
  if (body.length > maxBodyBytes) throw new RangeError('Request body too large.');
  return body.length ? body : undefined;
}

export default async function handler(request, response) {
  if (!allowedMethods.has(request.method)) {
    response.setHeader('Allow', [...allowedMethods].join(', '));
    return fail(response, 405, 'method_not_allowed', 'This method is not supported.');
  }
  let origin;
  try { origin = apiOrigin(); }
  catch { return fail(response, 503, 'service_unavailable', 'The API deployment is not configured yet.'); }

  const incoming = new URL(request.url, 'https://frontend.invalid');
  const rewritePath = request.query?.foodify_path;
  const paths = rewritePath === undefined
    ? incoming.searchParams.getAll('foodify_path')
    : Array.isArray(rewritePath) ? rewritePath : [rewritePath];
  if (paths.length !== 1 || !/^[A-Za-z0-9_/-]+$/.test(paths[0])) {
    return fail(response, 400, 'invalid_request', 'Invalid API path.');
  }
  const path = '/api/v1/' + paths[0];
  const upstreamUrl = new URL(path, origin);
  incoming.searchParams.delete('foodify_path');
  // Vercel also forwards the named `:path*` rewrite segment as `path`.
  // It belongs to routing, not to the upstream API query string.
  incoming.searchParams.delete('path');
  upstreamUrl.search = incoming.searchParams.toString();
  const headers = new Headers({ Accept: 'application/json' });
  // Never copy arbitrary proxy headers or a browser-supplied upstream hostname.
  for (const name of ['authorization', 'content-type', 'cookie', 'origin', 'x-foodify-client', 'x-request-id', 'idempotency-key']) {
    const value = request.headers[name];
    if (typeof value === 'string') headers.set(name, value);
  }
  const secret = process.env.FRONTEND_PROXY_SECRET;
  const forwarded = request.headers['x-forwarded-for'];
  const ip = typeof forwarded === 'string' ? forwarded.split(',')[0].trim() : '';
  if (secret && Buffer.byteLength(secret) >= 32 && isIP(ip)) {
    const timestamp = String(Math.floor(Date.now() / 1000));
    const signature = createHmac('sha256', secret)
      .update(`${timestamp}\n${request.method}\n${path}\n${ip}`).digest('hex');
    headers.set('X-Foodify-Proxy-IP', ip);
    headers.set('X-Foodify-Proxy-Time', timestamp);
    headers.set('X-Foodify-Proxy-Signature', signature);
  }
  try {
    const body = await readBody(request);
    const upstream = await fetch(upstreamUrl, {
      // A free backend can take time to wake up after inactivity.
      method: request.method, headers, body, redirect: 'manual', signal: AbortSignal.timeout(75_000),
    });
    response.statusCode = upstream.status;
    for (const name of ['content-type', 'retry-after', 'x-request-id', 'www-authenticate']) {
      const value = upstream.headers.get(name);
      if (value) response.setHeader(name, value);
    }
    response.setHeader('Cache-Control', 'no-store');
    const cookies = upstream.headers.getSetCookie();
    if (cookies.length) response.setHeader('Set-Cookie', cookies);
    // OAuth provider callbacks use the backend's public URL directly. Never
    // forward an unexpected redirect (or put its credentials in another host).
    if (upstream.status >= 300 && upstream.status < 400) {
      return fail(response, 502, 'service_unavailable', 'Unexpected API redirect.');
    }
    response.end(Buffer.from(await upstream.arrayBuffer()));
  } catch (error) {
    if (error instanceof RangeError) return fail(response, 413, 'request_too_large', 'Request body exceeds the allowed size.');
    return fail(response, 503, 'service_unavailable', 'The API is temporarily unavailable.');
  }
}
