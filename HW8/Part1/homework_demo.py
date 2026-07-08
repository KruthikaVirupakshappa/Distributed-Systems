"""
homework_demo.py — demonstrates CREATE_USER and GET_USER via the FastAPI service.

Make sure:
  1. Docker Kafka is running:  docker-compose up -d
  2. Worker is running:        python worker.py
  3. FastAPI is running:       uvicorn main:app --reload
"""

import requests

BASE_URL = "http://127.0.0.1:8000"


def demo_create_user():
    print("\n=== CREATE_USER ===")
    payload = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 30,
    }
    print(f"Request:  POST /users  {payload}")
    response = requests.post(f"{BASE_URL}/users", json=payload)
    data = response.json()
    print(f"Response: {data}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert data["success"] is True
    return data["userId"]


def demo_get_user(user_id: str):
    print("\n=== GET_USER ===")
    print(f"Request:  GET /users/{user_id}")
    response = requests.get(f"{BASE_URL}/users/{user_id}")
    data = response.json()
    print(f"Response: {data}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert data["success"] is True
    assert data["user"]["userId"] == user_id


def demo_get_nonexistent_user():
    print("\n=== GET_USER (non-existent) ===")
    bad_id = "00000000-0000-0000-0000-000000000000"
    print(f"Request:  GET /users/{bad_id}")
    response = requests.get(f"{BASE_URL}/users/{bad_id}")
    data = response.json()
    print(f"Response (status {response.status_code}): {data}")
    assert response.status_code == 404


if __name__ == "__main__":
    user_id = demo_create_user()
    demo_get_user(user_id)
    demo_get_nonexistent_user()
    print("\nAll demo operations completed successfully.")
