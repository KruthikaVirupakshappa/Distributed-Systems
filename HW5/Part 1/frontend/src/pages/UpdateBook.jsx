import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchBooks } from "../features/books/booksSlice";
import { updateBook } from "../features/books/booksSlice";
import { fetchAuthors } from "../features/authors/authorsSlice";

export default function UpdateBook({ goTo }) {
  const dispatch = useDispatch();
  const { items: books, loading: booksLoading, error: booksError } = useSelector((s) => s.books);
  const { items: authors, loading: authorsLoading, error: authorsError } = useSelector((s) => s.authors);

  const [selectedId, setSelectedId] = useState("");
  const [form, setForm] = useState({
    title: "",
    isbn: "",
    publication_year: new Date().getFullYear(),
    available_copies: 1,
    author_id: "",
  });

  const [localError, setLocalError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!books || books.length === 0) dispatch(fetchBooks());
    if (!authors || authors.length === 0) dispatch(fetchAuthors());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // when user selects a book id, populate the form
  useEffect(() => {
    if (!selectedId) {
      setForm({
        title: "",
        isbn: "",
        publication_year: new Date().getFullYear(),
        available_copies: 1,
        author_id: "",
      });
      setLocalError(null);
      return;
    }
    const b = books.find((x) => Number(x.id) === Number(selectedId));
    if (b) {
      setForm({
        title: b.title ?? "",
        isbn: b.isbn ?? "",
        publication_year: b.publication_year ?? new Date().getFullYear(),
        available_copies: b.available_copies ?? 1,
        author_id: b.author_id ?? "",
      });
      setLocalError(null);
    } else {
      setLocalError("Selected book not found in local list. Try refreshing.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, books]);

  const onChange = (e) => {
    const { name, value } = e.target;
    if (name === "publication_year" || name === "available_copies" || name === "author_id") {
      setForm((f) => ({ ...f, [name]: value === "" ? "" : Number(value) }));
    } else {
      setForm((f) => ({ ...f, [name]: value }));
    }
  };

  const validate = () => {
    if (!selectedId) return "Select a book to update.";
    if (!form.title || form.title.trim().length === 0) return "Title is required.";
    if (!form.isbn || form.isbn.trim().length === 0) return "ISBN is required.";
    if (!form.author_id) return "Please select an author.";
    if (!Number.isInteger(form.publication_year) || form.publication_year <= 0)
      return "Publication year must be a positive integer.";
    if (!Number.isInteger(form.available_copies) || form.available_copies < 0)
      return "Available copies must be 0 or greater.";
    return null;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setLocalError(null);
    const v = validate();
    if (v) {
      setLocalError(v);
      return;
    }

    setSubmitting(true);
    try {
      await dispatch(updateBook({ id: selectedId, payload: form })).unwrap();
      dispatch(fetchBooks());
      if (typeof goTo === "function") goTo("home");
    } catch (err) {
      setLocalError(err || "Failed to update book");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card card-clean">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div>
          <div className="fw-bold">Update Book</div>
          <div className="small-hint">Select a book, edit fields, and save changes.</div>
        </div>

        <div>
          <button className="btn btn-outline-secondary btn-sm" onClick={() => (typeof goTo === "function" ? goTo("home") : null)}>
            Cancel
          </button>
        </div>
      </div>

      <div className="card-body">
        {(localError || booksError) && (
          <div className="alert alert-danger alert-clean py-2 mb-3">{String(localError || booksError)}</div>
        )}

        {authorsError && <div className="alert alert-warning alert-clean py-2 mb-3">Failed to load authors: {String(authorsError)}</div>}

        <form onSubmit={onSubmit}>
          <div className="mb-3">
            <label className="form-label">Choose Book</label>
            <select className="form-select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
              <option value="">Select a book by ID</option>
              {books &&
                books.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.id} — {b.title}
                  </option>
                ))}
            </select>
          </div>

          <div className="mb-3">
            <label className="form-label">Title</label>
            <input name="title" value={form.title} onChange={onChange} className="form-control" disabled={submitting || !selectedId} />
          </div>

          <div className="mb-3">
            <label className="form-label">ISBN</label>
            <input name="isbn" value={form.isbn} onChange={onChange} className="form-control" disabled={submitting || !selectedId} />
          </div>

          <div className="row">
            <div className="col-md-4 mb-3">
              <label className="form-label">Publication Year</label>
              <input
                name="publication_year"
                type="number"
                value={form.publication_year}
                onChange={onChange}
                className="form-control"
                disabled={submitting || !selectedId}
              />
            </div>

            <div className="col-md-4 mb-3">
              <label className="form-label">Available Copies</label>
              <input
                name="available_copies"
                type="number"
                value={form.available_copies}
                onChange={onChange}
                className="form-control"
                min="0"
                disabled={submitting || !selectedId}
              />
            </div>

            <div className="col-md-4 mb-3">
              <label className="form-label">Author</label>
              <select
                name="author_id"
                value={form.author_id}
                onChange={onChange}
                className="form-select"
                disabled={submitting || !selectedId || authorsLoading}
              >
                <option value="">Select an author</option>
                {authors &&
                  authors.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.first_name} {a.last_name}
                    </option>
                  ))}
              </select>
            </div>
          </div>

          <div className="d-flex gap-2">
            <button type="submit" className="btn btn-primary" disabled={submitting || !selectedId}>
              {submitting ? "Saving..." : "Save Changes"}
            </button>

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => {
                if (selectedId) {
                  const b = books.find((x) => Number(x.id) === Number(selectedId));
                  if (b) {
                    setForm({
                      title: b.title ?? "",
                      isbn: b.isbn ?? "",
                      publication_year: b.publication_year ?? new Date().getFullYear(),
                      available_copies: b.available_copies ?? 1,
                      author_id: b.author_id ?? "",
                    });
                    setLocalError(null);
                  }
                } else {
                  setForm({
                    title: "",
                    isbn: "",
                    publication_year: new Date().getFullYear(),
                    available_copies: 1,
                    author_id: "",
                  });
                  setLocalError(null);
                }
              }}
              disabled={submitting}
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}