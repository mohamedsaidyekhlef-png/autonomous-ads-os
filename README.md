# Autonomous Ads OS — Shadow Beta

Shadow Beta is a sellable multi-tenant advertising intelligence workspace. It is permanently DRY_RUN and shadow-only: it produces analysis, decisions, and campaign drafts, but never spends money or claims a live platform action occurred.

## Local development

1. Copy `.env.example` into your deployment secret manager or export those variables; the app intentionally does not load local `.env` files.
2. Start Postgres and Redis with `docker compose up -d`.
3. Run `uv run alembic upgrade head`.
4. Run API: `uv run uvicorn app.main:app --reload --port 8080`.
5. Run worker separately: `uv run python -m app.worker`.
6. Run dashboard: `npm --prefix dashboard run dev`.

Commands return `202 Accepted` immediately. The Redis-backed worker claims queued runs idempotently, validates structured LLM output, and persists results, decisions, and draft campaigns.

## LLM configuration

- Local development: `LLM_PROVIDER=ollama`, with Ollama running locally.
- Hosted: `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`. The endpoint must support Chat Completions JSON Schema response format.

## Access and Whop

Production API calls require `X-Organization-ID` and verified `X-Whop-User-ID`; membership is deny-by-default. Configure Whop to POST signed HMAC-SHA256 requests to `/v1/webhooks/whop`, including `X-Whop-Signature` and a stable `X-Whop-Event-ID`. Deliveries are idempotent and activate, cancel, or expire memberships.

## Deployment

Deploy API and worker as separate Railway services using `railway.toml` and `railway.worker.toml`; provision Railway Postgres and Redis and inject secrets. Deploy `dashboard/` to Vercel using its `vercel.json`, with `NEXT_PUBLIC_API_URL` set to the API URL and API `CORS_ORIGINS` containing the Vercel domain.
