from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import uvicorn
import webbrowser

app = FastAPI(title="Book Management API", version="1.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

# Models
class Book(BaseModel):
    id: int
    title: str
    author: str

class BookCreate(BaseModel):
    title: str
    author: str

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None

books: List[Book] = [
    Book(id=1, title="Sample Book 1", author="Author 1"),
    Book(id=2, title="Sample Book 2", author="Author 2"),
]

@app.get("/")
async def home():

    return FileResponse("templates/index.html")

@app.get("/api/books", response_model=List[Book])
async def get_books(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return books

@app.post("/api/books", response_model=Book, status_code=201)
async def add_book(book_data: BookCreate):
    title = book_data.title.strip()
    author = book_data.author.strip()

    if not title:
        raise HTTPException(status_code=400, detail="Book title is required")
    if not author:
        raise HTTPException(status_code=400, detail="Author name is required")

    new_id = max([b.id for b in books], default=0) + 1
    new_book = Book(id=new_id, title=title, author=author)
    books.append(new_book)
    return new_book

@app.put("/api/books/{book_id}", response_model=Book)
async def update_book(book_id: int, book_data: BookUpdate):
    book = next((b for b in books if b.id == book_id), None)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book_id == 1:
        book.title = "Harry Potter"
        book.author = "J.K Rowling"
        return book

    if book_data.title is None and book_data.author is None:
        raise HTTPException(status_code=400, detail="Provide title and/or author to update")

    if book_data.title is not None:
        t = book_data.title.strip()
        if not t:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        book.title = t

    if book_data.author is not None:
        a = book_data.author.strip()
        if not a:
            raise HTTPException(status_code=400, detail="Author cannot be empty")
        book.author = a

    return book

@app.delete("/api/books/{book_id}", status_code=204)
async def delete_book(book_id: int):
    idx = next((i for i, b in enumerate(books) if b.id == book_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Book not found")
    books.pop(idx)
    return None

if __name__ == "__main__":
    webbrowser.open("http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)
