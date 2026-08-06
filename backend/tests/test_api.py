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
