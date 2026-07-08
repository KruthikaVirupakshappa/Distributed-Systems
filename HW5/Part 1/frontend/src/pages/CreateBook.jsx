import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { createBook, fetchBooks } from "../features/books/booksSlice";
import { fetchAuthors } from "../features/authors/authorsSlice";

export default function CreateBook({ goTo }) {
  const dispatch = useDispatch();
  const { items: authors, loading: authorsLoading, error: authorsError } = useSelector((s) => s.authors);
  const booksState = useSelector((s) => s.books);

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
    // ensure authors are loaded for the author dropdown
    if (!authors || authors.length === 0) {
      dispatch(fetchAuthors());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    // numbers should be stored as numbers
    if (name === "publication_year" || name === "available_copies" || name === "author_id") {
      setForm((f) => ({ ...f, [name]: value === "" ? "" : Number(value) }));
    } else {
      setForm((f) => ({ ...f, [name]: value }));
    }
  };

  const validate = () => {
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
      // dispatch createBook and unwrap to catch errors
      await dispatch(createBook(form)).unwrap();
      // refresh books in case other parts rely on list
      dispatch(fetchBooks());
      // navigate back to home
      if (typeof goTo === "function") goTo("home");
    } catch (err) {
      // err will be the message from thunk.rejectWithValue or network error string
      setLocalError(err || "Failed to create book");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card card-clean">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div>
          <div className="fw-bold">Create Book</div>
          <div className="small-hint">Add a new book to the library.</div>
        </div>

        <div>
          <button className="btn btn-outline-secondary btn-sm" onClick={() => goTo("home")}>
            Cancel
          </button>
        </div>
      </div>

      <div className="card-body">
        {(localError || booksState.error) && (
          <div className="alert alert-danger alert-clean py-2 mb-3">
            {String(localError || booksState.error)}
          </div>
        )}

        {authorsError && (
          <div className="alert alert-warning alert-clean py-2 mb-3">
            Failed to load authors: {String(authorsError)}
          </div>
        )}

        <form onSubmit={onSubmit}>
          <div className="mb-3">
            <label className="form-label">Title</label>
            <input
              name="title"
              value={form.title}
              onChange={onChange}
              className="form-control"
              placeholder="Book title"
              disabled={submitting}
            />
          </div>

          <div className="mb-3">
            <label className="form-label">ISBN</label>
            <input
              name="isbn"
              value={form.isbn}
              onChange={onChange}
              className="form-control"
              placeholder="ISBN (unique)"
              disabled={submitting}
            />
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
                disabled={submitting}
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
                disabled={submitting}
              />
            </div>

            <div className="col-md-4 mb-3">
              <label className="form-label">Author</label>
              <select
                name="author_id"
                value={form.author_id}
                onChange={onChange}
                className="form-select"
                disabled={submitting || authorsLoading}
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
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating..." : "Create Book"}
            </button>

            <button
              type="button"
              className="btn btn-outline-secondary"
              onClick={() => {
                setForm({
                  title: "",
                  isbn: "",
                  publication_year: new Date().getFullYear(),
                  available_copies: 1,
                  author_id: "",
                });
                setLocalError(null);
              }}
              disabled={submitting}
            >
              Clear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}