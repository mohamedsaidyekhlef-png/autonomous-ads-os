# Release readiness — Shadow Beta

## Release gates

- [x] Redis durable queue and independently deployable worker.
- [x] Command API responds 202 with a persisted run URL.
- [x] Worker-only LLM execution, schema validation, idempotent final states, decisions, and draft records.
- [x] Shadow mode and DRY_RUN are hard requirements; no automatic spending path exists.
- [x] Organization-scoped records, production Whop entitlement deny-by-default, verified idempotent membership webhooks.
- [x] Railway API/worker deployment, Vercel dashboard configuration, Dockerfiles, CI, migrations, and production CORS controls.

## Before commercial launch

- Configure production Postgres/Redis backups, retention, TLS, and alerting.
- Add the real dashboard authentication provider which forwards verified Whop user identity.
- Register the Whop webhook secret and validate its exact signature delivery format in a staging account.
- Configure a hosted LLM provider or provision Ollama capacity, then load-test the worker.
- Add platform OAuth credentials only for integrations that are explicitly released; leave all others Coming soon.
- Set `APP_ENV=production`, a long random `APP_SECRET_KEY`, an actual Fernet `TOKEN_ENCRYPTION_KEY`, CORS allowlist, and `WHOP_REQUIRED_PRODUCT_ID`.

No live platform mutation, spending, or autonomous activation is supported in this release.
