import uuid


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_me_flow(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "strongpassword123"

    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r2 = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert r2.status_code == 200

    r3 = client.get("/api/auth/me", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["email"] == email


def test_register_duplicate(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    r1 = client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpassword123"},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpassword123"},
    )
    assert r2.status_code == 409


def test_login_invalid_credentials(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrongpassword"},
    )
    assert r.status_code == 401


def test_protected_endpoint_requires_auth(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post(
        "/api/auth/register",
        json={"email": f"u_{uuid.uuid4().hex[:6]}@example.com", "password": "short"},
    )
    assert r.status_code == 422
