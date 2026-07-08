import requests

BASE_URL = "http://127.0.0.1:8000/books"

payload = {
    "operation": "CREATE_BOOK",
    "title": "FastAPI Basics",
    "author": "Devdatta",
    "price": 300
}

response = requests.post(BASE_URL, json=payload)
print(response.json())