import React from "react";
import { Link } from "react-router-dom";

export default function Home({ books, loading, auth }) {
  // If not logged in
  if (!auth.loggedIn) {
    return (
      <div className="card">
        <div className="card-body">
          <div className="notice">Login required.</div>
        </div>
      </div>
    );
  }

  // Logged in: show books
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="page-title">Books</div>
          <div className="subtitle">
            Session-based access: these books are fetched from FastAPI + MySQL using your cookie session.
          </div>
        </div>

        <Link className="btn primary" to="/create">
          + Add Book
        </Link>
      </div>

      <div className="card-body">
        {loading ? (
          <div className="notice">Loading books...</div>
        ) : books.length === 0 ? (
          <div className="notice">No books found. Click “Add Book”.</div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Author</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {books.map((b) => (
                  <tr key={b.id}>
                    <td>{b.id}</td>
                    <td>{b.title}</td>
                    <td>{b.author}</td>
                    <td className="actions">
                      <Link className="btn" to={`/update/${b.id}`}>
                        Update
                      </Link>
                      <Link className="btn danger" to={`/delete/${b.id}`}>
                        Delete
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
