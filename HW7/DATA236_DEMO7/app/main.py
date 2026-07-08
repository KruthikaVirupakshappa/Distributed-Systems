from fastapi import FastAPI

from app.routers import auth, courses, users

app = FastAPI(
    title="DATA 236 Demo 7 - JWT Authentication & Authorization",
    version="1.0.0",
    description="FastAPI demo for authentication, authorization, linting, "
    "and CI pipeline.",
)


@app.get("/")
def root():
    return {
        "message": "FastAPI JWT Auth Demo is running",
        "docs": "/docs",
    }


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(courses.router)
