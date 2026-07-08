from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .db import ensure_collections
from .routes.memory import router as memory_router
from .routes.tasks import router as tasks_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err.get("loc", [])[1:])
        errors.append({"field": field, "message": err.get("msg")})

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors,
        },
    )


@app.on_event("startup")
def on_startup():
    ensure_collections()


app.include_router(tasks_router)
app.include_router(memory_router)


@app.get("/")
def health():
    return {"status": "ok", "message": "Homework 6 API is running"}
