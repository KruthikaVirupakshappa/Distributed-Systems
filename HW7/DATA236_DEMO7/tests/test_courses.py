from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_token(username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )
    return response.json()["access_token"]


def test_student_cannot_create_course():
    token = get_token("alice", "alice123")
    response = client.post(
        "/courses",
        json={"title": "Cloud Computing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_instructor_can_create_course():
    token = get_token("bob", "bob123")
    response = client.post(
        "/courses",
        json={"title": "Cloud Computing"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201


def test_only_admin_can_delete_course():
    token = get_token("bob", "bob123")
    response = client.delete(
        "/courses/1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
