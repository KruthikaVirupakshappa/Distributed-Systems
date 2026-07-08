import os
import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from routers.auth import router as auth_router

# Create FastAPI app
app = FastAPI(title="ADS-SJSU Authentication System")

# Secret key for session signing
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-key")

# Enable session support
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    https_only=True, 
    same_site="lax",
    max_age=3600       
)

# Register routes
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )