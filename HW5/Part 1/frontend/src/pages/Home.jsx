import React, { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchBooks, deleteBook } from "../features/books/booksSlice";
import { api } from "../api/axios";

function getErrText(err) {
  const status = err?.response?.status;
  const detail = err?.response?.data?.detail;

  if (typeof detail === "string") return `HTTP ${status}: ${detail}`;
  if (Array.isArray(detail)) return `HTTP ${status}: Validation error`;
  if (status) return `HTTP ${status}: Request failed`;
  if (err?.message) return err.message;
  return "Unknown error";
}

export default function Home() {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((s) => s.books);

  const [authors, setAuthors] = useState([]);
  const [authError, setAuthError] = useState("");

  const authorMap = useMemo(() => {
    const m = new Map();
    authors.forEach((a) => m.set(a.id, `${a.first_name} ${a.last_name}`));
    return m;
  }, [authors]);

  const loadAuthors = async () => {
    setAuthError("");
    try {
      const res = await api.get("/authors?skip=0&limit=200");
      setAuthors(res.data);
    } catch (err) {
      setAuthError(`Author fetch failed → ${getErrText(err)}  (GET /authors)`);
      setAuthors([]);
    }
  };

  const refreshAll = async () => {
    dispatch(fetchBooks());
    await loadAuthors();
  };

  useEffect(() => {
    refreshAll();
  }, []);

  return (
    <div className="card card-clean">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div>
          <div className="fw-bold">Books</div>
          <div className="small-hint">View, refresh, and delete books.</div>
        </div>
        <button className="btn btn-soft btn-sm" onClick={refreshAll}>
          Refresh
        </button>
      </div>

      <div className="card-body">
        {loading && <div className="alert alert-info alert-clean py-2 mb-3">Loading...</div>}

        {error && (
          <div className="alert alert-danger alert-clean py-2 mb-3">
            {String(error)}
            <div className="small mt-1">If this looks like a network error, confirm backend is running on :8000.</div>
          </div>
        )}

        {authError && <div className="alert alert-warning alert-clean py-2 mb-3">{authError}</div>}

        <div className="table-responsive table-clean">
          <table className="table table-sm mb-0">
            <thead>
              <tr>
                <th style={{ width: 70 }}>ID</th>
                <th>Title</th>
                <th style={{ width: 160 }}>ISBN</th>
                <th style={{ width: 110 }}>Publication Year</th>
                <th style={{ width: 110 }}>Copies</th>
                <th style={{ width: 200 }}>Author</th>
                <th style={{ width: 110 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((b) => {
                const name = authorMap.get(b.author_id);
                return (
                  <tr key={b.id}>
                    <td className="fw-semibold">{b.id}</td>
                    <td>{b.title}</td>
                    <td>
                      <span className="badge badge-soft">{b.isbn}</span>
                    </td>
                    <td>{b.publication_year}</td>
                    <td>{b.available_copies}</td>
                    <td>{name ? name : `ID: ${b.author_id}`}</td>
                    <td>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => dispatch(deleteBook(b.id))}>
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}

              {items.length === 0 && (
                <tr>
                  <td colSpan="7" className="text-center text-muted py-4">
                    No books yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="small-hint mt-2"></div>
      </div>
    </div>
  );
}