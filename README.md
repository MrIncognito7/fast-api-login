# FastAPI Login System

A small, self-contained authentication boilerplate for FastAPI: register with
email + password, verify via a one-time code (OTP), log in, and access a
protected route with a JWT bearer token.

## Status: OTP email sending is **not implemented**

The whole register -> verify flow works end-to-end, but the step that would
actually email the OTP to the user is stubbed out in
[`app/routers/sendmail.py`](app/routers/sendmail.py) — it just prints the
code to your console (and keeps it in memory, see `get_last_otp`) instead of
sending it. This is on purpose, so you can drop in whatever provider you
want (SMTP, SendGrid, SES, Postmark, etc.) without fighting existing wiring.
See that file for where to plug it in.

## Features

- `POST /register` — create a pending signup and generate a 6-digit OTP (rate-limited to 3/minute per IP)
- `POST /resend-otp` — reissue the OTP if the original expired or never arrived
- `POST /verify-otp` — confirm the OTP and create the user, returns a JWT
- `POST /login` — email + password login, returns a JWT
- `GET /me` — example protected route, requires `Authorization: Bearer <token>`
- `POST /logout` — placeholder (this API is stateless JWT auth — see Limitations)
- Passwords hashed with bcrypt
- OTPs expire after 5 minutes and lock out after 5 wrong attempts
- Centralized config via `pydantic-settings` (`app/config.py`)
- SQLite by default, swap in Postgres/MySQL/etc. with one env var
- Test suite (pytest) covering the full auth flow
- Dockerfile + docker-compose (app + Postgres)
- GitHub Actions CI running tests on push/PR

## Quickstart (local, no Docker)

```bash
git clone <this-repo>
cd fastapi-login-system
python3 -m venv .venv && source .venv/bin/activate
make install        # or: pip install -r requirements.txt

cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste into SECRET_KEY in .env

make run             # or: uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Quickstart (Docker)

Runs the API against Postgres instead of SQLite.

```bash
cp .env.example .env   # set SECRET_KEY
export $(grep -v '^#' .env | xargs)   # or use `docker compose --env-file .env`
make docker-up          # or: docker compose up --build
```

API comes up on `http://localhost:8000`. `make docker-down` tears it down
(including the Postgres volume).

> Note: the Dockerfile/compose setup follows standard patterns but hasn't
> been run against a live Docker daemon while generating this project —
> sanity-check it in your own environment before relying on it.

## Running tests

```bash
make test            # or: pytest -q
```

The test suite spins up a fresh SQLite DB per test and reads OTPs back via
`get_last_otp()` in the sendmail stub, so it doesn't depend on a real email
provider.

## Trying it out manually

```bash
# 1. Register — OTP is printed in the server console, not emailed
curl -X POST localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada","email":"ada@example.com","password":"supersecret1"}'

# 2. Verify with the OTP from the console output
curl -X POST localhost:8000/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"name":"Ada","email":"ada@example.com","password":"supersecret1","otp":"123456"}'
# -> returns { "access_token": "...", "user": {...} }

# 3. Log in anytime after that
curl -X POST localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com","password":"supersecret1"}'

# 4. Hit a protected route
curl localhost:8000/me -H "Authorization: Bearer <access_token>"

# Didn't get the OTP in time? Reissue one:
curl -X POST localhost:8000/resend-otp \
  -H "Content-Type: application/json" \
  -d '{"email":"ada@example.com"}'
```

## Project layout

```
app/
  main.py          # FastAPI app, CORS, rate-limit handler, router wiring
  config.py          Centralized settings (pydantic-settings)
  database.py         SQLAlchemy engine/session
  models.py             User and EmailOtp tables
  security.py              bcrypt hashing + JWT create/decode
  routers/
    auth.py                  /register /resend-otp /verify-otp /login /me /logout
    sendmail.py                 OTP email — STUBBED, see "Status" above
tests/
  conftest.py        Isolated DB + rate-limiter reset per test
  test_auth.py         Full-flow tests
.github/workflows/ci.yml   Runs pytest on push/PR
Dockerfile, docker-compose.yml, Makefile
```

## Wiring up real email

Edit `app/routers/sendmail.py` and replace the body of `send_email` with a
real call to your provider. Keep the function signature
(`send_email(email, otp)`) and make sure it **raises** on failure —
`/register` and `/resend-otp` rely on that to roll back the OTP row if
sending fails. You can remove `_sent_otps`/`get_last_otp` once you no longer
need the dev/test shortcut.

## Config (`.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `SECRET_KEY` | yes | — | JWT signing key. Generate with `secrets.token_hex(32)`. |
| `DATABASE_URL` | no | `sqlite:///./app.db` | Any SQLAlchemy-compatible URL. |
| `TOKEN_EXPIRE_DAYS` | no | `7` | JWT lifetime. |
| `CORS_ORIGINS` | no | `*` | Comma-separated allowed origins, or `*` for dev. |

## Known limitations / things to add before production

- No token refresh or revocation — a JWT is valid until it expires, with no way to invalidate it early (e.g. on logout or password change). `/logout` is currently just a placeholder for this reason.
- No password-reset flow (though it'd follow the same OTP pattern already used for signup).
- `CORS_ORIGINS` defaults to `*` — set it explicitly before deploying publicly.
- `Base.metadata.create_all()` only creates tables on first run — it won't handle future schema changes. Add Alembic if you need migrations.
- Sync SQLAlchemy under an async app is fine at low traffic but will bottleneck under load; consider `asyncpg`/`aiosqlite` + async sessions if that matters for you.

## License

MIT — do whatever you want with it.
