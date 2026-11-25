import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

function load(name) {
  return JSON.parse(readFileSync(new URL(`../back/postman/${name}`, import.meta.url), 'utf8'));
}
function requests(items) {
  return items.flatMap(item => item.item ? requests(item.item) : [item.request]);
}

for (const name of [
  'Foodify.postman_collection.json',
  'Foodify.Sprint2.postman_collection.json',
  'Foodify.Sprint3.postman_collection.json',
]) {
  test(`${name} uses one /api/v1 prefix with the shared environment origin`, () => {
    const collection = load(name);
    const defaultBase = collection.variable?.find(variable => variable.key === 'base_url')?.value;
    if (defaultBase) assert.equal(new URL(defaultBase).pathname, '/');
    for (const request of requests(collection.item)) {
      const address = new URL(request.url.replace('{{base_url}}', 'http://localhost:8000'));
      if (address.pathname.startsWith('/health/')) continue;
      assert.ok(address.pathname.startsWith('/api/v1/'), request.url);
      assert.equal(address.pathname.includes('/api/v1/api/v1/'), false);
    }
  });
}

test('all Postman environments define a backend origin without a path prefix', () => {
  for (const name of ['development', 'test', 'production']) {
    const value = load(`${name}.postman_environment.json`).values.find(item => item.key === 'base_url').value;
    assert.equal(new URL(value).pathname, '/');
  }
});

test('browser email confirmation reference uses the protected session transport', () => {
  const collection = load('Foodify.postman_collection.json');
  const request = requests(collection.item).find(item => item.url.endsWith('/auth/browser/verify-email'));
  assert.ok(request);
  assert.equal(request.method, 'POST');
  const headers = new Map(request.header.map(header => [header.key.toLowerCase(), header.value]));
  assert.equal(headers.get('x-foodify-client'), 'web');
  assert.equal(headers.get('origin'), '{{frontend_origin}}');
  assert.equal(request.auth.type, 'noauth');
  assert.deepEqual(JSON.parse(request.body.raw), { token: '{{email_verification_token}}' });
});

test('browser login references the credential variables already supplied by each environment', () => {
  const collection = load('Foodify.postman_collection.json');
  const request = requests(collection.item).find(item => item.url.endsWith('/auth/browser/login'));
  const body = JSON.parse(request.body.raw);
  assert.deepEqual(body, { email: '{{email}}', password: '{{password}}' });
  for (const name of ['development', 'test', 'production']) {
    const keys = new Set(load(`${name}.postman_environment.json`).values.map(item => item.key));
    assert.ok(keys.has('email'));
    assert.ok(keys.has('password'));
  }
});

test('Sprint 3 Postman collection covers admin, kitchen, delivery, and notifications portals', () => {
  const collection = load('Foodify.Sprint3.postman_collection.json');
  const urls = requests(collection.item).map(item => item.url);
  for (const requiredSuffix of [
    '/api/v1/admin/staff',
    '/api/v1/kitchen/orders',
    '/api/v1/delivery/my-orders',
    '/api/v1/notifications',
  ]) {
    assert.ok(
      urls.some(url => url.includes(requiredSuffix)),
      `Missing Sprint 3 Postman contract for ${requiredSuffix}`,
    );
  }
});
