from app.core.security import get_password_hash

fake_users_db = {
    "alice": {
        "username": "alice",
        "full_name": "Alice Student",
        "role": "student",
        "hashed_password": get_password_hash("alice123"),
        "disabled": False,
    },
    "bob": {
        "username": "bob",
        "full_name": "Bob Instructor",
        "role": "instructor",
        "hashed_password": get_password_hash("bob123"),
        "disabled": False,
    },
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "role": "admin",
        "hashed_password": get_password_hash("admin123"),
        "disabled": False,
    },
}

fake_courses_db = [
    {
        "id": 1,
        "title": "Distributed Systems",
        "instructor": "bob",
    },
    {
        "id": 2,
        "title": "Data Engineering",
        "instructor": "bob",
    },
]
