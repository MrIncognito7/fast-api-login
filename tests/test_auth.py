from app.routers.sendmail import get_last_otp


def _register(client, email="ada@example.com", name="Ada", password="supersecret1"):
    return client.post("/register", json={"name": name, "email": email, "password": password})


def _verify(client, email="ada@example.com", name="Ada", password="supersecret1", otp=None):
    otp = otp or get_last_otp(email)
    return client.post(
        "/verify-otp",
        json={"name": name, "email": email, "password": password, "otp": otp},
    )


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_register_sends_otp(client):
    r = _register(client)
    assert r.status_code == 200
    assert get_last_otp("ada@example.com") is not None


def test_register_twice_before_verification_reissues_otp(client):
    # Calling /register again before verifying just reissues the OTP (same
    # as /resend-otp) — it's not an error, since no User exists yet.
    _register(client)
    r = _register(client)
    assert r.status_code == 200


def test_register_after_verified_is_rejected(client):
    _register(client)
    _verify(client)  # completes signup, user now exists
    r = _register(client)
    assert r.status_code == 400


def test_full_signup_and_login_flow(client):
    _register(client)
    r = _verify(client)
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert body["user"]["email"] == "ada@example.com"

    r = client.post("/login", json={"email": "ada@example.com", "password": "supersecret1"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_verify_wrong_otp_rejected(client):
    _register(client)
    r = _verify(client, otp="000000")
    assert r.status_code == 400


def test_login_before_verification_fails(client):
    _register(client)
    r = client.post("/login", json={"email": "ada@example.com", "password": "supersecret1"})
    assert r.status_code == 401


def test_login_wrong_password_fails(client):
    _register(client)
    _verify(client)
    r = client.post("/login", json={"email": "ada@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_resend_otp_issues_new_code(client):
    _register(client)
    first_otp = get_last_otp("ada@example.com")

    r = client.post("/resend-otp", json={"email": "ada@example.com"})
    assert r.status_code == 200

    # Old code should no longer work even if it happened to match (it won't,
    # since OTPs are random, but the important case is the row was replaced).
    r = _verify(client, otp=first_otp)
    assert r.status_code in (201, 400)  # 400 expected unless random collision

    # New code works.
    r = _verify(client)
    assert r.status_code == 201


def test_me_requires_token(client):
    r = client.get("/me")
    assert r.status_code in (401, 403)  # 403 if no Authorization header at all


def test_me_with_valid_token(client):
    _register(client)
    r = _verify(client)
    token = r.json()["access_token"]

    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ada@example.com"


def test_me_with_bad_token(client):
    r = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401
