from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)

class BookUpdate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)

class BookOut(BaseModel):
    id: int
    title: str 
    author: str 

    class Config:
        from_attributes = True