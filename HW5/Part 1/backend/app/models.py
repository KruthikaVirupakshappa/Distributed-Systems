from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class Author(Base):
    __tablename__ = "authors"
    __table_args__ = (UniqueConstraint("email", name="uq_authors_email"),)

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    books = relationship("Book", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("isbn", name="uq_books_isbn"),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    isbn = Column(String(20), nullable=False, index=True)
    publication_year = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False, default=1)

    author_id = Column(Integer, ForeignKey("authors.id", ondelete="RESTRICT"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("Author", back_populates="books")