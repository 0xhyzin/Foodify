# Backend Team — Sprint 1

## 1. Purpose and scope

Sprint 1 establishes the customer account foundation for Foodify. The backend receives account requests, validates them, applies business rules, persists normalized data, and returns structured responses to the website or another API client.

The customer can register, verify an email address, sign in, recover a password, continue through Google or Facebook, complete a profile, and manage delivery addresses. Persistent sessions support continuing to use the application after a short access token expires.

This chapter explains the current implementation of those account features. The sprint grouping describes the functional scope; it does not claim that every current safeguard was introduced on the first development day. In particular, browser confirmation that creates a session is a later integration correction to the original account flow.

Restaurants, menu items, carts, checkout, orders, and payments belong to Sprint 2. They reuse the authenticated customer identity and address ownership rules established here.

## 2. Technologies and their actual responsibilities

| Technology | Responsibility in this project |
| --- | --- |
| Python and FastAPI | Implement use cases, expose HTTP endpoints, and assemble dependencies. |
| Pydantic | Validate request and response DTOs and reject unexpected input fields. |
| SQLAlchemy | Map Python entities to relational tables and implement repositories. |
| MySQL | Store customers, addresses, roles, sessions, action tokens, and outbox jobs. |
| Alembic | Apply versioned database schema changes. |
| PyJWT | Sign and verify access JWTs with required claims. |
| Argon2 | Hash and verify passwords using Argon2id. |
| Redis or compatible Valkey | Share atomic abuse limits between API processes. |
| Fernet | Encrypt sensitive transactional email payloads before storing them. |
| SMTP or configured email adapter | Deliver the email that the outbox worker has claimed. |
| Docker Compose and Uvicorn | Run development services and the ASGI API process. |

FastAPI also generates OpenAPI from the routes and DTOs. Swagger UI presents that contract interactively. These tools document HTTP contracts; they do not automatically write the explanations of business rules in this chapter.

MySQL is the source of truth for customer data. Redis does not replace the database and does not store the authoritative user profile. The identity implementation uses Redis for rate limiting, including across multiple API workers.

## 3. Simplified Clean Architecture

The code starts with a feature such as `app/users/`, then separates individual actions into folders. Login is in `app/users/login/`; registration is in `app/users/register/`. The application does not put every account function inside a single service file.

Each operation normally contains `dto.py`, `interfaces.py`, `service.py`, `dependencies.py`, and `router.py`. The route handles HTTP. The DTO declares the permitted data. The service executes one use case. The interface describes its contract. The dependency file constructs the service with the adapters it needs.

The typical execution path is: request → route → validated DTO → service → repository or security port → infrastructure adapter → database → response DTO.

Repositories live in `app/users/shared/repositories/` because several account operations use the same entities. Sharing `SqlAlchemyUserRepository` avoids creating a separate, duplicated user-storage implementation for every endpoint.

`app/users/shared/interfaces.py` contains account contracts such as `UserRepository`, `SessionRepository`, `ActionTokenRepository`, and `SocialRepository`. `app/shared/ports.py` declares reusable ports such as `UnitOfWork`, `PasswordHasher`, `TokenCodec`, `EmailSender`, and `OAuthGateway`.

Dependencies are assembled in `app/users/shared/dependencies/` and each operation's local `dependencies.py`. FastAPI's `Depends` supplies them. Business services receive dependencies through constructors, so they do not construct database connections or SMTP clients themselves.

The design is deliberately simplified: services use shared ORM entities instead of duplicating an identical domain entity and mapper for every table. It follows separation of responsibilities while avoiding unnecessary layers for this project's size.

## 4. How SOLID appears in the code

Single Responsibility is visible in `LoginService.execute`, which validates credentials and opens a session. It does not manage addresses, process orders, or send SMTP messages itself.

Open/Closed and Dependency Inversion appear at adapter boundaries. A service depends on the `EmailSender` or `PasswordHasher` contract; replacing an implementation is principally a dependency-composition change rather than rewriting every use case.

Interface Segregation keeps an operation's service contract focused on its own input and output. Shared ports describe specific responsibilities rather than a general object with unrelated methods.

Liskov Substitution means an adapter must honor the contract's behavior. An alternative `SessionRepository` must preserve lookup and revocation semantics, not merely provide methods with the same names. The presence of interfaces alone does not prove every substitution is safe.

## 5. Transactions and Unit of Work

`app/infrastructure/database.py` creates the SQLAlchemy engine and request-scoped sessions. The repositories and Unit of Work used by one request share the same database session.

`SqlAlchemyUnitOfWork` in `app/infrastructure/unit_of_work.py` exposes `flush`, `commit`, and `rollback`. It converts SQLAlchemy integrity conflicts into the application-level `PersistenceConflict` type.

`flush` sends pending changes to the database transaction without making them final. It is needed, for example, before assigning the ID of a newly inserted address as the user's default address.

`commit` finalizes a coherent change. Registration commits the new customer, verification token, and encrypted email job together. A failure should not leave a customer created without the corresponding confirmation job.

Services decide the transaction boundary. Repositories perform storage operations; they do not independently commit every statement. Some sensitive operations lock the user row to serialize competing changes.

## 6. Account database design

| Table or relationship | Purpose and duplication control |
| --- | --- |
| `users` | One customer identity; email is unique. |
| `roles` and `permissions` | Define role codes and permission codes once. |
| `user_roles` | Many-to-many user/role bridge with a composite primary key. |
| `role_permissions` | Many-to-many role/permission bridge; repeated assignments are prevented. |
| `addresses` | Many delivery addresses belong to one user. |
| `users.default_address_id` | One pointer identifies the current default address. |
| `auth_sessions` | Persistent, expiring, revocable sessions owned by users. |
| `refresh_tokens` | Digests of successive refresh tokens, linked to a session. |
| `token_types` and `action_tokens` | Classify and store expiring, one-use email action proofs. |
| `social_accounts` | Associate an external provider subject with one local user. |
| `oauth_states` and `oauth_tickets` | Temporary state for starting and completing social sign-in. |
| `email_outbox` | Encrypted jobs committed before an email worker delivers them. |

`app/infrastructure/models.py` defines these mappings. The composite bridge keys prevent assigning the same role to the same user twice. Social-account uniqueness covers `(provider, provider_subject)` and `(user_id, provider)`.

The default address is not duplicated as a persistent `is_default` flag on every row. API responses calculate that flag by comparing the address ID with `users.default_address_id`.

The account phone and the delivery recipient's phone represent different facts. An address can belong to a user while its recipient is another person; keeping both phone fields is intentional.

Token types are not interchangeable. Access JWTs identify sessions, refresh tokens rotate those sessions, email tokens prove a particular action, OAuth states bind callbacks, and OAuth tickets bridge the provider result back to the initiating browser.

## 7. Registration: from submitted form to queued email

The client sends `POST /api/v1/auth/register` with `name`, `email`, and `password`. `RegisterRequest` validates the fields; shared credential DTOs normalize the email and constrain a new password to 15–128 characters.

`RegisterService.execute` in `app/users/register/service.py` hashes the password before checking whether the email already exists. This also performs the expensive hash work for duplicate registrations rather than introducing an obvious cheap duplicate path.

If the email is new, the service creates an active, unverified `User` and assigns the seeded `customer` role. Public input cannot choose a role. A client-supplied `role` field is rejected by the base DTO configuration.

The service flushes the user, invokes `EmailActionService.queue_email_action(user, "verify_email")`, and commits. That helper invalidates older verification actions, stores a digest of a new random token, and queues its encrypted email job.

The route returns a generic `202 Accepted` message. Existing-email requests receive the same class of public response to reduce account enumeration. A concurrent registration that wins the unique-email constraint is handled through rollback and a recheck.

## 8. Email verification and resending

`POST /api/v1/auth/resend-verification` uses `ResendVerificationService.execute`. It only creates a fresh job for an active, unverified account. Its public response remains generic for unknown or ineligible addresses.

The email link targets the frontend, not a GET endpoint that consumes a proof automatically. The frontend reads the token and explicitly submits confirmation. A fragment-based link avoids placing the original proof in the initial HTTP URL sent to the frontend server.

`EmailActionService.require_action` hashes the supplied token, checks its purpose, locks the owning user and token, and rejects inactive owners, consumed tokens, and expired tokens. It returns the verified user/token pair to the calling use case.

`confirm_email_token` in `app/users/verify_email/confirmation.py` marks the email verified, consumes the selected token, and invalidates other verification tokens for that customer. It leaves transaction completion to its caller.

The original `POST /api/v1/auth/verify-email` returns a confirmation message. The later browser-flow correction adds `POST /api/v1/auth/browser/verify-email` using `VerifyBrowserEmailService.execute`.

That browser operation confirms the email and calls `SessionIssuer.create_session` in one transaction. It returns an access token and public user data while placing the refresh token in an HttpOnly cookie. If session persistence fails, rollback preserves the unused proof.

The session allows the frontend to send the customer to phone/address onboarding instead of asking for email and password again. This is a coordinated frontend/backend behavior, not a redirect decision hidden inside the database.

## 9. Password login

The browser sends `POST /api/v1/auth/browser/login` with `email` and `password`. The underlying `LoginService.execute` is shared with the JSON-token transport at `POST /api/v1/auth/login`.

The service retrieves the normalized email, verifies Argon2id, and uses a dummy hash when an eligible password hash is unavailable. It returns a generic invalid-credentials error for a missing user, inactive account, absent local password, or incorrect password.

After expensive password verification, the service locks and reloads the user. It checks that the stored password hash has not changed during a concurrent password reset. An unverified email causes `email_verification_required` rather than opening a session.

`SessionIssuer.create_session` creates `AuthSession`, flushes it, and calls `issue_token_pair`. Login commits the session and refresh-token digest before returning the result.

`login_browser_customer` in `app/users/browser/login/router.py` writes the refresh cookie and converts the result to `BrowserSessionResponse`. The browser JSON omits the raw refresh token; the JSON-token transport has a different contract for non-browser clients.

## 10. Access JWTs, refresh tokens, and authentication

`Argon2PasswordHasher` and `JwtTokenCodec` live in `app/core/security.py`. Passwords use Argon2id with a random salt provided by the hashing library; plaintext passwords are not stored.

The configured Argon2 parameters are 64 MiB of memory, three iterations, and four lanes. These are deliberate computational costs for password verification, not encryption keys that recover the original password.

Access JWT claims include `sub`, `sid`, `jti`, `type`, `iat`, `nbf`, `exp`, `iss`, and `aud`. `sub` identifies the user and `sid` identifies the persistent session. The default access lifetime is 15 minutes; settings can change it within validated bounds.

`JwtTokenCodec.decode_access` checks the signature using the configured algorithm, issuer, audience, required claims, time constraints, and the `access` token type. A JWT is signed data, not encrypted data; sensitive profile details should not be placed in its payload.

`AccessAuthenticator.authenticate_access` then loads the session and user. A valid signature is insufficient if the session was revoked or expired, belongs to another user, or the account is inactive or unverified.

Refresh tokens are opaque random strings rather than access JWTs. `SessionIssuer.issue_token_pair` returns the raw value once and stores only `hash_token(refresh)` in `refresh_tokens`.

`RefreshSessionService.execute` locks the user, session, and refresh record. It rejects revoked or expired sessions. A successful refresh marks the old token used and issues a new access/refresh pair in the same session.

Reusing an already-used refresh token revokes that session and commits the revocation before returning an error. This preserves replay detection even when request-level error handling performs a rollback later.

The default session lifetime is 30 days. Rotating a refresh token does not silently create an indefinitely extended session; expiry is attached to the persistent session record.

## 11. Browser cookies, CSRF, and logout

`app/users/browser/shared/cookies.py` sets the host-only `foodify_refresh` cookie under `/api/v1/auth/browser`. It is HttpOnly, uses environment-appropriate Secure/SameSite settings, and adds no-store response headers.

HttpOnly prevents application JavaScript from reading the refresh value. It does not replace CSRF protection, because browsers can attach cookies automatically.

`require_browser_client` checks an explicitly allowed Origin and `X-Foodify-Client: web` before cookie-based mutations execute. The CORS allowlist permits the intended frontend origins and required credentials; a wildcard origin is not an identity check.

`POST /api/v1/auth/browser/refresh` reads the refresh cookie and uses the same rotation service. The frontend keeps access credentials in memory and requests a refresh when needed instead of persisting a refresh token in browser storage.

`LogoutService.execute` revokes the session identified by an authenticated access token. The browser logout flow also supports the cookie-based transport and clears the browser cookie. `LogoutAllService.execute` revokes every session belonging to the authenticated user.

Revocation matters immediately because subsequent protected requests consult `auth_sessions`. Merely deleting a frontend variable would leave a still-valid server session alive.

## 12. Forgotten and reset passwords

`POST /api/v1/auth/forgot-password` calls `ForgotPasswordService.execute`. It queues a password-reset action only for an active, verified account with a local password. Social-only accounts recover through their external provider.

The route returns a generic accepted response. The raw reset token appears only inside the encrypted email job and the delivered frontend link, never as a normal API response field.

`POST /api/v1/auth/reset-password` accepts the token and new password. `ResetPasswordService.execute` computes the new password hash before taking sensitive database locks, then requires a valid `password_reset` action.

The operation updates the password hash, consumes the proof, invalidates other reset proofs, revokes all existing sessions, and commits. The customer signs in again with the new password. Reset success does not silently keep old devices authenticated.

Default verification and reset proof lifetimes are 60 and 15 minutes respectively. A new request can invalidate an older action of the same purpose, so users should follow their latest email link.

## 13. Google and Facebook OAuth: the complete route

Social login uses the external provider to prove an identity. Foodify still owns the local customer record, phone, delivery addresses, roles, and session policy.

First, the frontend generates a random `binding_verifier`, keeps it temporarily in the initiating browser origin, and sends its SHA-256 challenge to `POST /api/v1/auth/oauth/{provider}/start`.

`StartOAuthService.execute` generates state, a provider code verifier, and a nonce. It stores a hashed state, provider, temporary verifier/nonce, browser-binding hash, and expiry in `oauth_states`. The gateway returns the provider authorization URL.

The provider redirects to `GET /api/v1/auth/oauth/{provider}/callback`. `OAuthCallbackService.execute` requires the correct provider and an unconsumed, unexpired state. It consumes the state before the external exchange so an authorization code is attempted once.

`HttpOAuthGateway` in `app/infrastructure/oauth.py` exchanges the authorization code. Google validation checks the signed ID token through provider keys, issuer, audience, time claims, nonce, and relevant authorized-party rules.

Google email authority is evaluated rather than treating every provider email as automatically trusted. Facebook exchanges and inspects its access token through the provider, verifies the expected application and identity, and does not treat the supplied email as locally verified by default.

If a known `(provider, subject)` exists, the service loads its active Foodify user. Otherwise it creates a new `customer` account and a `social_accounts` row, provided a valid email is available.

An existing local account with the same email is not automatically merged. The service returns `oauth_account_link_required`; matching email text alone is insufficient proof to attach a new social identity to that account.

If local email confirmation is required, the service queues it and returns the corresponding frontend error state. Otherwise it creates a short-lived, hashed OAuth ticket carrying the user ID and initiating browser binding.

The redirect contains a ticket fragment rather than access/refresh tokens. The frontend submits the ticket and original verifier to `POST /api/v1/auth/browser/oauth/complete`.

`CompleteOAuthService.execute` validates expiry, one-use state, owner, and the constant-time binding comparison, then consumes the ticket and creates a Foodify session. The browser transport writes the refresh cookie and returns access credentials and user data.

Provider client IDs, client secrets, and redirect URIs must be configured together. The redirect URI registered in Google/Meta must match the backend setting exactly, including scheme, host, port, and path. Origin changes such as `localhost` to `127.0.0.1` can also lose a browser's temporary verifier.

## 14. Profile completion

`GET /api/v1/users/me` requires `Authorization: Bearer ACCESS_TOKEN`. `get_current_user` resolves the token through `AccessAuthenticator`; `GetProfileService.execute` returns the current active customer's public profile.

`PATCH /api/v1/users/me` uses `UpdateProfileService.execute` to update explicitly provided `name` and `phone` fields. It cannot change `roles`, `is_active`, or email verification flags through mass assignment.

The shared phone DTO expects E.164 format, for example `+201012345678`. This validates the representation; it does not implement SMS proof of phone ownership.

`user_response` in `app/users/shared/dto/profile.py` returns safe profile fields, deduplicated permissions, roles, and `profile_complete`. That property is true when the user has an account phone and a default delivery address.

Local-password and social-login customers use the same completion rule. The frontend reads the returned profile to choose profile onboarding, address onboarding, or the main application.

## 15. Delivery addresses and ownership

`GET /api/v1/users/me/addresses` lists the authenticated user's addresses. `POST` on the same path creates one through `AddAddressService.execute` in `app/users/addresses/add_address/service.py`.

Address input includes a label, recipient name, recipient phone, country, city, area, street, building, and optional delivery details. Coordinates are optional as a pair and constrained to valid latitude/longitude ranges.

Creation locks the user row, enforces the limit of 20 addresses, inserts and flushes the new row, and selects it as default if the user has no default address. The lock serializes concurrent address/default changes.

`PUT /api/v1/users/me/addresses/{id}` replaces an owned address using its operation-specific DTO and service. It is a full update contract; it should not be described as arbitrary partial profile editing.

`PUT /api/v1/users/me/default-address/{id}` calls `SetDefaultAddressService.execute`. It requires that the address belongs to the active user, changes the single default pointer, and returns the updated profile.

`DELETE /api/v1/users/me/addresses/{id}` calls `DeleteAddressService.execute`. When deleting the default, it moves the pointer to the oldest remaining address or clears it, flushes that change, then removes the old target and commits.

`require_owned_address` scopes lookups to the authenticated owner. A missing address and another user's address both produce `404`, reducing information disclosure and preventing ID-based access to another customer's delivery details.

## 16. Roles and authorization

`app/roles/enums.py` defines `RoleType`; `app/roles/definitions.py` defines role names and permission assignments. The roles are `customer`, `courier`, `order_preparer`, `operations_manager`, and `admin`.

`operations_manager` is the role below administrator for operational responsibilities. It does not automatically receive every administrative permission. The bridges allow one user to hold multiple roles without duplicating user records.

`require_permission` in `app/dependencies.py` checks the loaded user's roles and permissions. Authentication proves a user/session; authorization determines whether that identity may perform an operation.

Sprint 1 exposes customer self-service, not public staff creation or public role assignment. Seeded permission vocabulary for later features does not mean those features already have endpoints.

## 17. Email outbox: commit first, send separately

`OutboxEmailSender.send_action_email` in `app/infrastructure/outbox.py` serializes recipient, purpose, proof, and expiry, encrypts the payload with Fernet, and adds `EmailOutbox` through the same transaction as the account change.

`deliver_next_email` in `app/worker.py` claims a due job with row locking and `SKIP LOCKED`, decrypts it, checks its expiry, and delegates to `create_email_sender`. The configured adapter constructs the frontend link and performs actual delivery.

Success, or discarding an expired job, marks it complete and clears the encrypted payload. Transient delivery failures increase the attempt count and schedule exponential backoff capped at one hour. Ten failed attempts require operator attention.

A `202` from registration means accepted and committed, not that an email arrived in the inbox. SMTP configuration, sender verification, provider limits, spam filtering, worker health, and job expiry can affect delivery.

Development uses Mailpit for inspecting local messages. Production can run a separate worker; the repository also has an explicitly configured embedded-worker adapter for a hosted process. These are deployment choices around the same outbox logic.

## 18. Error handling and defensive boundaries

`APIModel` in `app/shared/dto.py` sets `extra="forbid"`. Unexpected fields are rejected instead of copied onto database entities. Response DTOs also keep internal hashes, cookies, and provider secrets out of public JSON.

Application failures use `AppError` with a stable code, safe message, status, and optional details. Central handlers return an envelope containing `error.code`, `message`, `details`, and `request_id`.

Typical statuses are `401` for invalid authentication, `403` for forbidden behavior, `404` for an unavailable owned resource, `409` for a conflict, `422` for invalid input, `429` for a limit, and `503` for a required unavailable dependency.

`RedisRateLimiter` uses a Lua increment/expiry operation for atomic shared limits. Identifiers in Redis keys are hashed. If Redis is unavailable, protected rate-limit checks fail closed rather than silently disabling protection.

`SecurityMiddleware` limits request bodies, creates or validates a request ID, and applies security/no-store headers. Trusted-host checks and explicitly trusted proxy settings restrict host/IP assumptions. Sensitive query values and request bodies must not be logged indiscriminately.

These measures address concrete OWASP-related risks, including broken access control, injection exposure, authentication abuse, and misconfiguration. They are implemented controls, not a claim of certification or a complete external penetration test.

## 19. Development, test, and production operation

`APP_ENV` selects `.env.development`, `.env.test`, or `.env.production`. Each environment needs separate database/Redis configuration and secrets. Real `.env` files are excluded from version control; templates explain the variables.

`run.py` configures Uvicorn and validates supported runtime options. Reload belongs to development. Running the server does not itself create tables, seed users, or silently apply schema changes.

The setup sequence is: provision MySQL/Redis/email service → run `alembic upgrade head` → run the role/token-type seed → start API and email worker. `python -m scripts.seed` is repeatable and does not create an administrator with a default password.

The development Compose setup includes MySQL, Redis, Mailpit, API, and email worker. After changing environment values, recreate the affected API/worker containers; a simple restart does not replace their original environment.

`FRONTEND_URL` controls links built for newly sent confirmation/reset emails. The worker must receive the updated value too. Existing delivered emails retain the old URL, so users should request a fresh message after changing it.

Production additionally needs HTTPS, verified database/Redis TLS where required, safe secret storage, correct CORS and OAuth callback settings, backups, and worker/outbox monitoring. `/health/live` reports process liveness; `/health/ready` checks required backing services.

## 20. File map and handoff to Sprint 2

| Where to look | What to explain or change |
| --- | --- |
| `app/users/<operation>/` | HTTP contract, dependency assembly, and the operation's `execute` method. |
| `app/users/shared/` | Repositories, account contracts, email actions, session issuance, and authentication. |
| `app/core/` | Settings, password/JWT adapters, HTTP hardening, and trusted origin/IP rules. |
| `app/infrastructure/` | SQLAlchemy models/UoW, OAuth network adapter, Redis, email/outbox. |
| `app/roles/` | Enumerated roles and normalized permission definitions. |
| `migrations/` and `scripts/seed.py` | Versioned schema and repeatable lookup-data setup. |
| `app/worker.py` and `run.py` | Email delivery loop and API runtime entry point. |

The output of Sprint 1 is a verified identity with revocable sessions, controlled roles, a validated profile, and owned delivery addresses. Sprint 2 takes that authenticated user ID into cart ownership, address selection at checkout, order history, and payment ownership checks.

For a presentation, follow one customer from registration to verification, login, profile, and address. Then show how a protected request resolves JWT → session → active user. That trace connects the architecture, database, security rules, and API responses to one understandable journey.
