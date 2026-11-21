# Backend Team — Sprint 2 Explained

**Language: English. Reviewed: 3 November 2026.**

This is a teaching guide for explaining the backend team's work. It describes code that exists in this repository, why it was structured that way, and how a request travels through it. The implementation reference is `back/README_SPRINT_2.md`.

## 1. The team's responsibility

The backend owns the rules and persistent state behind the user interface. In Sprint 2 it implemented catalog reads, independent restaurant/store carts, order creation, payment preparation and verification, order history, tracking events and staff operations.

The frontend team owns screens and interactions. The integration team connects frontend repository interfaces to these HTTP contracts. The deployment team provides running services, environment settings and provider callback URLs. The backend must still validate every request because a caller can bypass the UI and call an endpoint directly.

For example, the UI can display EGP 100.50, but the backend determines whether that amount matches current database prices. It also determines whether the address belongs to the caller and whether a payment is really confirmed.

## 2. What was reused and what was added

Sprint 1 already provided customer registration/login, email confirmation, password recovery, Google/Facebook OAuth, JWT access sessions, refresh rotation, roles, permissions, profile and delivery addresses.

Sprint 2 reuses that identity system. It does not create a second customer table or a second login session for ordering.

New work includes:

1. A marketplace catalog backed by database tables and explicit seed data.
2. One separate cart for each customer/merchant pair.
3. Cart quantity, removal and total calculations.
4. Checkout that creates immutable order snapshots.
5. Customer order history and status-event history.
6. Central operations routes for merchant order lists and sequential status changes.
7. Paymob hosted checkout, manual InstaPay review, cash and development-only simulation.
8. Automated regression tests for the complete route/service/repository flow and isolated business rules.
9. Related fixes to email-confirmation sessions and social-login completion.

## 3. Tools and the reason for each

### Python and FastAPI

Python implements the business services. FastAPI exposes HTTP routes and injects dependencies using `Depends`. Each route has a request/response type, which also contributes to the generated OpenAPI schema.

A route should answer HTTP questions: which URL, which method, which DTO, which authenticated caller and which permission. It should not contain a large SQL query or the full payment algorithm.

### Pydantic DTOs

A DTO, or Data Transfer Object, defines the data crossing a boundary. It gives each operation an explicit contract.

The checkout DTO accepts merchant ID, address ID, payment method, reviewed total and cart revision. It does not accept arbitrary user ID, order status, staff permissions or a client-defined final charge.

DTO validation rejects malformed input with 422. Business rules can then return a meaningful application error, such as 409 when the cart changed after review.

### SQLAlchemy and MySQL

MySQL stores the application data. SQLAlchemy maps rows to models and provides parameterized queries, relationships and transaction control.

Repositories hide SQL details behind interfaces. A service requests capabilities such as `get_owned` or `get_for_user`; it does not need to know how a join or row lock is written.

Unique constraints and foreign keys remain necessary even when services validate first. Two requests could otherwise pass the same pre-check at nearly the same time.

### Alembic migrations

Alembic applies schema changes in order. Sprint 2 introduced the ordering schema, extended carts/payments for the marketplace, and expanded catalog image URL storage.

A seed script inserts reference/demo records separately. A migration changes the shape of storage; a seed changes selected records. Neither is equivalent to dropping a production database.

### Redis-compatible Valkey

Valkey supports rate limiting in this application. It helps restrict repeated sensitive requests such as login or email actions. Restaurant, cart and order records remain in MySQL.

The automated HTTP suite replaces the limiter so tests remain isolated. Separate unit tests exercise the rate-limit adapter with a fake Redis client. This does not claim the real Lua script or production Valkey connection was executed.

### HTTPX, Paymob and cryptography

HTTPX performs server-to-server provider requests with TLS verification, a bounded timeout and no automatic POST retry. Paymob handles the hosted card/wallet page. HMAC verifies provider callbacks. Fernet encrypts the stored one-time checkout token.

Foodify never receives a card number, CVV or OTP through its API.

## 4. How the architecture is organized

The architecture is intentionally small and operation-based:

```text
Feature -> Operation -> router / DTO / interface / service / dependencies
```

A concrete example is `back/app/cart/add_item/`:

| File | Responsibility |
| --- | --- |
| `router.py` | Defines the POST route and requires the authenticated customer. |
| `dto.py` | Defines/reuses the product ID, strict quantity and cart response contract. |
| `interfaces.py` | Describes the service contract used by the router. |
| `service.py` | Adds/merges a line, checks availability and limits, increments the cart revision. |
| `dependencies.py` | Constructs the service with user/cart/catalog adapters and a unit of work. |

Shared SQL adapters live in `back/app/ordering/infrastructure/`. Shared ordering models and value mapping live in `back/app/ordering/`. Provider-specific HTTP code lives in `back/app/payments/infrastructure/paymob.py`.

### How this applies SOLID

- **Single Responsibility:** one operation service handles one use case; HTTP, SQL and payment transport have separate classes.
- **Open/Closed:** a gateway/repository can be replaced by another adapter implementing the same port.
- **Liskov Substitution:** a replacement must honor the same input, output and error expectations; tests use substitutes to exercise those contracts.
- **Interface Segregation:** callers receive the capabilities relevant to their responsibility instead of a universal application object.
- **Dependency Inversion:** services depend on ports, while dependency factories supply SQLAlchemy/HTTPX implementations.

This is a practical design, not a claim that merely adding interface files automatically guarantees every SOLID property.

## 5. Database relationships explained

A customer can have multiple carts, but only one per merchant. The unique key is `(user_id, restaurant_id)`.

A merchant has many menu items. A cart has many lines, with unique `(cart_id, menu_item_id)`, so adding the same product again changes quantity rather than duplicating a row.

Merchants can appear in several browse categories, such as desserts and bakery. This is many-to-many through `restaurant_categories`. Customer favorites use another bridge, `favorite_restaurants`.

Orders belong to one customer and one merchant. Each order has line snapshots, a payment lifecycle record and a list of status events. Payment events retain provider transaction processing history.

### Why an order copies a name, price and address

Normalization prevents accidental duplication of current data. Historical records have a different requirement: they must retain what the customer purchased.

If a burger price changes tomorrow, yesterday's order must keep yesterday's price. If a customer removes a saved address, an old order must still show where it was delivered. These snapshots are deliberate historical data, not an abandoned duplicate source.

## 6. Walkthrough: browse, add and review

Suppose a customer opens a burger merchant.

1. `GET /api/v1/restaurants` reads active merchant records with bounded filters and pagination.
2. `GET /api/v1/restaurants/{id}/menu` loads that merchant's products.
3. `POST /api/v1/carts/{merchant_id}/items` supplies a product ID and quantity two.
4. The customer identity comes from the authenticated session, not the submitted JSON.
5. `AddCartItemService` obtains the customer/cart lock, validates product ownership and availability, then merges or creates the line.
6. The cart revision increases. The response includes item totals, subtotal, delivery and total.

Two units at EGP 45.25 plus EGP 10 delivery give:

```text
subtotal = 45.25 x 2 = 90.50
final total = 90.50 + 10.00 = 100.50
```

The code uses `Decimal`, not binary `float`. An empty cart has zero delivery charge.

Opening a supermarket creates/loads a different cart. Its products do not replace the burger cart, and the two merchants create separate orders and payments.

## 7. Walkthrough: checkout and duplicate-click protection

The browser sends an `Idempotency-Key` header and a checkout DTO containing the merchant, owned address, method, reviewed total and cart revision.

`CheckoutService` first checks whether the same customer already used that key. If the fingerprint matches, the service returns the existing order. If the key is reused for different data, it returns a conflict.

For a new checkout it verifies:

- The cart is nonempty and has the revision the customer reviewed.
- The merchant is active and all products are still available.
- The address belongs to the customer.
- Current database prices equal the reviewed total.
- The payment method is enabled and the total is within the supported limit.

It then writes the order, item/address snapshots, payment and first event in one transaction. A failure rolls the transaction back rather than leaving half an order.

The client-supplied total is a review acknowledgement. It is never accepted as the source of truth for the amount to charge.

## 8. Walkthrough: card or mobile-wallet payment

The order initially has status `awaiting_payment`. The frontend calls `POST /api/v1/orders/{id}/payment`.

`StartPaymentService` checks ownership and payment state. It records `initializing` and commits before calling Paymob, so a slow provider request does not hold database row locks.

The gateway submits a Paymob intention using a backend secret key. It groups each order line into its complete price, includes delivery, and checks that provider item totals exactly match the saved order total.

The returned client secret is encrypted for storage. The public response contains a short-lived HTTPS checkout URL. The browser navigates to Paymob for card/wallet input.

### The difference between rejected and unknown setup

A definite validation/authentication rejection means setup did not create a usable intention, so the payment can return to `pending` for a controlled retry.

A timeout, uncertain provider response, 5xx or malformed successful response may mean an intention was created remotely. The service stores `initialization_unknown` and blocks automatic resubmission. Support must reconcile it before another potentially chargeable intention is created.

If an unexpired intention already exists, reopening payment returns its existing checkout URL. It does not create another one.

### How payment is actually confirmed

Paymob sends a signed callback to the backend. The gateway verifies the ordered HMAC SHA-512 fields using constant-time comparison.

The application then matches provider order, amount, currency and integration ID against the saved payment. It records a deduplicated event and confirms the order.

The customer being redirected back to the website is not proof of payment. The return route ignores `success=true` and other browser query flags. The frontend reads the authenticated order API to display the recorded result.

Repeated callbacks do not repeat settlement. A late failure cannot turn a paid order into failed. A refund is retained for operational review. A bank/provider transaction reference cannot be reused to settle a second order.

## 9. Walkthrough: manual transfer and cash

For InstaPay, the API returns a configured recipient and saves those recipient details with the order. The customer transfers externally and submits a reference. The payment becomes `pending_review`.

A staff member with `payments:review` verifies the bank record, records a unique bank reference and approves or rejects the claim. Only approval changes payment to `paid`. This is explicitly manual verification; the application does not claim a direct InstaPay banking integration.

Cash starts `due_on_delivery`. Central operations move the order through fulfillment; confirming delivery also confirms cash collection.

Simulation is provided only for development/test environments. It cannot be enabled in production by setting the simulation flag alone.

## 10. Tracking and staff access

The allowed fulfillment sequence is:

```text
placed -> preparing -> ready -> out_for_delivery -> delivered
```

An online payment must be verified before the first fulfillment stage. Staff cannot jump directly from `placed` to `delivered`. Each change records status, timestamp, actor and an optional note.

Customers read only their own orders. Operations managers/admins have the relevant permissions. The restaurant order list is a central operations API in this release; it does not implement separate store-owner tenancy or per-branch employee assignments.

There is no simulated courier GPS data. Courier assignment and live location are separate future requirements.

## 11. Related identity-flow repairs

Email confirmation previously confirmed the address but returned the browser to login. `VerifyBrowserEmailService` now confirms the one-use proof and creates a session in one transaction. The browser response includes access credentials and an HttpOnly refresh cookie, without exposing the raw refresh value in JSON.

If session creation fails, the email proof remains usable after rollback. Tests cover failure, unchanged database state and a successful retry.

OAuth completion uses one-use, browser-bound tickets. The Google provider is mocked in tests, but the local state/ticket/session repositories are real. A wrong browser verifier cannot exchange the ticket, and a failed verifier attempt does not consume the legitimate browser's ticket. Matching a provider email does not silently link an existing password account.

The frontend handles the next step: customers missing phone/address go to onboarding. That navigation decision is frontend responsibility; the backend exposes profile completeness and the required fields.

## 12. Unit tests and integration tests: what each means

### Unit test

A unit test isolates a small rule or adapter by replacing its dependencies. It does not start the FastAPI application or connect a database.

Examples here include Decimal rounding, zero delivery on an empty cart, confirmation commit/rollback orchestration, HMAC rejection, timeout uncertainty and fake Redis error handling.

A timeout test gives the gateway an in-process HTTPX transport that raises `ReadTimeout`. It proves the gateway returns an unknown outcome instead of incorrectly claiming payment failed or automatically retrying.

### Integration test

An integration test checks cooperating application layers. Here it sends an HTTP request to FastAPI's `TestClient`, passes real DTO validation/authentication, invokes services and runs real SQLAlchemy repositories against a fresh SQLite in-memory database.

For example, the duplicate-checkout test creates a customer, address and cart, submits checkout twice with the same key, and checks that only one order exists. That proves more than merely checking a helper's return value.

Payment-provider calls, Google identity exchange and the Redis connection remain fakes. These are application integration tests with substituted external systems, not live-provider end-to-end tests.

### Commands

From `back/`, after installing `requirements-test.txt`:

```bash
.venv/bin/python -m pytest -q -m unit
.venv/bin/python -m pytest -q -m integration
.venv/bin/python -m pytest -q --cov=app --cov-report=term-missing
```

Every test has exactly one marker. The collection hook rejects missing or overlapping classification. Socket connections are blocked for every test; fixtures do not load real environment files, send mail or touch MySQL.

The complete backend suite passed **172 cases: 37 unit and 135 integration** on 3 November 2026. Measured statement coverage across `app` was **89.41%** (`4003 / 4477` statements); runtime was 46.96 seconds on the review machine. Coverage measures executed Python statements, not security completeness. The testing guide explains the cases by responsibility and the separate commands.

### What the tests do not prove

SQLite does not reproduce MySQL row locks, repeatable-read snapshots, migration DDL or concurrent transactions. Fake Redis does not run the real Lua script. Mock providers do not validate live OAuth console settings, SMTP delivery, real payment settlement or webhook reachability.

A separate staging environment with MySQL, Valkey and provider Sandbox settings is needed for those checks. These limits are explicit so the team can explain exactly what a passing suite means.

## 13. Problems found and corrected during the final review

1. The earlier OAuth wrong-browser test used an invalid short verifier and reached DTO validation instead of the intended security rule. Its input was corrected to a valid-length wrong verifier and extended to prove the legitimate browser can still complete sign-in.
2. Paymob malformed success data could include an empty intention ID or a nonpositive provider order ID. These values now produce `payment_initialization_unknown` and are not saved as a valid checkout.
3. Reusing an InstaPay verified reference could trigger an implicit SQLAlchemy flush during a cart read, bypassing the unit-of-work conflict translation and producing 503. An explicit flush now returns a safe 409 before settlement continues.
4. A separate regression verifies that a consumed provider transaction/status event cannot settle another order: the replay is acknowledged without changing the second order or creating another event.
5. Regressions now cover refunds, repeated callbacks, late failures, unknown provider orders, payment ownership and preservation of cart changes made during payment.

## 14. How to explain the documentation tools honestly

FastAPI generates the OpenAPI contract from the route declarations, DTOs and response models. Swagger UI presents that generated contract interactively. Those are real automatic documentation tools used by this backend.

The written team explanations are authored Markdown. MkDocs converts those Markdown files into a navigable documentation website. It renders and organizes the explanation; it does not infer all business rules or write the handbook automatically.

A correct presentation statement is: “We used FastAPI OpenAPI and Swagger UI for the API contract, and MkDocs to build the authored team documentation.” The team should not claim that a tool automatically wrote text it did not generate.

## 15. Presentation questions and answers

**Why keep business logic out of routes?** To make the operation reusable, testable and independent of HTTP and storage details.

**Why does each merchant have a cart?** An order must belong to one merchant, while browsing another merchant must preserve the first cart.

**Why is `expected_total` sent if the server calculates money?** It confirms the customer reviewed the same price. A price change should require review, not silently change the charge.

**How do duplicate clicks avoid duplicate orders?** A customer-scoped idempotency key and payload fingerprint return the same saved order, backed by a unique database constraint.

**Why not mark paid when the browser returns?** Browser URLs are customer-controlled. Payment requires a verified provider callback or authorized bank review.

**Why keep an unknown payment state?** A timeout does not prove the provider failed to create an intention. Blindly retrying could create a second chargeable process.

**Why copy order prices and addresses?** A historical order must remain stable when current menu/address records change.

**What does Valkey store here?** Rate-limit counters; core commerce records are in MySQL.

**Do the tests prove production MySQL concurrency?** No. They verify application rules and persistence behavior with SQLite; MySQL-specific locking needs staging verification.

**What still needs a future sprint?** Store-owner tenancy, courier assignment/GPS, automatic reconciliation, initiating refunds, and additional live-provider operational checks.
