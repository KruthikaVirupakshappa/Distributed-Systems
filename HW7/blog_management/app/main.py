from fastapi import FastAPI

from app.routers import auth, posts, users

app = FastAPI(
    title="Blog Management System",
    version="1.0.0",
    description="FastAPI Blog API with JWT auth and role-based authorization.",
)


@app.get("/")
def root():
    return {
        "message": "Blog Management System is running",
        "docs": "/docs",
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)
