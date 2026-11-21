import assert from 'node:assert/strict';
import { before, after, afterEach, test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

// Real application adapters are composed together. Only the backend HTTP
// boundary is substituted; these do not claim to be browser-to-MySQL tests.
let server;
let modules;
const originalFetch = globalThis.fetch;
const baseUrl = 'https://api.example.invalid/api/v1';
const userDto = {
  id: 'customer-a', name: 'Demo customer', email: 'customer@example.invalid',
  phone: null, email_verified: true, roles: ['customer'], permissions: [],
  profile_complete: false, default_address_id: null, created_at: '2026-11-03T00:00:00Z',
};
const sessionDto = token => ({ access_token: token, token_type: 'bearer', expires_in: 900, user: userDto });
const orderDto = {
  id: 'order-a', restaurant_id: 'merchant-a', status: 'awaiting_payment',
  payment_method: 'card', payment_status: 'pending', subtotal: '90.50',
  delivery_fee: '10.00', total: '100.50', created_at: '2026-11-03T00:00:00Z',
  delivery_address: { recipient_name: 'Demo customer', phone: '+201000000000', city: 'Cairo', area: 'Nasr City', street: 'Demo Street', building: '1' },
  payment: { reference: 'demo-reference', is_simulated: false, claimed_reference: null, transfer_recipient: null, transfer_recipient_name: null },
  items: [{ menu_item_id: 'item-a', name: 'Demo meal', unit_price: '45.25', quantity: 2, line_total: '90.50' }],
  events: [{ status: 'awaiting_payment', note: null, created_at: '2026-11-03T00:00:00Z' }],
};

before(async () => {
  server = await createServer({
    configFile: false, root: fileURLToPath(new URL('../', import.meta.url)),
    logLevel: 'error', server: { middlewareMode: true }, appType: 'custom',
    resolve: { alias: { '@': fileURLToPath(new URL('../src', import.meta.url)) } },
  });
  const paths = [
    '/src/infrastructure/http/fetch-client.ts', '/src/infrastructure/http/browser-session.ts',
    '/src/features/auth/infrastructure/http-auth-repository.ts',
    '/src/features/marketplace/infrastructure/http-cart-repository.ts',
    '/src/features/marketplace/infrastructure/http-order-repository.ts',
    '/src/features/marketplace/infrastructure/http-payment-repository.ts',
    '/src/features/marketplace/infrastructure/http-delivery-repository.ts',
    '/src/features/marketplace/infrastructure/http-notification-repository.ts',
    '/src/features/marketplace/infrastructure/http-operations-repository.ts',
    '/src/features/marketplace/application/checkout/use-case.ts',
    '/src/features/marketplace/application/start-payment/use-case.ts',
    '/src/app/router/paths.ts',
  ];
  modules = Object.assign({}, ...await Promise.all(paths.map(path => server.ssrLoadModule(path))));
});
after(async () => { await server?.close(); });
afterEach(() => { globalThis.fetch = originalFetch; });

function transport() {
  const manager = new modules.BrowserSessionManager(baseUrl);
  return { manager, client: new modules.FetchHttpClient(baseUrl, manager) };
}

test('confirmation composes HTTP, DTO mapping, session acceptance and onboarding routing', async () => {
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    return Response.json(url.endsWith('/verify-email') ? sessionDto('confirmed-access') : userDto);
  };
  const { manager, client } = transport();
  let cancelled = false;
  const auth = new modules.HttpAuthRepository(client, manager, { cancel: () => { cancelled = true; } });
  const profile = await auth.confirmEmail({ token: 'one-use-confirmation-token' });
  assert.equal(profile.phoneNumber, null);
  assert.equal(modules.accountDestination(profile), '/onboarding/profile');
  assert.equal(manager.current().access_token, 'confirmed-access');
  assert.equal(cancelled, true);
  assert.equal(requests[0].url, baseUrl + '/auth/browser/verify-email');
  assert.equal(requests[0].options.credentials, 'include');
  assert.equal(requests[0].options.headers['X-Foodify-Client'], 'web');
  assert.deepEqual(JSON.parse(requests[0].options.body), { token: 'one-use-confirmation-token' });
  assert.equal(requests[0].options.headers.Authorization, undefined);
  await auth.getSession();
  assert.equal(requests[1].options.headers.Authorization, 'Bearer confirmed-access');
});

test('protected API rejection rotates the real session manager and retries once with its new token', async () => {
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    if (url.endsWith('/auth/browser/refresh')) return Response.json(sessionDto('rotated-access'));
    if (requests.length === 1) return new Response(null, { status: 401 });
    return Response.json({ data: { orders: [] } });
  };
  const { manager, client } = transport();
  manager.accept(sessionDto('old-access'));
  assert.deepEqual(await client.request('/orders'), { data: { orders: [] } });
  assert.equal(requests.length, 3);
  assert.equal(requests[0].options.headers.Authorization, 'Bearer old-access');
  assert.equal(requests[1].url, baseUrl + '/auth/browser/refresh');
  assert.equal(requests[2].options.headers.Authorization, 'Bearer rotated-access');
  assert.equal(manager.current().access_token, 'rotated-access');
});

test('cart HTTP repositories preserve merchant identifiers and exact money strings through mapping', async () => {
  const requested = [];
  globalThis.fetch = async (url, options) => {
    const merchant = url.split('/').at(-1);
    requested.push({ merchant, options });
    return Response.json({ data: { cart: {
      id: 'cart-' + merchant, restaurant_id: merchant, revision: 2,
      subtotal: '45.25', delivery_fee: '10.00', total: '55.25',
      items: [{ id: 'line-' + merchant, menu_item_id: 'item-' + merchant, name: 'Demo meal', price: '45.25', quantity: 1, line_total: '45.25', available: true }],
    } } });
  };
  const { manager, client } = transport();
  manager.accept(sessionDto('cart-access'));
  const repository = new modules.HttpCartRepository(client);
  const first = await repository.get('merchant-a');
  const second = await repository.get('merchant-b');
  assert.deepEqual(requested.map(entry => entry.merchant), ['merchant-a', 'merchant-b']);
  assert.equal(first.restaurantId, 'merchant-a');
  assert.equal(second.restaurantId, 'merchant-b');
  assert.equal(first.items[0].productId, 'item-merchant-a');
  assert.equal(second.items[0].productId, 'item-merchant-b');
  assert.equal(first.total, '55.25');
});

test('checkout use case composes its HTTP DTO, idempotency header and mapped order response', async () => {
  let request;
  globalThis.fetch = async (url, options) => { request = { url, options }; return Response.json({ data: { order: orderDto } }, { status: 201 }); };
  const { manager, client } = transport();
  manager.accept(sessionDto('checkout-access'));
  const checkout = modules.createCheckout(new modules.HttpOrderRepository(client));
  const result = await checkout({ restaurantId: 'merchant-a', addressId: 'address-a', method: 'card', expectedTotal: '100.50', cartRevision: 2 }, 'stable-checkout-key');
  assert.equal(request.url, baseUrl + '/checkout');
  assert.equal(request.options.headers['Idempotency-Key'], 'stable-checkout-key');
  assert.deepEqual(JSON.parse(request.options.body), { restaurant_id: 'merchant-a', address_id: 'address-a', payment_method: 'card', expected_total: '100.50', cart_revision: 2 });
  assert.equal(result.restaurantId, 'merchant-a');
  assert.equal(result.paymentStatus, 'pending');
  assert.equal(result.items[0].total, '90.50');
  assert.equal(result.total, '100.50');
});

test('payment HTTP response passes through the real Paymob destination and expiry validator', async () => {
  const url = 'https://eg.checkout.paymob.com/?publicKey=demo-public&clientSecret=demo-intention';
  const expires = new Date(Date.now() + 60_000).toISOString();
  let requested;
  globalThis.fetch = async (address, options) => { requested = { address, options }; return Response.json({ data: { checkout_url: url, expires_at: expires } }); };
  const { manager, client } = transport();
  manager.accept(sessionDto('payment-access'));
  const start = modules.createStartPayment(new modules.HttpPaymentRepository(client));
  assert.deepEqual(await start('order-a'), { url, expiresAt: expires });
  assert.equal(requested.address, baseUrl + '/orders/order-a/payment');
  assert.equal(requested.options.method, 'POST');
});

test('checkout conflicts retain server error codes and request IDs through the HTTP boundary', async () => {
  globalThis.fetch = async () => Response.json({ error: { code: 'cart_price_changed', message: 'Private diagnostic details', details: null, request_id: 'demo-conflict-id' } }, { status: 409 });
  const { manager, client } = transport();
  manager.accept(sessionDto('checkout-access'));
  await assert.rejects(
    new modules.HttpOrderRepository(client).checkout({ restaurantId: 'merchant-a', addressId: 'address-a', method: 'card', expectedTotal: '100.50', cartRevision: 2 }, 'key'),
    error => error.code === 'cart_price_changed' && error.requestId === 'demo-conflict-id' && !error.message.includes('Private diagnostic details'),
  );
});

test('order cancel and Sprint 3 structured address, transaction IDs, preparer, and courier fields map cleanly', async () => {
  const richOrderDto = {
    ...orderDto,
    restaurant_name: 'مشويات بورسعيد',
    restaurant_address: 'شارع الجمهورية، بورسعيد',
    status: 'cancelled',
    delivery_address: {
      ...orderDto.delivery_address,
      floor: '4',
      apartment: '12',
      delivery_notes: 'بجوار مسجد السلام',
    },
    payment: {
      ...orderDto.payment,
      transaction_id: 'tx-local-1',
      provider_transaction_id: 'paymob-999',
    },
    delivery_assignment: {
      delivery_person_id: 'courier-1',
      delivery_person_name: 'محمود المندوب',
      status: 'ASSIGNED',
      assigned_at: '2026-11-21T10:00:00Z',
      updated_at: '2026-11-21T10:00:00Z',
    },
    assigned_preparer: {
      id: 'prep-1',
      name: 'أحمد المحضّر',
    },
  };
  let request;
  globalThis.fetch = async (url, options) => {
    request = { url, options };
    return Response.json({ data: { order: richOrderDto } });
  };
  const { manager, client } = transport();
  manager.accept(sessionDto('customer-access'));
  const cancelled = await new modules.HttpOrderRepository(client).cancel('order-a', 'تغيير خطة');
  assert.equal(request.url, baseUrl + '/orders/order-a/cancel');
  assert.equal(request.options.method, 'POST');
  assert.deepEqual(JSON.parse(request.options.body), { note: 'تغيير خطة' });
  assert.equal(cancelled.restaurantName, 'مشويات بورسعيد');
  assert.equal(cancelled.restaurantAddress, 'شارع الجمهورية، بورسعيد');
  assert.equal(cancelled.deliveryAddressDetails.deliveryNotes, 'بجوار مسجد السلام');
  assert.equal(cancelled.deliveryAddressDetails.floor, '4');
  assert.equal(cancelled.deliveryAddressDetails.apartment, '12');
  assert.equal(cancelled.transactionId, 'tx-local-1');
  assert.equal(cancelled.providerTransactionId, 'paymob-999');
  assert.equal(cancelled.deliveryAssignment?.deliveryPersonName, 'محمود المندوب');
  assert.equal(cancelled.assignedPreparer?.name, 'أحمد المحضّر');
});

test('delivery repository covers couriers, assign/reassign, my-orders, and courier PICKED_UP/DELIVERED status', async () => {
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    if (url.endsWith('/delivery/couriers')) {
      return Response.json({ data: { couriers: [{ id: 'c1', name: 'محمود', phone: '+201012345678', active_order_count: 2 }] } });
    }
    if (url.endsWith('/delivery-assignment') && options.method === 'POST') {
      return Response.json({ data: { order_id: 'order-a', delivery_person_id: 'c1', delivery_person_name: 'محمود', assignment_status: 'ASSIGNED', assigned_at: '2026-11-21T10:00:00Z' } }, { status: 201 });
    }
    if (url.endsWith('/delivery-assignment') && options.method === 'PATCH') {
      return Response.json({ data: { order_id: 'order-a', previous_delivery_person_id: 'c1', new_delivery_person_id: 'c2', new_delivery_person_name: 'يوسف', assignment_status: 'REASSIGNED', updated_at: '2026-11-21T10:05:00Z' } });
    }
    if (url.includes('/delivery/my-orders')) {
      return Response.json({ data: { delivery_person_id: 'c1', orders: [{ ...orderDto, status: 'ready_for_pickup' }], pagination: { limit: 20, offset: 0, has_more: false } } });
    }
    return Response.json({ data: { order_id: 'order-a', previous_status: 'ready_for_pickup', current_status: 'picked_up', order: { ...orderDto, status: 'picked_up' } } });
  };
  const { manager, client } = transport();
  manager.accept(sessionDto('delivery-access'));
  const delivery = new modules.HttpDeliveryRepository(client);

  const couriers = await delivery.listCouriers();
  assert.deepEqual(couriers, [{ id: 'c1', name: 'محمود', phone: '+201012345678', activeOrderCount: 2 }]);

  await delivery.assignCourier('order-a', 'c1');
  assert.deepEqual(JSON.parse(requests[1].options.body), { delivery_person_id: 'c1' });

  await delivery.reassignCourier('order-a', 'c2');
  assert.deepEqual(JSON.parse(requests[2].options.body), { new_delivery_person_id: 'c2' });

  const myOrders = await delivery.listMyOrders(0, undefined, 'ready_for_pickup');
  assert.ok(requests[3].url.includes('status=ready_for_pickup'));
  assert.equal(myOrders.items[0].status, 'ready_for_pickup');

  const pickedUp = await delivery.updateDeliveryStatus('order-a', 'PICKED_UP');
  assert.deepEqual(JSON.parse(requests[4].options.body), { status: 'PICKED_UP' });
  assert.equal(pickedUp.status, 'picked_up');
});

test('notification and operations repositories cover unread inbox, restaurant/menu creation, preparers, and kitchen flow', async () => {
  const requests = [];
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options });
    if (url.includes('/notifications?')) {
      return Response.json({
        data: {
          notifications: [{ id: 'n1', order_id: 'order-a', event_type: 'order_accepted', channel: 'in_app', title: 'تم قبول طلبك', message: 'المطعم قبل الطلب', delivery_status: 'sent', read_at: null, created_at: '2026-11-21T10:00:00Z' }],
          unread_count: 1,
          pagination: { limit: 20, offset: 0, has_more: false },
        },
      });
    }
    if (url.endsWith('/notifications/n1/read')) {
      return Response.json({
        data: { notification: { id: 'n1', order_id: 'order-a', event_type: 'order_accepted', channel: 'in_app', title: 'تم قبول طلبك', message: 'المطعم قبل الطلب', delivery_status: 'sent', read_at: '2026-11-21T10:01:00Z', created_at: '2026-11-21T10:00:00Z' } },
      });
    }
    if (url.endsWith('/notifications/read-all')) {
      return Response.json({ data: { updated_count: 1 } });
    }
    if (url.endsWith('/operations/restaurants') && options?.method === 'POST') {
      return Response.json({
        data: { restaurant: { id: 'rest-new', name: 'سمك الفنار', slug: null, kind: 'restaurant', category: 'مأكولات بحرية', tags: [], description: null, address: 'طرح البحر', rating: '0.0', reviews: 0, time: 30, delivery_fee: '15.00', artwork: 'burger', logo: null } },
      }, { status: 201 });
    }
    if (url.endsWith('/menu-items') && options?.method === 'POST') {
      return Response.json({
        data: { item: { id: 'item-new', restaurant_id: 'rest-new', name: 'جمبري مشوي', category: 'أسماك', desc: null, price: '220.00', artwork: 'burger', available: true } },
      }, { status: 201 });
    }
    if (url.endsWith('/kitchen/orders/order-a/status')) {
      return Response.json({ data: { order: { ...orderDto, status: 'ready_for_pickup' } } });
    }
    if (url.includes('/kitchen/orders')) {
      return Response.json({ data: { orders: [{ ...orderDto, status: 'preparing' }], pagination: { limit: 20, offset: 0, has_more: false } } });
    }
    return Response.json({ data: { order: { ...orderDto, assigned_preparer: { id: 'p1', name: 'كريم' } } } });
  };
  const { manager, client } = transport();
  manager.accept(sessionDto('ops-access'));

  const notifications = new modules.HttpNotificationRepository(client);
  const inbox = await notifications.list({ unreadOnly: true });
  assert.equal(inbox.unreadCount, 1);
  assert.equal(inbox.items[0].eventType, 'order_accepted');
  assert.ok((await notifications.markRead('n1')).readAt);
  assert.equal(await notifications.markAllRead(), 1);

  const ops = new modules.HttpOperationsRepository(client);
  const createdRest = await ops.createRestaurant({
    name: 'سمك الفنار',
    category: 'مأكولات بحرية',
    kind: 'restaurant',
    address: 'طرح البحر',
    deliveryFee: '15.00',
    deliveryMinutes: 30,
  });
  assert.equal(createdRest.address, 'طرح البحر');
  const createdItem = await ops.createMenuItem('rest-new', {
    name: 'جمبري مشوي',
    category: 'أسماك',
    price: '220.00',
  });
  assert.equal(createdItem.price, '220.00');
  const assigned = await ops.assignPreparer('order-a', 'p1', false);
  assert.equal(assigned.assignedPreparer?.name, 'كريم');
  const kitchenPage = await ops.listKitchenOrders();
  assert.equal(kitchenPage.items[0].status, 'preparing');
  const readyOrder = await ops.updateKitchenStatus('order-a', 'ready_for_pickup');
  assert.equal(readyOrder.status, 'ready_for_pickup');
});
