# FastAPI Login System

A small, self-contained authentication boilerplate for FastAPI: register with
email + password, verify via a one-time code (OTP), log in, and access a
protected route with a JWT bearer token.

## Status: OTP email sending is **not implemented**

The whole register → verify flow works end-to-end, but the step that would
actually email the OTP to the user is stubbed out in
[`app/routers/sendmail.py`](app/routers/sendmail.py) — it just prints the
code to your console instead of sending it. This is on purpose, so you can
drop in whatever provider you want (SMTP, SendGrid, SES, Postmark, etc.)
without fighting existing wiring. See that file for where to plug it in.

## Features

- `POST /register` — create a pending signup and generate a 6-digit OTP (rate-limited to 3/minute per IP)
- `POST /verify-otp` — confirm the OTP and create the user, returns a JWT
- `POST /login` — email + password login, returns a JWT
- `GET /me` — example protected route, requires `Authorization: Bearer <token>`
- Passwords hashed with bcrypt
- OTPs expire after 5 minutes and lock out after 5 wrong attempts
- SQLite by default, swap in Postgres/MySQL/etc. with one env var

## Setup

```bash
git clone <this-repo>
cd fastapi-login-system
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste the output into SECRET_KEY in .env

uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API docs.

## Trying it out

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
```

## Project layout

```
app/
  main.py          # FastAPI app, CORS, rate-limit handler, router wiring
  database.py       SQLAlchemy engine/session (SQLite by default)
  models.py          User and EmailOtp tables
  security.py         bcrypt hashing + JWT create/decode
  routers/
    auth.py            /register /verify-otp /login /me
    sendmail.py         OTP email — STUBBED, see "Status" above
```

## Wiring up real email

Edit `app/routers/sendmail.py` and replace the `print(...)` with a real call
to your provider. Keep the function signature (`send_email(email, otp)`) and
make sure it **raises** on failure — `/register` relies on that to roll back
the OTP row if sending fails.

## Config (`.env`)

| Variable | Required | Default | Notes |
|---|---|---|---|
| `SECRET_KEY` | yes | — | JWT signing key. Generate with `secrets.token_hex(32)`. |
| `DATABASE_URL` | no | `sqlite:///./app.db` | Any SQLAlchemy-compatible URL. |
| `TOKEN_EXPIRE_DAYS` | no | `7` | JWT lifetime. |

## Known limitations / things to add before production

- No token refresh or revocation — a JWT is valid until it expires, with no way to invalidate it early (e.g. on logout or password change).
- No password-reset flow.
- `CORSMiddleware` is wide open (`allow_origins=["*"]`) — tighten this before deploying publicly.
- No tests included yet.

## License

MIT — do whatever you want with it.
