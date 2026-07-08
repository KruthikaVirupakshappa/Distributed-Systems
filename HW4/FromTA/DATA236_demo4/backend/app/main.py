from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import Response, Request
from .session_crud import create_session, get_session, delete_session

from .database import Base, engine, get_db
from . import crud, schema

Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Management API")

# Allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_session(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_id")
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in")
    s = get_session(db, token)
    if not s:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return s  # contains user_id

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/users", response_model=schema.UserOut)
def add_user(payload: schema.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, payload)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already exists")

@app.get("/users", response_model=list[schema.UserOut])
def list_users(
    db: Session = Depends(get_db),
    _session = Depends(require_session)
):
    return crud.get_users(db)

@app.get("/users/{user_id}", response_model=schema.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=schema.UserOut)
def edit_user(user_id: int, payload: schema.UserUpdate, db: Session = Depends(get_db)):
    user = crud.update_user(db, user_id, payload)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/{user_id}", response_model=schema.UserOut)
def remove_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.delete_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/auth/me")
def me(_session = Depends(require_session)):
    return {"logged_in": True, "user_id": _session.user_id}

@app.post("/auth/login")
def login(user_id: int, response: Response, db: Session = Depends(get_db)):
    # Demo-simple: login using an existing user_id (no password)
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    s = create_session(db, user_id=user_id)

    # cookie sent to browser/postman
    response.set_cookie(
        key="session_id",
        value=s.id,
        httponly=True,
        samesite="lax",
        max_age=30 * 60
    )
    return {"message": "logged in", "user_id": user_id}

@app.post("/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("session_id")
    if token:
        delete_session(db, token)
    response.delete_cookie("session_id")
    return {"message": "logged out"}