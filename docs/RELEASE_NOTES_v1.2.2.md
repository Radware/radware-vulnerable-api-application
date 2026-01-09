# Release Notes - v1.2.2

This release expands the vulnerable API demo surface, tightens deployment guidance, and refreshes documentation to align with the official container image. These notes can be used directly in the GitHub release description.

## Highlights

- **SQL Injection demos (new):** Added intentional SQL injection behavior for:
  - `GET /api/products/search?name=...` (search injection)
  - `POST /api/users/{userId}/orders/{orderId}/apply-coupon?coupon_code=...` (coupon lookup injection)
- **Postgres-specific payload support:** Time-based and Postgres-specific payloads (e.g., `pg_sleep`, `ILIKE`) require **PostgreSQL mode** (`docker-compose.rva-db.yml`) or `DB_MODE=external` with a PostgreSQL `DB_URL`. SQLite and in-memory modes execute read-only queries but do not support Postgres-only payloads.
- **Legacy + B2B demo coverage:** Maintains legacy endpoints and the unauthenticated B2B partner lookup endpoint that returns internal pricing snapshots for demonstration purposes.
- **Flow catalog expansions:** New legit and attack flows cover legacy endpoints, B2B pricing scraping behavior, and sequence-violation scenarios for BLA demonstrations.
- **Deployment defaults updated:** Compose files now default to the official image `razor29/rva:latest` (override with `RVA_IMAGE` if needed).

## Deployment Notes

1. **Recommended demo mode for SQLi:** Use PostgreSQL mode with `docker-compose -f docker-compose.rva-db.yml up -d`, or set `DB_MODE=external` with a PostgreSQL `DB_URL`.
2. **Image source:** The official published image is `razor29/rva:latest`. Custom tags are supported via `RVA_IMAGE`.
3. **Protected Entity Mode:** Protected demo users and products remain non-destructible while keeping non-protected entities fully exploitable.

## Quick Links

- Deployment guide: `DEPLOYMENT.md`
- Protected entities: `PROTECTED_ENTITIES.md`
- OpenAPI schema: `openapi.yaml`
