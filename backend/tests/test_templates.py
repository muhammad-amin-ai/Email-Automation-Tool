import uuid


def _register(client):
    email = f"u_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpassword123"},
    )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_template_crud(client):
    headers = _register(client)

    r = client.post(
        "/api/templates",
        json={
            "name": "Welcome",
            "subject": "Hi {{ first_name }}",
            "html_body": "<p>Hello {{ first_name }}!</p>",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    tid = r.json()["id"]

    r = client.get("/api/templates", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = client.put(
        f"/api/templates/{tid}",
        json={"name": "Welcome v2"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Welcome v2"

    r = client.delete(f"/api/templates/{tid}", headers=headers)
    assert r.status_code == 204
