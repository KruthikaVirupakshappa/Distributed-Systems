import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function CreateBook({ onAdd }) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    await onAdd({ title, author });
    navigate("/");
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="page-title">Add Book</div>
        <div className="subtitle">Enter book details below</div>
      </div>

      <div className="card-body">
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Book Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>

          <label>
            Author Name
            <input value={author} onChange={(e) => setAuthor(e.target.value)} />
          </label>

          <button className="btn primary" type="submit">
            Add Book
          </button>
        </form>
      </div>
    </div>
  );
}
