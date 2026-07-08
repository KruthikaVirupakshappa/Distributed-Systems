from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr

class UserUpdate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True