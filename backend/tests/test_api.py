import os
from uuid import uuid4

from app.main import DEMO_STARTING_BALANCES, RATES


def unique_email() -> str:
    return f"test-{uuid4().hex[:12]}@example.com"


def register(client, password="a-very-strong-password", full_name="Test User"):
    email = unique_email()
    response = client.post("/v1/auth/register", json={"email": email, "password": password, "full_name": full_name})
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return email, password, token


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_me(client):
    email, password, token = register(client)

    login = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    login_token = login.json()["access_token"]

    me = client.get("/v1/auth/me", headers=auth_headers(login_token))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == email
    assert body["role"] == "customer"


def test_duplicate_email_rejected(client):
    email, password, _ = register(client)
    response = client.post("/v1/auth/register", json={"email": email, "password": password, "full_name": "Again"})
    assert response.status_code == 409


def test_login_wrong_password_rejected(client):
    email, _, _ = register(client)
    response = client.post("/v1/auth/login", json={"email": email, "password": "totally-wrong-password"})
    assert response.status_code == 401


def test_unauthenticated_requests_rejected(client):
    assert client.get("/v1/auth/me").status_code == 401
    assert client.get("/v1/swaps").status_code == 401
    assert client.get("/v1/balances").status_code == 401


def test_quote_math_matches_rates(client):
    response = client.post("/v1/quotes", json={"from_asset": "USDT", "to_asset": "BTC", "amount": 1000})
    assert response.status_code == 200
    body = response.json()
    expected_rate = RATES["USDT"] / RATES["BTC"]
    expected_gross = 1000 * RATES["USDT"] / RATES["BTC"]
    expected_fee = expected_gross * 0.0025
    assert body["rate"] == expected_rate
    assert abs(body["fee"] - expected_fee) < 1e-9
    assert abs(body["received"] - (expected_gross - expected_fee)) < 1e-9


def test_quote_same_asset_rejected(client):
    response = client.post("/v1/quotes", json={"from_asset": "BTC", "to_asset": "BTC", "amount": 1})
    assert response.status_code == 422


def test_balances_seeded_with_demo_defaults(client):
    _, _, token = register(client)
    response = client.get("/v1/balances", headers=auth_headers(token))
    assert response.status_code == 200
    balances = {row["asset"]: row["amount"] for row in response.json()}
    assert balances == DEMO_STARTING_BALANCES


def test_swap_success_debits_and_credits_balances(client):
    _, _, token = register(client)
    headers = auth_headers(token)

    quote = client.post("/v1/quotes", json={"from_asset": "USDT", "to_asset": "BTC", "amount": 1000}).json()
    swap = client.post("/v1/swaps", headers=headers, json={
        "from_asset": "USDT", "to_asset": "BTC", "amount": 1000, "expected_received": quote["received"],
    })
    assert swap.status_code == 201, swap.text
    body = swap.json()
    assert body["status"] == "completed"
    assert body["from_asset"] == "USDT" and body["to_asset"] == "BTC"

    balances = {row["asset"]: row["amount"] for row in client.get("/v1/balances", headers=headers).json()}
    assert balances["USDT"] == DEMO_STARTING_BALANCES["USDT"] - 1000
    assert abs(balances["BTC"] - (DEMO_STARTING_BALANCES["BTC"] + quote["received"])) < 1e-8

    history = client.get("/v1/swaps", headers=headers).json()
    assert len(history) == 1
    assert history[0]["reference"] == body["reference"]


def test_swap_insufficient_balance_rejected(client):
    _, _, token = register(client)
    headers = auth_headers(token)

    quote = client.post("/v1/quotes", json={"from_asset": "BTC", "to_asset": "USDT", "amount": 999}).json()
    swap = client.post("/v1/swaps", headers=headers, json={
        "from_asset": "BTC", "to_asset": "USDT", "amount": 999, "expected_received": quote["received"],
    })
    assert swap.status_code == 409
    assert "Insufficient" in swap.json()["detail"]

    balances = {row["asset"]: row["amount"] for row in client.get("/v1/balances", headers=headers).json()}
    assert balances["BTC"] == DEMO_STARTING_BALANCES["BTC"]


def test_swap_stale_quote_rejected(client):
    _, _, token = register(client)
    headers = auth_headers(token)
    swap = client.post("/v1/swaps", headers=headers, json={
        "from_asset": "USDT", "to_asset": "BTC", "amount": 100, "expected_received": 999999,
    })
    assert swap.status_code == 409
    assert "Quote changed" in swap.json()["detail"]


def test_swaps_scoped_per_user(client):
    _, _, token_a = register(client)
    _, _, token_b = register(client)
    headers_a, headers_b = auth_headers(token_a), auth_headers(token_b)

    quote = client.post("/v1/quotes", json={"from_asset": "USDT", "to_asset": "SOL", "amount": 500}).json()
    client.post("/v1/swaps", headers=headers_a, json={
        "from_asset": "USDT", "to_asset": "SOL", "amount": 500, "expected_received": quote["received"],
    })

    assert len(client.get("/v1/swaps", headers=headers_a).json()) == 1
    assert len(client.get("/v1/swaps", headers=headers_b).json()) == 0


def test_password_reset_flow_and_session_revocation(client):
    email, password, old_token = register(client)
    old_headers = auth_headers(old_token)
    assert client.get("/v1/auth/me", headers=old_headers).status_code == 200

    request_reset = client.post("/v1/auth/password-reset/request", json={"email": email})
    assert request_reset.status_code == 200
    reset_token = request_reset.json()["dev_reset_token"]
    assert reset_token

    new_password = "a-different-strong-password"
    confirm = client.post("/v1/auth/password-reset/confirm", json={"token": reset_token, "new_password": new_password})
    assert confirm.status_code == 200, confirm.text
    new_token = confirm.json()["access_token"]

    # Old sessions must be dead the instant the password changes.
    assert client.get("/v1/auth/me", headers=old_headers).status_code == 401
    # The reset itself signs the user back in with a fresh, valid token.
    assert client.get("/v1/auth/me", headers=auth_headers(new_token)).status_code == 200
    # Old password no longer works; new one does.
    assert client.post("/v1/auth/login", json={"email": email, "password": password}).status_code == 401
    assert client.post("/v1/auth/login", json={"email": email, "password": new_password}).status_code == 200


def test_password_reset_request_unknown_email_is_generic(client):
    response = client.post("/v1/auth/password-reset/request", json={"email": "nobody-here@example.com"})
    assert response.status_code == 200
    assert "dev_reset_token" not in response.json() or response.json().get("dev_reset_token") is None


def test_password_reset_token_single_use(client):
    email, _, _ = register(client)
    reset_token = client.post("/v1/auth/password-reset/request", json={"email": email}).json()["dev_reset_token"]

    first = client.post("/v1/auth/password-reset/confirm", json={"token": reset_token, "new_password": "first-new-password-123"})
    assert first.status_code == 200

    second = client.post("/v1/auth/password-reset/confirm", json={"token": reset_token, "new_password": "second-new-password-123"})
    assert second.status_code == 400


def test_password_reset_invalid_token_rejected(client):
    response = client.post("/v1/auth/password-reset/confirm", json={"token": "not-a-real-token", "new_password": "whatever-password-123"})
    assert response.status_code == 400


def test_email_verification_flow(client):
    _, _, token = register(client)
    headers = auth_headers(token)

    me = client.get("/v1/auth/me", headers=headers).json()
    assert me["is_email_verified"] is False

    request_verify = client.post("/v1/auth/verify-email/request", headers=headers)
    assert request_verify.status_code == 200
    verify_token = request_verify.json()["dev_verification_token"]
    assert verify_token

    confirm = client.post("/v1/auth/verify-email/confirm", json={"token": verify_token})
    assert confirm.status_code == 200
    assert confirm.json()["is_email_verified"] is True

    me_after = client.get("/v1/auth/me", headers=headers).json()
    assert me_after["is_email_verified"] is True

    already_verified = client.post("/v1/auth/verify-email/request", headers=headers)
    assert already_verified.status_code == 200
    assert "already verified" in already_verified.json()["detail"].lower()


def test_sign_out_everywhere_revokes_old_token(client):
    _, _, token_a = register(client)
    headers_a = auth_headers(token_a)

    sign_out_everywhere = client.post("/v1/auth/sign-out-everywhere", headers=headers_a)
    assert sign_out_everywhere.status_code == 200
    new_token = sign_out_everywhere.json()["access_token"]

    assert client.get("/v1/auth/me", headers=headers_a).status_code == 401
    assert client.get("/v1/auth/me", headers=auth_headers(new_token)).status_code == 200


def test_rate_limit_trips_after_threshold(client):
    for _ in range(10):
        response = client.post("/v1/auth/password-reset/request", json={"email": "rate-limit-probe@example.com"})
        assert response.status_code == 200
    limited = client.post("/v1/auth/password-reset/request", json={"email": "rate-limit-probe@example.com"})
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers


def test_admin_endpoints_require_admin_role(client):
    _, _, customer_token = register(client)
    assert client.get("/v1/admin/summary", headers=auth_headers(customer_token)).status_code == 403

    admin_login = client.post("/v1/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"],
    })
    assert admin_login.status_code == 200
    admin_headers = auth_headers(admin_login.json()["access_token"])

    summary = client.get("/v1/admin/summary", headers=admin_headers)
    assert summary.status_code == 200
    assert "users" in summary.json() and "swaps" in summary.json()


def admin_headers_for(client):
    admin_login = client.post("/v1/auth/login", json={
        "email": os.environ["ADMIN_EMAIL"], "password": os.environ["ADMIN_PASSWORD"],
    })
    assert admin_login.status_code == 200
    return auth_headers(admin_login.json()["access_token"])


def test_admin_can_update_swap_status(client):
    _, _, token = register(client)
    headers = auth_headers(token)
    quote = client.post("/v1/quotes", json={"from_asset": "USDT", "to_asset": "ETH", "amount": 200}).json()
    swap = client.post("/v1/swaps", headers=headers, json={
        "from_asset": "USDT", "to_asset": "ETH", "amount": 200, "expected_received": quote["received"],
    }).json()

    update = client.patch(f"/v1/admin/swaps/{swap['reference']}", headers=admin_headers_for(client), json={
        "status": "failed", "provider_reference": "provider-ref-123",
    })
    assert update.status_code == 200, update.text
    assert update.json()["status"] == "failed"

    # A non-admin can't touch it.
    forbidden = client.patch(f"/v1/admin/swaps/{swap['reference']}", headers=headers, json={"status": "completed"})
    assert forbidden.status_code == 403


def test_admin_update_unknown_swap_returns_404(client):
    response = client.patch("/v1/admin/swaps/SWP-DOESNOTEXIST", headers=admin_headers_for(client), json={"status": "completed"})
    assert response.status_code == 404


def test_health_check_reports_database_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_unhandled_error_returns_generic_response_and_is_logged(client, monkeypatch, caplog):
    import app.main as main_module
    from fastapi.testclient import TestClient

    def boom(*_args, **_kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(main_module, "ensure_balances", boom)
    _, _, token = register(client)

    # TestClient re-raises exceptions by default even when a registered handler already
    # produced a response, specifically so tests don't miss real bugs. Here the "bug" is
    # intentional, so this one client opts out to check what a real caller would receive.
    with caplog.at_level("ERROR"), TestClient(main_module.app, raise_server_exceptions=False) as quiet_client:
        response = quiet_client.get("/v1/balances", headers=auth_headers(token))

    assert response.status_code == 500
    assert response.json() == {"detail": "Something went wrong. Please try again."}
    assert "simulated failure" not in response.text
    assert "unhandled_error" in caplog.text
