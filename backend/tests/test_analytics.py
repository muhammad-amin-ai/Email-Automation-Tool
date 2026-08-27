import uuid


def _register(client):
    email = f"u_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpassword123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_analytics_summary(client):
    headers = _register(client)
    r = client.get("/api/analytics/summary", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total_contacts" in data
    assert "total_sent" in data
    assert isinstance(data["total_contacts"], int)
