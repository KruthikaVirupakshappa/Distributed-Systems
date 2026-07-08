from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# -------- Authors --------
class AuthorCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class AuthorUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class AuthorOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -------- Books --------
class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=3, max_length=20)
    publication_year: int = Field(ge=0, le=2100)
    available_copies: int = Field(ge=0, default=1)
    author_id: int = Field(gt=0)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, min_length=3, max_length=20)
    publication_year: Optional[int] = Field(default=None, ge=0, le=2100)
    available_copies: Optional[int] = Field(default=None, ge=0)
    author_id: Optional[int] = Field(default=None, gt=0)


class BookOut(BaseModel):
    id: int
    title: str
    isbn: str
    publication_year: int
    available_copies: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True