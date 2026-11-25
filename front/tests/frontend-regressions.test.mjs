import assert from 'node:assert/strict';
import { after, before, afterEach, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

// Vite already belongs to the project. Its loader resolves the same TypeScript
// modules and aliases as the app without installing a second test runtime.
let server;
let modules;
const originalFetch = globalThis.fetch;
const globals = ['window', 'document', 'sessionStorage'].map(name => [name, Object.getOwnPropertyDescriptor(globalThis, name)]);
const future = () => new Date(Date.now() + 60_000).toISOString();
const checkoutUrl = 'https://eg.checkout.paymob.com/?publicKey=public-test&clientSecret=intention-test';
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};
const session = (id = 'customer-a', token = 'access-a') => ({
  access_token: token,
  token_type: 'bearer',
  expires_in: 900,
  user: {
    id, name: 'Demo customer', email: 'customer@example.invalid', phone: null,
    email_verified: true, profile_complete: false, default_address_id: null,
    roles: ['customer'], permissions: [], created_at: '2026-11-01T00:00:00Z',
  },
});

before(async () => {
  server = await createServer({
    configFile: false,
    root: fileURLToPath(new URL('../', import.meta.url)),
    logLevel: 'error',
    resolve: { alias: { '@': fileURLToPath(new URL('../src', import.meta.url)) } },
    server: { middlewareMode: true },
    appType: 'custom',
  });
  const [payment, links, browserSession, http, auth, paths, quantity, checkout, orderStages, oauth] = await Promise.all([
    server.ssrLoadModule('/src/features/marketplace/application/start-payment/use-case.ts'),
    server.ssrLoadModule('/src/app/bootstrap/external-links.ts'),
    server.ssrLoadModule('/src/infrastructure/http/browser-session.ts'),
    server.ssrLoadModule('/src/infrastructure/http/fetch-client.ts'),
    server.ssrLoadModule('/src/features/auth/infrastructure/http-auth-repository.ts'),
    server.ssrLoadModule('/src/app/router/paths.ts'),
    server.ssrLoadModule('/src/features/marketplace/application/update-quantity/use-case.ts'),
    server.ssrLoadModule('/src/features/marketplace/application/checkout/use-case.ts'),
    server.ssrLoadModule('/src/features/marketplace/presentation/status-labels.ts'),
    server.ssrLoadModule('/src/features/auth/infrastructure/oauth-flow.ts'),
  ]);
  modules = { ...payment, ...links, ...browserSession, ...http, ...auth, ...paths, ...quantity, ...checkout, ...orderStages, ...oauth };
});
after(async () => { await server?.close(); });
afterEach(() => {
  globalThis.fetch = originalFetch;
  for (const [name, descriptor] of globals) {
    if (descriptor) Object.defineProperty(globalThis, name, descriptor);
    else delete globalThis[name];
  }
});

function startPayment(url = checkoutUrl, expiresAt = future()) {
  return modules.createStartPayment({ start: async () => ({ url, expiresAt }) })('order-a');
}
for (const url of [checkoutUrl, 'https://accept.paymob.com/unifiedcheckout/?publicKey=public-test&clientSecret=intention-test']) {
  test(`payment accepts an approved HTTPS Paymob checkout: ${new URL(url).hostname}`, async () => {
    assert.equal((await startPayment(url)).url, url);
  });
}
for (const [label, url] of [
  ['HTTP', checkoutUrl.replace('https:', 'http:')],
  ['lookalike host', checkoutUrl.replace('eg.checkout.paymob.com', 'eg.checkout.paymob.com.attacker.invalid')],
  ['unexpected port', checkoutUrl.replace('.com/', '.com:444/')],
  ['wrong checkout path', checkoutUrl.replace('.com/', '.com/other/')],
  ['credentials', checkoutUrl.replace('https://', 'https://user:password@')],
  ['fragment', checkoutUrl + '#unsafe'],
  ['missing public key', 'https://eg.checkout.paymob.com/?clientSecret=secret'],
  ['missing client secret', 'https://eg.checkout.paymob.com/?publicKey=public'],
  ['duplicate public key', checkoutUrl + '&publicKey=other'],
  ['duplicate client secret', checkoutUrl + '&clientSecret=other'],
  ['blank public key', 'https://eg.checkout.paymob.com/?publicKey=%20&clientSecret=secret'],
  ['blank client secret', 'https://eg.checkout.paymob.com/?publicKey=public&clientSecret=%20'],
  ['invalid URL', 'this-is-not-a-url'],
]) {
  test(`payment rejects ${label}`, async () => {
    await assert.rejects(startPayment(url), { code: 'invalid_payment_destination' });
  });
}
for (const [label, expiry] of [['expired link', '2020-01-01T00:00:00Z'], ['invalid expiry', 'not-a-date']]) {
  test(`payment rejects ${label}`, async () => {
    await assert.rejects(startPayment(checkoutUrl, expiry), { code: 'payment_expired' });
  });
}
test('payment preserves an uncertain gateway failure instead of making another attempt', async () => {
  const failure = Object.assign(new Error('uncertain'), { code: 'payment_initialization_unknown' });
  let attempts = 0;
  const start = modules.createStartPayment({ start: async () => { attempts += 1; throw failure; } });
  await assert.rejects(start('order-a'), error => error === failure);
  assert.equal(attempts, 1);
});

function locationFor(url) {
  let replaced;
  let normalized;
  const parsed = new URL(url);
  globalThis.window = {
    location: Object.assign(parsed, { replace: value => { replaced = value; } }),
    history: { replaceState: (_state, _title, value) => { normalized = value; } },
  };
  globalThis.document = { title: 'Foodify' };
  return { replaced: () => replaced, normalized: () => normalized };
}
test('local canonical origin preserves the OAuth/action path, query, and fragment', () => {
  const state = locationFor('http://localhost:5173/oauth/callback?source=email#ticket=safe-demo');
  assert.equal(modules.redirectLocalDevelopmentOrigin(), true);
  assert.equal(state.replaced(), 'http://127.0.0.1:5173/oauth/callback?source=email#ticket=safe-demo');
});
for (const url of ['http://127.0.0.1:5173/#/login', 'https://foodify.example/#/login', 'http://localhost:4173/#/login']) {
  test(`origin redirect leaves unrelated origin untouched: ${new URL(url).origin}`, () => {
    const state = locationFor(url);
    assert.equal(modules.redirectLocalDevelopmentOrigin(), false);
    assert.equal(state.replaced(), undefined);
  });
}
for (const [path, fragment, expected] of [
  ['/verify-email', 'token=demo%2Btoken', '/verify-email#/verify-email/confirm?token=demo%2Btoken'],
  ['/reset-password', 'token=demo%26token', '/reset-password#/reset-password?token=demo%26token'],
  ['/oauth/callback', 'ticket=demo-ticket', '/oauth/callback#/oauth/callback?ticket=demo-ticket'],
  ['/oauth/callback', 'error=oauth_cancelled', '/oauth/callback#/oauth/callback?error=oauth_cancelled'],
]) {
  test(`external ${path} action reaches its HashRouter page`, () => {
    const state = locationFor(`http://127.0.0.1:5173${path}#${fragment}`);
    modules.normalizeExternalLinks();
    assert.equal(state.normalized(), expected);
  });
}
test('normalization does not turn an unrelated page into an auth action', () => {
  const state = locationFor('http://127.0.0.1:5173/other#token=demo');
  modules.normalizeExternalLinks();
  assert.equal(state.normalized(), undefined);
});

test('parallel session restores share one cookie rotation', async () => {
  const response = deferred();
  const requests = [];
  globalThis.fetch = (url, options) => { requests.push({ url, options }); return response.promise; };
  const manager = new modules.BrowserSessionManager('https://api.example/api/v1');
  const first = manager.restore();
  const second = manager.restore();
  assert.equal(requests.length, 1);
  assert.equal(requests[0].options.credentials, 'include');
  assert.equal(requests[0].options.headers['X-Foodify-Client'], 'web');
  response.resolve(Response.json(session()));
  assert.deepEqual(await first, session());
  assert.deepEqual(await second, session());
});
test('a late refresh 401 cannot erase a newly confirmed or OAuth session', async () => {
  const response = deferred();
  globalThis.fetch = () => response.promise;
  const manager = new modules.BrowserSessionManager('https://api.example/api/v1');
  const restore = manager.restore();
  const fresh = session('customer-b', 'new-login-token');
  manager.accept(fresh);
  response.resolve(new Response(null, { status: 401 }));
  assert.deepEqual(await restore, fresh);
  assert.deepEqual(manager.current(), fresh);
});
test('a late refresh success cannot restore a cleared session', async () => {
  const response = deferred();
  globalThis.fetch = () => response.promise;
  const manager = new modules.BrowserSessionManager('https://api.example/api/v1');
  const restore = manager.restore();
  manager.clear();
  response.resolve(Response.json(session()));
  assert.equal(await restore, null);
  assert.equal(await manager.restore(), null);
});
test('logout waits for an in-flight cookie rotation before clearing the server cookie', async () => {
  const refresh = deferred();
  const requests = [];
  globalThis.fetch = (url) => {
    requests.push(url);
    return url.endsWith('/refresh') ? refresh.promise : Promise.resolve(new Response(null, { status: 204 }));
  };
  const manager = new modules.BrowserSessionManager('https://api.example/api/v1');
  manager.accept(session());
  const restoring = manager.restore(true);
  const logout = manager.signOut();
  assert.equal(requests.length, 1);
  refresh.resolve(Response.json(session('customer-a', 'rotated-token')));
  await restoring;
  await logout;
  assert.deepEqual(requests.map(url => url.split('/').at(-1)), ['refresh', 'logout']);
  assert.equal(manager.current(), null);
});
test('malformed browser session is rejected before accepting access credentials', async () => {
  globalThis.fetch = async () => Response.json({ ...session(), token_type: 'unexpected' });
  const manager = new modules.BrowserSessionManager('https://api.example/api/v1');
  await assert.rejects(manager.restore(), { code: 'invalid_response' });
  assert.equal(manager.current(), null);
});
test('a rejected request from customer A is never retried as customer B', async () => {
  let current = session('customer-a');
  let fetches = 0;
  let restores = 0;
  globalThis.fetch = async () => { fetches += 1; current = session('customer-b'); return new Response(null, { status: 401 }); };
  const client = new modules.FetchHttpClient('https://api.example/api/v1', {
    current: () => current,
    restore: async () => { restores += 1; return current; },
  });
  await assert.rejects(client.request('/carts'), { code: 'authentication_required' });
  assert.equal(fetches, 1);
  assert.equal(restores, 0);
});
test('an expired request reuses a token already refreshed for the same customer', async () => {
  let current = session();
  let restores = 0;
  const authorizations = [];
  globalThis.fetch = async (_url, options) => {
    authorizations.push(options.headers.Authorization);
    if (authorizations.length === 1) { current = session('customer-a', 'rotated-token'); return new Response(null, { status: 401 }); }
    return Response.json({ items: [] });
  };
  const client = new modules.FetchHttpClient('https://api.example/api/v1', {
    current: () => current,
    restore: async () => { restores += 1; return current; },
  });
  assert.deepEqual(await client.request('/carts'), { items: [] });
  assert.deepEqual(authorizations, ['Bearer access-a', 'Bearer rotated-token']);
  assert.equal(restores, 0);
});
test('email confirmation uses browser-session endpoint and continues to profile onboarding', async () => {
  let request;
  let accepted;
  let cancellations = 0;
  const repository = new modules.HttpAuthRepository(
    { request: async (path, options) => { request = { path, options }; return session(); } },
    { accept: value => { accepted = value; } },
    { cancel: () => { cancellations += 1; } },
  );
  const user = await repository.confirmEmail({ token: 'one-use-demo-token' });
  assert.equal(request.path, '/auth/browser/verify-email');
  assert.equal(request.options.authenticated, false);
  assert.deepEqual(request.options.body, { token: 'one-use-demo-token' });
  assert.deepEqual(accepted, session());
  assert.equal(cancellations, 1);
  assert.equal(modules.accountDestination(user), '/onboarding/profile');
  assert.equal(modules.accountDestination({ ...user, phoneNumber: '+201000000000' }), '/onboarding/address');
  assert.equal(modules.accountDestination({ ...user, phoneNumber: '+201000000000', defaultAddressId: 'address-a' }), '/account');
});

function storageWith(entries = []) {
  const values = new Map(entries);
  globalThis.sessionStorage = {
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
  };
  return values;
}
test('OAuth exchange requires the verifier retained by the originating browser tab', async () => {
  storageWith();
  const flow = new modules.BrowserOAuthFlow({ request: () => assert.fail('exchange must not run without a verifier') }, () => assert.fail('session must not be accepted'));
  await assert.rejects(flow.complete('demo-ticket'), { code: 'oauth_session_missing' });
});
test('Google OAuth exchange accepts the browser session and removes its one-use verifier', async () => {
  const values = storageWith([['foodify.oauth.verifier.google', 'originating-tab-demo-verifier']]);
  let request;
  let accepted;
  const flow = new modules.BrowserOAuthFlow({
    request: async (path, options) => { request = { path, options }; return session(); },
  }, value => { accepted = value; });
  const user = await flow.complete('demo-ticket');
  assert.equal(request.path, '/auth/browser/oauth/complete');
  assert.deepEqual(request.options.body, { ticket: 'demo-ticket', binding_verifier: 'originating-tab-demo-verifier' });
  assert.equal(request.options.authenticated, false);
  assert.deepEqual(accepted, session());
  assert.equal(values.size, 0);
  assert.equal(modules.accountDestination(user), '/onboarding/profile');
});
for (const [provider, authorizationUrl] of [
  ['google', 'https://accounts.google.com.attacker.invalid/o/oauth2/v2/auth'],
  ['google', 'http://accounts.google.com/o/oauth2/v2/auth'],
  ['google', 'https://user:password@accounts.google.com/o/oauth2/v2/auth'],
  ['facebook', 'https://www.facebook.com/unexpected'],
]) {
  test(`OAuth start rejects an unapproved ${provider} authorization destination: ${authorizationUrl}`, async () => {
    const values = storageWith();
    locationFor('http://127.0.0.1:5173/#/login');
    const flow = new modules.BrowserOAuthFlow({ request: async () => ({ authorization_url: authorizationUrl }) }, () => assert.fail('session must not be accepted'));
    await assert.rejects(flow.start(provider), { code: 'invalid_response' });
    assert.equal(values.size, 0);
  });
}

for (const quantity of [0, -1, 1.5, 100, NaN]) {
  test(`cart rejects invalid quantity ${quantity} before HTTP`, () => {
    const update = modules.createUpdateQuantity({ update: () => assert.fail('HTTP must not run') });
    assert.throws(() => update('merchant-a', 'line-a', quantity), { code: 'quantity_limit' });
  });
}
test('cart update preserves merchant scope and checkout passes server revision and idempotency key', async () => {
  let cartCall;
  const update = modules.createUpdateQuantity({ update: async (...args) => { cartCall = args; return { items: [] }; } });
  await update('merchant-a', 'line-a', 2);
  assert.deepEqual(cartCall, ['merchant-a', 'line-a', 2]);
  const input = { restaurantId: 'merchant-a', addressId: 'address-a', method: 'card', expectedTotal: '179.50', cartRevision: 4 };
  let checkoutCall;
  await modules.createCheckout({ checkout: async (...args) => { checkoutCall = args; return { id: 'order-a' }; } })(input, 'idempotency-demo');
  assert.deepEqual(checkoutCall, [input, 'idempotency-demo']);
});
test('operations only advances active fulfillment stages and never reopens cancelled or unpaid orders', () => {
  assert.equal(modules.nextOrderStage('pending'), 'accepted');
  assert.equal(modules.nextOrderStage('accepted'), 'preparing');
  assert.equal(modules.nextOrderStage('preparing'), 'ready_for_pickup');
  assert.equal(modules.nextOrderStage('ready_for_pickup'), 'picked_up');
  assert.equal(modules.nextOrderStage('picked_up'), 'delivered');
  for (const status of ['cancelled', 'rejected', 'awaiting_payment', 'delivered', 'unknown']) {
    assert.equal(modules.nextOrderStage(status), undefined);
  }
});

test('role stage helpers separate manager, kitchen, and courier transitions strictly', () => {
  assert.equal(modules.nextManagerStage('accepted'), 'preparing');
  assert.equal(modules.nextManagerStage('preparing'), 'ready_for_pickup');
  assert.equal(modules.nextManagerStage('ready_for_pickup'), undefined);
  assert.equal(modules.nextManagerStage('picked_up'), undefined);

  assert.equal(modules.nextKitchenStage('accepted'), 'preparing');
  assert.equal(modules.nextKitchenStage('preparing'), 'ready_for_pickup');
  assert.equal(modules.nextKitchenStage('ready_for_pickup'), undefined);

  assert.equal(modules.nextCourierStage('accepted'), undefined);
  assert.equal(modules.nextCourierStage('preparing'), undefined);
  assert.equal(modules.nextCourierStage('ready_for_pickup'), 'PICKED_UP');
  assert.equal(modules.nextCourierStage('picked_up'), 'DELIVERED');
  assert.equal(modules.nextCourierStage('delivered'), undefined);

  assert.equal(modules.primaryPortalPath(['customer']), null);
  assert.equal(modules.primaryPortalPath(['admin']), '/admin');
  assert.equal(modules.primaryPortalPath(['courier']), '/delivery');
  assert.equal(modules.primaryPortalPath(['order_preparer']), '/kitchen');
  assert.equal(modules.primaryPortalPath(['restaurant_manager']), '/operations');

  const baseProfile = {
    id: 'u1',
    name: 'Test',
    email: 'u1@example.invalid',
    phoneNumber: null,
    emailVerified: true,
    profileComplete: false,
    defaultAddressId: null,
    roles: ['customer'],
  };
  assert.equal(modules.accountDestination(baseProfile), '/onboarding/profile');
  assert.equal(modules.loginDestination(baseProfile), '/onboarding/profile');
  assert.equal(modules.loginDestination({ ...baseProfile, roles: ['admin'] }), '/admin');
  assert.equal(modules.loginDestination({ ...baseProfile, roles: ['restaurant_manager'] }), '/operations');
  assert.equal(modules.loginDestination({ ...baseProfile, roles: ['order_preparer'] }), '/kitchen');
  assert.equal(modules.loginDestination({ ...baseProfile, roles: ['courier'] }), '/delivery');
});
