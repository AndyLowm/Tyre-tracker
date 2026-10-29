# Tyre Tracker

Tyre tracking API, track tyre stocks across multiple locations via size and spec. Keeps a weighted cost price every time tyre stocks are added.

**Status** Work in progress

## Why I built it
I'm a vehicle mechanic moving into software. Mobile fitters often keep
stock in their head believe it or not!, so I wanted to build something
that helps.

## Features
- Add tyres and stock across named locations
- Weighted-average cost price recalculated when new stock arrives
- Move stock between locations; remove stock with validation
- Search by make, model and size
- Multi-account: each account only sees its own stock and prices
- JWT cookie auth with Argon2 password hashing
- Failed login attempts are logged

## Tech
FastAPI, SQLModel, Pydantic, PyJWT, pwdlib (Argon2), Jinja2, uv.
SQLite for local development; PostgreSQL (Supabase) planned.
  
## Setup
Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

1. `cp .env.example .env`
2. Set `JWT_KEY` in `.env` (generate one with
   `python -c "import secrets; print(secrets.token_hex(32))"`)
3. `uv sync`
4. `uv run fastapi dev`

Interactive API docs are at `/docs` on the address shown in the terminal.

## Tests
Needs `.env` set up as above. Tests run against an in-memory SQLite database.

```bash
uv run pytest -v
```

## Design decisions
- Service layer separate from routes; routes own the commit
- Row locks (`SELECT ... FOR UPDATE`) on stock changes to prevent two
  requests changing the same stock at once (no effect on SQLite, so
  this matters once I move to Postgres)
- Input normalisation, so "Michelin " and "michelin" are one tyre
- Generic auth error messages and a dummy hash check, so login timing
  doesn't reveal which usernames exist

## Roadmap
- [ ] More tests (move stock, add tyre, search, account isolation, auth)
- [ ] htmx front end
- [ ] Postgres (Supabase), database constraints and migrations (Alembic)
- [ ] Deployment
- [ ] Rate limiting on login