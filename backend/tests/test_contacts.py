import uuid


def _register(client):
    email = f"u_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "strongpassword123"},
    )
    assert r.status_code == 201
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_contacts_crud(client):
    headers = _register(client)

    r = client.post(
        "/api/contacts",
        json={"email": "contact@example.com", "first_name": "John", "last_name": "Doe"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    contact_id = r.json()["id"]

    r = client.get("/api/contacts", headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"/api/contacts/{contact_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "contact@example.com"

    r = client.put(
        f"/api/contacts/{contact_id}",
        json={"first_name": "Jane"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["first_name"] == "Jane"

    r = client.delete(f"/api/contacts/{contact_id}", headers=headers)
    assert r.status_code == 204


def test_user_isolation(client):
    h1 = _register(client)
    h2 = _register(client)

    r = client.post(
        "/api/contacts",
        json={"email": "private@example.com"},
        headers=h1,
    )
    assert r.status_code == 201
    cid = r.json()["id"]

    r = client.get(f"/api/contacts/{cid}", headers=h2)
    assert r.status_code == 404

    r = client.delete(f"/api/contacts/{cid}", headers=h2)
    assert r.status_code == 404


def test_csv_import(client):
    headers = _register(client)
    csv_content = (
        "email,first_name,last_name\n"
        "alice@example.com,Alice,Smith\n"
        "bob@example.com,Bob,Jones\n"
        "not-an-email,Charlie,Brown\n"
    )
    files = {"file": ("contacts.csv", csv_content, "text/csv")}
    r = client.post("/api/contacts/import", files=files, headers=headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["imported"] == 2
    assert data["invalid"] == 1
