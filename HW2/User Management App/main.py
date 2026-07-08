from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="User Management API", version="1.0.0")

# Mount static files directory for serving HTML/CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for request/response validation
class User(BaseModel):
    id: int
    name: str

class UserCreate(BaseModel):
    name: str

class UserUpdate(BaseModel):
    name: str

# In-memory user storage
users: List[User] = [
    User(id=1, name="Alice"),
    User(id=2, name="Bob")
]

# Serve the main HTML page
@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

# REST API Endpoints

from fastapi import Response

@app.get("/api/users", response_model=List[User])
async def get_users(response: Response):
    """Get all users - Returns JSON array of user objects"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return users

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get a specific user by ID"""
    user = next((user for user in users if user.id == user_id), None)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users", response_model=User, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user - Accepts JSON with 'name' field"""
    if not user_data.name.strip():
        raise HTTPException(status_code=400, detail="User name is required")
    
    # Generate new ID
    new_id = max([user.id for user in users], default=0) + 1
    new_user = User(id=new_id, name=user_data.name)
    users.append(new_user)
    
    print(f"Created user: {new_user}")
    return new_user

@app.put("/api/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_data: UserUpdate):
    """Update an existing user - Accepts JSON with 'name' field"""
    user = next((user for user in users if user.id == user_id), None)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user_data.name.strip():
        raise HTTPException(status_code=400, detail="User name is required")
    
    user.name = user_data.name
    print(f"Updated user: {user}")
    return user

@app.delete("/api/users/{user_id}", status_code=204)
async def delete_user(user_id: int):
    """Delete a user by ID"""
    global users
    user_index = next((index for index, user in enumerate(users) if user.id == user_id), None)
    
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted_user = users.pop(user_index)
    print(f"Deleted user: {deleted_user}")
    return None

import webbrowser

# Start the server
if __name__ == "__main__":
    # Open the browser automatically
    webbrowser.open("http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
