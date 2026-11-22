# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

- Setup: `cp .env.example .env`, set `JWT_KEY` (`python3 -c "import secrets; print(secrets.token_hex(32))"`), then `uv sync`
- Run dev server: `uv run fastapi dev` (entrypoint `app.main:app`; docs at `/docs`)
- All tests: `uv run pytest -v`
- Single test: `uv run pytest tests/test_add_stock.py::test_name -v`

Tailwind (v4, standalone CLI via `pytailwindcss`, no Node). Source is `app/static/css/input.css`; `output.css` is gitignored and must be built:
- Dev (run alongside the server): `uv run tailwindcss -i app/static/css/input.css -o app/static/css/output.css --watch`
- Production: same command with `--minify`
- If the first run fails with `CERTIFICATE_VERIFY_FAILED` while downloading the binary, prefix with `SSL_CERT_FILE=/etc/ssl/cert.pem`.

`Settings` (`app/dependencies/config.py`) requires `DATABASE_URL`, `JWT_KEY` and `JWT_ALGO` in `.env` at import time, so tests also need `.env`. No linter is configured.

## Architecture

FastAPI + SQLModel API for tracking tyre stock across named locations, multi-account. SQLite for dev; Postgres (Supabase) planned. There is a small Jinja2/htmx front end (`routers/views.py`, `app/templates`), which is hidden from the OpenAPI schema.

Layering: `routers/` → `services/` → `models/` (schemas in `schemas/`).

- **Routes own the transaction.** Service functions only `session.add`/`flush`; routers call `session.commit()` after the service succeeds. Don't commit inside services.
- **Custom exceptions** (`app/exceptions.py`, base `TyreTrackerError`: `TyreNotFoundError`, `StockError`, `LocationError`) are raised by services and caught in routers, which translate them to HTTP responses.
- **Data model** (`app/models/tyre.py`): `Tyre` is global (shared across accounts, identified by make/model/width/aspect_ratio/rim/speed_rating). Per-account data lives in `StockLocation` (unique on tyre_id + acc_id + location_name, `amount >= 0` check) and `AccountPrices` (per-account weighted-average cost price). Every query on stock or prices must filter by `acc_id` to keep accounts isolated.
- **Service "master" functions** in `services/tyre_service.py` (`add_tyre_master`, `add_tyre_stock_master`, `remove_stock_master`, `move_stock`) orchestrate the flows. Adding stock updates location rows (returning old/new totals) and then recomputes the weighted cost price from those totals. Cost prices use `Decimal` with `ROUND_HALF_UP`.
- **Row locking**: stock changes use `SELECT ... FOR UPDATE` (`with_for_update()`), which does nothing on SQLite and matters on Postgres.
- **Input normalisation**: strings such as make/model are normalised (`services/utils.py::normalise_string`) so "Michelin " and "michelin" are the same tyre.
- **Auth**: JWT in a cookie (`jwt_service`, `dependencies/auth_flow.py`), Argon2 hashing via pwdlib. Login errors are deliberately generic and use a dummy hash check to avoid leaking which usernames exist. Failed logins are logged to `app_security_log.txt`.
- DB tables are created at startup via `SQLModel.metadata.create_all` in the lifespan hook. There are no migrations yet (Alembic is planned).

## Testing

`tests/conftest.py` builds an in-memory SQLite engine (`StaticPool`) per test and overrides the `get_session` and `get_acc_id` dependencies, so tests run as account id 1 with no auth. The `tyre` fixture creates a michelin pilot with 1 in `unit` and 4 in `van`.
