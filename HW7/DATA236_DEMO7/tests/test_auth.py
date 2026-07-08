from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success():
    response = client.post(
        "/auth/login",
        data={
            "username": "alice",
            "password": "alice123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_failure():
    response = client.post(
        "/auth/login",
        data={
            "username": "alice",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_users_me_requires_token():
    response = client.get("/users/me")
    assert response.status_code == 401
