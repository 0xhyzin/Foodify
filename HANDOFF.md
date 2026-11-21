# Foodify — Agent Handoff

Checked **2026-11-21**. Project root is `/home/hyzin/Projects/Foodify`; the configured `foodify-api` working directory is absent here. React/Vite frontend + FastAPI modular monolith + MySQL food-delivery app.

## Architecture and key paths

- Frontend feature Clean Architecture: `front/src/features/{auth,account,catalog,marketplace}/{presentation,application,domain,infrastructure}`. Composition/injection: `front/src/app/services.ts`; HTTP/session: `front/src/infrastructure/http/fetch-client.ts`; email/OAuth links: `front/src/app/bootstrap/external-links.ts`.
- Backend composition root: `back/app/main.py`. Feature modules split routers, DTOs, services, repositories/dependencies. Sprint 2: `back/app/{cart,checkout/submit_order,orders,restaurants,payments}/`; shared ports/errors/security in `back/app/{shared,core,ordering}/`.
- SQLAlchemy models: `back/app/ordering/models.py`, `back/app/infrastructure/`; Alembic: `back/migrations/`. Demo catalog seed: `back/app/ordering/data/demo-catalog.json` → MySQL. Valkey is used for shared rate limits.
- Vercel API proxy: `api/proxy.mjs`; routing/headers: `vercel.json`. Tests: `back/tests/`, `front/tests/`, root `tests/`; Postman: `back/postman/`.
- Integration references: `docs/SPRINT_2_INTEGRATION.md`, `front/docs/INTEGRATION.md`; verification/limits: `docs/SPRINT_2_VERIFICATION.md`; deploy guide: `docs/SPRINT_2_DEPLOYMENT.md`.

Flow: React page → use case → repository interface/HTTP adapter → `FetchHttpClient` → FastAPI → MySQL/provider. Local API base is `http://127.0.0.1:8000/api/v1`; production uses Vercel same-origin proxy → FastAPI Cloud. Hosting roles: Vercel frontend/proxy, FastAPI Cloud API, Aiven MySQL/Valkey, Mailjet email, Paymob hosted payments. Live provider configuration was not revalidated.

## Decisions and strict constraints

- Preserve feature boundaries/DI; no `fetch` or business logic in pages, and no provider secrets or card data in the frontend.
- Cart identity is `(user_id, restaurant_id)`; each order belongs to one merchant. Never clear other merchants’ carts.
- Backend is authoritative for ownership, permissions, prices/totals, cart revision, order/payment state, and verified callbacks. Never trust client role/total/success flags.
- Preserve checkout lock → recheck → snapshots/order/payment/tracking in one transaction. Same idempotency key + same fingerprint replays; changed payload returns `409 idempotency_key_reused`.
- Keep Paymob hosted card entry, HTTPS destination validation, HMAC callback verification, deduplication, stable safe error codes/request IDs, CORS/proxy allowlists, and rate limits.
- Access token stays in memory; refresh token is HttpOnly. OAuth verifier is tab/origin-bound and one-use. Never expose `.env*`, tokens, SQL/provider details in Git, logs, docs, screenshots, or chat.
- Do not `git clean`, reset, or overwrite: preserve and inspect all dirty/untracked work.

## Completed vs. pending

Sprint 2 implementation/documentation covers MySQL-backed marketplace/catalog, per-merchant carts, address/checkout validation, orders/history/tracking/restaurant operations, Paymob payment flow, idempotency/security, Postman, and frontend/backend integration.

Follow-up changes are present locally for Paymob validation/transfer review, email confirmation session and OAuth deep-link/session races, payment/checkout UI, Postman, tests, CI, and docs. They are **uncommitted and not confirmed deployed**. `main` and `origin/main` were at `245afbf`; 48 tracked files were modified plus many untracked files. Review before changing or packaging them.

## Latest checks and blockers

Run on this worktree **2026-11-21**:

- `cd back && .venv/bin/python -m pytest -q`: **172 passed**, 0 failed (50.15 s).
- `npm test`: **71 passed** (54 frontend + 12 proxy + 5 Postman), 0 failed/skipped.
- `npm run typecheck` and `npm run build`: passed.
- Non-failing test warning: `WebSocket server error: Port 24678 is already in use`; test exit code was 0. `ss` showed no listener afterward.

No automated test failures are known. Live checks are blocked: API probe returned `curl: (7) Failed to connect to 127.0.0.1 port 8000` (HTTP `000`); `docker ps` returned `permission denied while trying to connect to the Docker API at unix:///var/run/docker.sock`. Tests use isolated/in-memory DB and provider substitutes; they do not verify live MySQL locks/migrations, OAuth consent, email delivery, Paymob callbacks, or deployment.

## Agent tools and skills

- Graphify CLI/skill is installed; existing indexes: `graphify-out/{back,front}/graphify-out/graph.json`. This handoff queried both. Index locally/code-only; do not include `.env*` or send source to an external backend. Example:
  ```bash
  GRAPHIFY_BACKEND=none graphify extract back/app --code-only --no-cluster --no-dedup --out graphify-out/back
  graphify query 'CheckoutService lock_cart' --graph graphify-out/back/graphify-out/graph.json --budget 600
  ```
- RTK **1.1.0** is configured for Codex (`~/.codex/RTK.md`, global hook); use `rtk` for supported shell commands. Project notes document installed agent skills: `frontend-design`, `web-design-guidelines`, `vercel-react-best-practices`, `playwright-cli`, `graphify`. Playwright is for manual browser inspection; automated tests use Node’s built-in runner/pytest. PDF deliverables used `pdf:pdf`; the Sites connector published a separate design visualization—neither is needed for API integration.
- For an OpenCode environment missing the requested tools, bootstrap (agent tooling only, not app dependencies):
  ```bash
  npx skills add anthropics/skills --skill frontend-design -a opencode
  npx skills add vercel-labs/agent-skills --skill web-design-guidelines -a opencode
  npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices -a opencode
  npm install -g @playwright/cli@latest
  npx skills add microsoft/playwright-cli --skill playwright-cli -a opencode
  curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | RTK_EDITION=oss sh
  rtk --version && rtk init --global --opencode --dry-run && rtk init --global --opencode
  ```

## Next steps

1. Preserve and review tracked diffs and untracked files; exclude unrelated generated artifacts.
2. Restore Docker access, start MySQL/Valkey/Mailpit/API per `docs/SPRINT_2_DEPLOYMENT.md`, run migrations and seed, then confirm API health/OpenAPI.
3. Smoke-test confirmation/login → catalog → two merchant carts → checkout/idempotent retry → Paymob sandbox callback → order history/tracking/operations.
4. Separately verify deployed Vercel/FastAPI Cloud/Aiven/Mailjet/OAuth/Paymob settings; keep credentials in ignored local env or provider secret stores.
5. Record fresh live-smoke results in `docs/SPRINT_2_VERIFICATION.md`; distinguish local automated results from external-provider/deployment checks.
