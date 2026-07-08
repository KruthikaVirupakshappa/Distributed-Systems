import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchBookById } from "../api/usersApi.js";

export default function DeleteBook({ onDelete }) {
  const { id } = useParams();
  const bookId = Number(id);
  const navigate = useNavigate();

  const [book, setBook] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchBookById(bookId);
        setBook(data);
      } catch {
        setBook(null);
      }
    })();
  }, [bookId]);

  async function handleDelete() {
    await onDelete(bookId);
    navigate("/");
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="page-title">Delete Book</div>
      </div>

      <div className="card-body">
        {book ? (
          <>
            <p style={{ fontSize: "18px", marginBottom: "24px" }}>
              Are you sure you want to delete{" "}
              <strong>{book.title}</strong> by {book.author}?
            </p>

            <button className="btn danger" onClick={handleDelete}>
              Delete Book
            </button>
          </>
        ) : (
          <div className="notice">
            Book not found (or already deleted).
          </div>
        )}
      </div>
    </div>
  );
}
