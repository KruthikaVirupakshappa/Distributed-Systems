import React from "react";
import { Link } from "react-router-dom";

export default function Home({ users, loading, auth }) {
  // If not logged in, show a clear message (since backend is protected)
  if (!auth.loggedIn) {
    return (
      <div className="card">
        <div className="card-header">
          <div>
            <div className="page-title">Users</div>
            <div className="subtitle">
              Login first to fetch users from the protected API.
            </div>
          </div>
        </div>

        <div className="card-body">
          <div className="notice">
            🔒 You are not logged in. Use the Login bar above (enter a valid user_id).
          </div>
        </div>
      </div>
    );
  }

  // Logged in: show users table
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="page-title">Users</div>
          <div className="subtitle">
            Session-based access: these users are fetched from FastAPI + MySQL using your cookie session.
          </div>
        </div>

        <Link className="btn primary" to="/create">
          + Add User
        </Link>
      </div>

      <div className="card-body">
        {loading ? (
          <div className="notice">Loading users...</div>
        ) : users.length === 0 ? (
          <div className="notice">No users found. Click “Add User”.</div>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>{u.id}</td>
                    <td>{u.name}</td>
                    <td>{u.email}</td>
                    <td className="actions">
                      <Link className="btn" to={`/update/${u.id}`}>
                        Update
                      </Link>
                      <Link className="btn danger" to={`/delete/${u.id}`}>
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