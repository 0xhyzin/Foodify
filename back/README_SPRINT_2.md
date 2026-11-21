# Foodify Backend — Sprint 2 Implementation Reference

Reviewed on **3 November 2026**. This backend document is intentionally written in English. The frontend, integration and deployment team guides are written in Arabic.

This document describes implemented behavior in the current source tree. It is not a claim that local changes have already been deployed, that every third-party account is configured, or that live payments have been processed.

## 1. Delivered scope

Sprint 2 extends the existing customer identity API with a database-backed marketplace, independent merchant carts, checkout, order history, order tracking, operational order management and payment workflows.

| Requirement | Implementation |
| --- | --- |
| Cart creation and management | One cart per customer and merchant; adding the first item can create the cart. |
| Quantity, removal and totals | Strict integer quantities from 1 to 99; merging repeated additions; item removal; clearing one cart; server-calculated totals. |
| Delivery addresses | Existing Sprint 1 address operations are reused, including ownership and default-address rules. |
| Checkout validation | Active merchant, available items, owned address, current cart revision, reviewed price and enabled payment method. |
| Order submission and confirmation | Atomic order creation; retry protection with an idempotency key; immutable item and delivery-address snapshots. |
| Order history | Authenticated, owner-scoped history and order details. |
| Restaurant order list | A backend API restricted to central operations staff with `orders:manage`. |
| Initial payment workflow | Paymob hosted card/wallet checkout, manually reviewed InstaPay, cash on delivery and development-only simulation. |
| Tracking | Persisted order events and validated status transitions; the backend is authoritative. |
| Unit and integration tests | Separate, marked pytest groups; isolated SQLite database; blocked external sockets and mocked providers. |

The system supports restaurants, dessert shops and groceries through catalog data and merchant categories. Production catalog records are stored in MySQL. Seed JSON is an input for an explicit seed script; it is not a frontend fallback or a separate live data source.

## 2. Technology choices

| Technology | Purpose and reason |
| --- | --- |
| Python + FastAPI | HTTP endpoints, dependency injection, automatic OpenAPI description and explicit response contracts. |
| Pydantic | DTO validation before business logic; output validation before transaction commit where applicable. |
| SQLAlchemy | Repository adapters, relationships, parameterized queries and transactions. |
| MySQL + PyMySQL | Persistent production application data with unique constraints and row locks. |
| Alembic | Ordered schema migrations; application startup does not silently recreate production tables. |
| Redis-compatible Valkey | Rate limiting; it is not the source of restaurant, cart or order data. |
| JWT + Argon2id | Short-lived access credentials and password hashing. Refresh/session records allow revocation. |
| Fernet | Encryption of sensitive email-outbox payloads and stored Paymob checkout tokens. |
| HTTPX | Bounded, TLS-verified server-to-server provider requests. |
| pytest + pytest-cov | Automated unit/integration cases and measured Python statement coverage. |
| FastAPI OpenAPI/Swagger UI | A schema generated from the actual route and DTO declarations. |

The dependency lock is `back/requirements.lock.txt`. `back/pyproject.toml` reads its runtime dependencies from the same lock used by Docker. The wheel includes the local Swagger JavaScript and the catalog/category JSON resources.

## 3. Simplified Clean Architecture

```text
HTTP request
  -> router.py                 HTTP contract, authentication and permission dependency
  -> dto.py                    validated request values
  -> service.py                one business operation
  -> interfaces / ports        required capabilities, independent of SQL or provider details
  -> repository / gateway      SQLAlchemy or HTTPX adapter
  -> UnitOfWork                flush, commit or rollback
  -> response DTO              public fields only
```

Operations are grouped by feature and then by action, rather than collecting every user/cart function in one file:

```text
back/app/
  restaurants/
    list_restaurants/ get_restaurant/ list_menu/ list_categories/
    browse_categories/ list_favorites/ set_favorite/
  cart/
    create_cart/ get_cart/ list_carts/ add_item/
    update_item/ remove_item/ clear_cart/
  checkout/submit_order/
  orders/
    list_orders/ get_order/ list_restaurant_orders/ update_status/
  payments/
    list_methods/ start_payment/ process_callback/
    claim_transfer/ review_transfer/ infrastructure/ shared/
  ordering/
    models.py
    infrastructure/           SQLAlchemy adapters and payment-method configuration
    shared/                   shared DTOs, ports, money, guards and mapping
  users/                      existing identity, session and address operations
```

Each operation normally contains `router.py`, `dto.py`, `interfaces.py`, `service.py` and `dependencies.py`. Shared DTOs are re-exported when the contract is genuinely shared. Dependency factories construct the concrete service; routes depend on a service interface. SQL stays in repository adapters, provider HTTP stays in gateways, and services own the business sequence and transaction boundary.

This applies SOLID practically: each class has one operation, new adapters can implement the same port, and services receive dependencies rather than instantiate storage clients internally. It does not introduce an interface for every trivial arithmetic function.

## 4. Database design and redundancy

| Relationship | Representation |
| --- | --- |
| User -> Cart | One-to-many, with unique `(user_id, restaurant_id)`. |
| Restaurant -> MenuItem | One-to-many. A product belongs to one merchant. |
| Cart -> CartItem | One-to-many, unique `(cart_id, menu_item_id)`. |
| Restaurant <-> BrowseCategory | Many-to-many through `restaurant_categories`. |
| User <-> FavoriteRestaurant | Many-to-many through `favorite_restaurants`. |
| User / Restaurant -> FoodOrder | One-to-many. Each order contains products from one merchant. |
| FoodOrder -> FoodOrderItem | One-to-many historical order lines. |
| FoodOrder -> Payment | One payment lifecycle record per order. |
| Payment -> PaymentEvent | One-to-many, with unique event identifiers. |
| FoodOrder -> OrderEvent | One-to-many status history. |
| User <-> Role <-> Permission | Existing role and permission bridges are reused. |

A second merchant has a second cart; entering it does not delete the first cart. A repeated product addition increases an existing cart line rather than inserting duplicate lines.

Historical duplication is deliberate: an order copies item name, unit price and delivery-address fields at purchase time. Editing a menu item or deleting a saved address must not rewrite an old invoice. Current catalog/address data remains normalized separately.

`Decimal` and database decimal columns are used for money. Public monetary JSON values are strings, preventing binary floating-point differences. Quantities, nonnegative totals, unique keys and foreign keys have database constraints as a second line of protection.

Schema/ERD reference: `back/docs/SPRINT_2_SCHEMA.md`. Marketplace/payment migrations: `back/migrations/versions/20261031_0004_marketplace_payments.py` and `20261031_0005_catalog_image_urls.py`.

## 5. Operation reference

| Service / helper | What it does and where it continues |
| --- | --- |
| `ListRestaurantsService` | Validates browse filters/pagination, calls the catalog repository, maps public merchant views. |
| `GetRestaurantService` / `ListMenuService` | Reads active merchant details or available menu data through the catalog adapter. |
| `SetFavoriteService` | Changes the current customer's merchant favorite state idempotently. |
| `CreateCartService` / `lock_cart` | Acquires the common user lock, finds or creates that customer's cart for one merchant. |
| `AddCartItemService` | Validates merchant ownership/availability, merges a product line, enforces quantity/line limits and increments revision. |
| `UpdateCartItemService` | Sets an owned cart line's quantity and increments revision. |
| `RemoveCartItemService` / `ClearCartService` | Removes one line or clears one merchant cart; other carts remain intact. |
| `present_cart` / `cart_response` | Loads current menu values and calculates subtotal, delivery fee and total. An empty cart has no delivery fee. |
| `CheckoutService` | Checks the idempotency fingerprint, cart revision, prices, address and payment method; creates order snapshots atomically. |
| `StartPaymentService` | Creates one Paymob intention or reopens a valid stored checkout; blocks a retry when the outcome is uncertain. |
| `PaymobHostedGateway` | Builds the intention request, groups line totals correctly, encrypts the checkout token and verifies callback HMAC. |
| `ProcessCallbackService` | Matches a verified callback to the recorded order, deduplicates events and applies payment state safely. |
| `ClaimTransferService` | Records the customer's claimed transfer reference without marking the payment paid. |
| `ReviewTransferService` | Requires an operations permission, records bank verification and approves/rejects a pending claim. |
| `confirm_paid_order` | Places an awaiting-payment order and clears its cart only if that cart has not changed. |
| `UpdateOrderStatusService` | Enforces the next allowed fulfillment stage and records actor/time/note. Cash becomes paid when delivery is confirmed. |
| `VerifyBrowserEmailService` | Confirms a one-use email proof and creates its session in the same transaction; failures roll back both. |

Exact class definitions and helper names are available in the operation directories above. Some shared service methods use the name `execute`; the feature folder and class specify the action.

## 6. Cart and checkout lifecycle

1. The authenticated customer adds a product ID and quantity to `/carts/{restaurant_id}/items`.
2. The backend derives the customer ID from the access session. It never accepts another customer's identity from the request body.
3. The service locks the common parent user row and merchant cart, then checks the current product's merchant and availability.
4. The backend returns a cart with a revision and totals calculated from database prices.
5. At checkout the browser supplies an owned address, method, reviewed `expected_total`, `cart_revision` and UUID `Idempotency-Key`.
6. The backend recalculates the price under current reads. A different revision or price returns a conflict, requesting another review.
7. One transaction persists the order, line snapshots, address snapshot, payment record and initial event.
8. Cash/simulation can place the order immediately. Online/manual payment creates `awaiting_payment`; its cart stays until verified settlement.
9. Repeating the same key and payload returns the same order. Reusing the key for another payload returns 409.
10. Settlement clears only the unchanged originating cart. Items added while paying are preserved.

Example: two burgers at EGP 45.25 plus EGP 10 delivery produce subtotal `90.50` and total `100.50`. The browser cannot change the charge to `1.00` by modifying JSON; the backend compares it to current database prices and rejects a mismatch.

## 7. Payment flows and safeguards

### Paymob hosted checkout

```text
POST /checkout -> awaiting_payment order
POST /orders/{id}/payment -> server creates intention
React navigates to Paymob HTTPS checkout
Paymob sends signed POST callback
Backend verifies HMAC + amount + currency + integration + provider order
Backend records event and settles order
Customer returns to React -> authenticated GET /orders/{id}
```

PAN, CVV and OTP are entered on Paymob, never through Foodify inputs. The backend uses the secret key; frontend builds contain no provider secret. The current hosted URL is `https://eg.checkout.paymob.com/`; the frontend validates the allowed provider host/path and required parameters.

For quantity two, the gateway sends one grouped Paymob line with the complete order-line amount and a label describing the actual quantity. It checks that all provider line amounts plus delivery equal the recorded total exactly.

HMAC verification uses SHA-512, the prescribed ordered fields and constant-time comparison. A valid signature alone is insufficient: amount, currency, integration ID and the stored provider order must match. A customer-controlled return query such as `success=true` never settles an order.

A known provider setup rejection returns the payment to a retryable `pending` state. A timeout, 5xx or malformed success response becomes `initialization_unknown`: an intention may have been created, so an automatic second intention could duplicate a charge. Reconciliation is a manual support task in this version. An existing valid token reopens the same intention.

Repeated callbacks are idempotent. Late failures do not reverse a paid state. A refund/void is recorded for operational review and cannot be undone by a repeated paid event. The same provider transaction cannot settle two orders.

### InstaPay

This is a manual transfer workflow, not an automatic bank API. The configured recipient is snapshotted onto the payment. The customer submits a reference, producing `pending_review`. Staff with `payments:review` must verify the bank account and record a unique verified reference before approval. Customer claims alone never produce `paid`.

### Cash and simulation

Cash starts `due_on_delivery`; the authorized delivery confirmation records collection. Simulation is explicitly labeled and disabled in production, even if its enable flag is accidentally set.

Paymob Sandbox still needs real Sandbox account configuration. Localhost cannot receive provider webhooks from the internet; a reachable HTTPS backend/tunnel is required for full external callback verification.

## 8. Orders, tracking and permissions

```text
awaiting_payment -> placed -> preparing -> ready -> out_for_delivery -> delivered
```

Payment verification performs the first transition. Authorized operations staff perform the later transitions sequentially. Unpaid or refunded online orders cannot enter fulfillment. Every transition records an event instead of replacing history.

Customers may read their own orders only. `operations_manager` and `admin` are central operations roles in this version. The restaurant order-list route requires `orders:manage`; it is not an independent restaurant-owner tenancy boundary. Courier assignments, live GPS and store-specific employee assignment are not implemented.

## 9. Sprint 2 API routes

All paths below use the `/api/v1` prefix. Customer and operations routes require Bearer access credentials. Catalog and enabled-payment-method reads are public. Paymob callbacks use their signature instead of a customer JWT.

| Method | Path | Result / authorization |
| --- | --- | --- |
| GET | `/restaurants` | Filtered, sorted, paginated catalog. |
| GET | `/restaurants/{id}` | Active merchant details. |
| GET | `/restaurants/{id}/menu` | Merchant products; optional category filter. |
| GET | `/restaurants/{id}/categories` | Merchant menu categories. |
| GET | `/catalog/categories` | Marketplace browse categories. |
| GET | `/users/me/favorites` | Current customer's favorites. |
| PUT | `/users/me/favorites/{id}` | Set `favorite: true/false`. |
| GET | `/carts` | Current customer's nonempty carts. |
| GET / POST / DELETE | `/carts/{restaurant_id}` | Read / create / clear one merchant cart. |
| POST | `/carts/{restaurant_id}/items` | Add or merge a product. |
| PATCH / DELETE | `/carts/{restaurant_id}/items/{item_id}` | Update quantity / remove owned line. |
| POST | `/checkout` | Validated, idempotent order creation. |
| GET | `/orders` | Current customer's order history. |
| GET | `/orders/{id}` | Owned order details and event history. |
| GET | `/restaurant/orders?restaurant_id={id}` | Central staff order list, `orders:manage`. |
| PATCH | `/operations/orders/{id}/status` | Next stage, `orders:manage`. |
| GET | `/payments/methods` | Enabled methods and public transfer-recipient details. |
| POST | `/orders/{id}/payment` | Start/reopen owned Paymob checkout. |
| POST | `/payments/paymob/callback?hmac=...` | Signed provider callback. |
| GET | `/payments/return/{id}` | Redirect to order page; never confirms payment. |
| POST | `/orders/{id}/transfer-claim` | Customer transfer claim. |
| POST | `/operations/orders/{id}/transfer-review` | Bank verification, `payments:review`. |
| POST | `/auth/browser/verify-email` | Origin-protected confirmation plus HttpOnly session. |

The complete machine-readable contract is `/openapi.json`; `/docs` renders it through Swagger UI. Postman collections are in `back/postman/` and contain placeholders, not production secrets.

## 10. Security review

Security decisions include parameterized SQL, strict DTO fields, owner-scoped reads, server-side permission checks, bounded queries and quantities, session revocation, Argon2id, browser Origin/client-header validation, rate limiting, TLS provider calls, encrypted provider tokens, idempotency, safe error messages and sensitive-data-free logs.

Browser refresh tokens are HttpOnly cookies; refresh values are excluded from browser JSON. Google state and one-use completion tickets are bound to the originating browser verifier. Existing password accounts are not silently linked merely because a provider reports the same email.

These controls address relevant OWASP risks, but the tests are not a certification, a penetration test or proof that all OWASP Top 10 risks are eliminated.

## 11. Unit and integration testing

From the repository root:

```bash
cd back
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -q -m unit
python -m pytest -q -m integration
python -m pytest -q --cov=app --cov-report=term-missing
```

If `.venv` already exists with the required packages, only activation and the pytest commands are needed. `requirements-test.txt` uses the runtime lock and pins pytest/pytest-cov. No database URL, SMTP credential, OAuth secret or Paymob credential is needed to run these tests.

Every collected test has exactly one marker. The collection hook rejects unclassified or doubly classified tests so the two groups cover the complete suite without overlap.

| Group / file | What it proves |
| --- | --- |
| Unit — `test_domain_units.py` | Decimal rounding, empty-cart delivery fees, availability mapping and confirmation transaction orchestration. |
| Unit — `test_payment_units.py` | Invalid/missing HMAC, provider-error status, malformed success responses, timeout uncertainty and no request for inconsistent totals. |
| Unit cases in `test_payments.py` | Callback state rules and production simulation disabling. |
| Unit cases in `test_security.py` | Rate-limit key privacy, Retry-After and fail-closed adapter behavior with fake Redis. |
| Integration — `test_auth.py` | Registration, confirmation/session atomicity and rollback/retry, refresh rotation/replay, password reset and revocation. |
| Integration — `test_oauth.py` | Mocked Google identity through real state/ticket/session flow, wrong binding and replay rejection, no silent account linking. |
| Integration — `test_profile_auth.py` | Profile validation, address ownership and operational permissions. |
| Integration — `test_restaurants.py` | Database catalog, filters, bounded pagination, menus, hidden inactive merchants and favorites. |
| Integration — `test_ordering.py` | Separate carts, quantity limits, trusted totals, snapshots, stale-cart rejection, idempotency, ownership and sequential tracking. |
| Integration — `test_payments.py` | Callback-to-database settlement, duplicate/refund behavior, unchanged/changed carts, intention reuse, payment ownership and unique bank/provider references. |
| Integration cases in `test_security.py` | JWT rejection, revoked accounts, structured errors, CORS, trusted hosts and security headers. |

**Final reviewed run (3 November 2026): 172 passed, comprising 37 unit cases and 135 integration cases.** The complete suite measured **89.41% statement coverage** (`4003 / 4477` statements) across `app`; no coverage threshold is presented as a production-readiness guarantee. The full coverage run completed in 46.96 seconds on this machine. A passing unit test verifies an isolated rule; a passing integration test verifies cooperating application layers. Neither by itself proves third-party production behavior.

The integration fixture creates a fresh SQLite in-memory schema per test, enables foreign keys, uses fake credentials, overrides dependencies, disables embedded email delivery and blocks socket connections. Provider responses and Redis are in-process fakes. Real customer data is never reset and no messages, charges or external intentions are sent.

**Limits:** SQLite does not prove MySQL row locking, repeatable-read isolation, concurrent checkout serialization, migration DDL or MySQL-specific constraints. Fake Redis does not execute the real Redis Lua script. Provider fakes do not prove live Google consent, SMTP delivery or Paymob settlement. Those require a separately controlled staging review with MySQL, Valkey and Sandbox accounts.

## 12. Final review fixes and remaining scope

The review corrected email-confirmation session issuance, OAuth frontend-origin consistency, Paymob item-total/hosted-checkout handling and conservative uncertain-outcome handling. New regression coverage also found that an implicit SQLAlchemy flush could bypass safe conflict translation when reusing a verified bank reference. An explicit unit-of-work flush now rejects that conflict before settlement reads; the second order remains unpaid. A separate regression confirms that a consumed provider event cannot settle another order.

An empty intention identifier or nonpositive provider order identifier in a purported successful provider response is also treated as uncertain, preventing a broken payment link from being saved as a valid intention.

Out of scope: automatic bank reconciliation, initiating refunds from Foodify, restaurant-owner tenancy, courier assignment/GPS, real-time push transport and production provider-account approval. These are documented boundaries rather than simulated completed functionality.
