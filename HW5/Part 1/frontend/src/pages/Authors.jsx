import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  fetchAuthors,
  createAuthor,
  updateAuthor,
  deleteAuthor,
} from "../features/authors/authorsSlice";

function shortErrText(err) {
  if (!err) return "";
  if (typeof err === "string") return err;
  if (err?.response?.data?.detail) return String(err.response.data.detail);
  if (err?.message) return err.message;
  return "Unknown error";
}

export default function Authors() {
  const dispatch = useDispatch();
  const { items, loading, error } = useSelector((s) => s.authors);

  const [createForm, setCreateForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
  });
  const [createError, setCreateError] = useState(null);
  const [creating, setCreating] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
  });
  const [editError, setEditError] = useState(null);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    dispatch(fetchAuthors());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refresh = () => {
    dispatch(fetchAuthors());
  };

  const onCreateChange = (e) => {
    const { name, value } = e.target;
    setCreateForm((f) => ({ ...f, [name]: value }));
  };

  const validateCreate = () => {
    if (!createForm.first_name?.trim()) return "First name is required.";
    if (!createForm.last_name?.trim()) return "Last name is required.";
    if (!createForm.email?.trim()) return "Email is required.";
    return null;
  };

  const submitCreate = async (e) => {
    e.preventDefault();
    setCreateError(null);
    const v = validateCreate();
    if (v) {
      setCreateError(v);
      return;
    }
    setCreating(true);
    try {
      await dispatch(createAuthor(createForm)).unwrap();
      setCreateForm({ first_name: "", last_name: "", email: "" });
      dispatch(fetchAuthors());
    } catch (err) {
      setCreateError(shortErrText(err) || "Failed to create author");
    } finally {
      setCreating(false);
    }
  };

  const startEdit = (a) => {
    setEditingId(a.id);
    setEditForm({
      first_name: a.first_name ?? "",
      last_name: a.last_name ?? "",
      email: a.email ?? "",
    });
    setEditError(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ first_name: "", last_name: "", email: "" });
    setEditError(null);
  };

  const onEditChange = (e) => {
    const { name, value } = e.target;
    setEditForm((f) => ({ ...f, [name]: value }));
  };

  const validateEdit = () => {
    if (!editForm.first_name?.trim()) return "First name is required.";
    if (!editForm.last_name?.trim()) return "Last name is required.";
    if (!editForm.email?.trim()) return "Email is required.";
    return null;
  };

  const submitEdit = async (e) => {
    e.preventDefault();
    setEditError(null);
    const v = validateEdit();
    if (v) {
      setEditError(v);
      return;
    }
    setEditing(true);
    try {
      await dispatch(updateAuthor({ id: editingId, payload: editForm })).unwrap();
      dispatch(fetchAuthors());
      cancelEdit();
    } catch (err) {
      setEditError(shortErrText(err) || "Failed to update author");
    } finally {
      setEditing(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this author? This will fail if the author has books.")) return;
    try {
      await dispatch(deleteAuthor(id)).unwrap();
      dispatch(fetchAuthors());
    } catch (err) {
      // show a small alert
      alert(shortErrText(err) || "Failed to delete author");
    }
  };

  return (
    <div className="card card-clean">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div>
          <div className="fw-bold">Authors</div>
          <div className="small-hint">Manage authors. You cannot delete an author with books.</div>
        </div>

        <div>
          <button className="btn btn-soft btn-sm" onClick={refresh}>Refresh</button>
        </div>
      </div>

      <div className="card-body">
        {loading && <div className="alert alert-info alert-clean py-2 mb-3">Loading authors...</div>}

        {error && (
          <div className="alert alert-danger alert-clean py-2 mb-3">
            {String(error)}
          </div>
        )}

        <div className="row">
          <div className="col-md-6">
            <h6 className="mb-2">Create Author</h6>
            {(createError) && <div className="alert alert-danger py-2">{createError}</div>}
            <form onSubmit={submitCreate}>
              <div className="mb-2">
                <input
                  name="first_name"
                  value={createForm.first_name}
                  onChange={onCreateChange}
                  className="form-control"
                  placeholder="First name"
                  disabled={creating}
                />
              </div>

              <div className="mb-2">
                <input
                  name="last_name"
                  value={createForm.last_name}
                  onChange={onCreateChange}
                  className="form-control"
                  placeholder="Last name"
                  disabled={creating}
                />
              </div>

              <div className="mb-2">
                <input
                  name="email"
                  value={createForm.email}
                  onChange={onCreateChange}
                  className="form-control"
                  placeholder="Email"
                  disabled={creating}
                />
              </div>

              <div className="d-flex gap-2">
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setCreateForm({ first_name: "", last_name: "", email: "" })}
                  disabled={creating}
                >
                  Clear
                </button>
              </div>
            </form>
          </div>

          <div className="col-md-6">
            <h6 className="mb-2">Authors List</h6>

            <div className="table-responsive">
              <table className="table table-sm mb-0">
                <thead>
                  <tr>
                    <th style={{ width: 70 }}>ID</th>
                    <th>Name</th>
                    <th style={{ width: 240 }}>Email</th>
                    <th style={{ width: 160 }}>Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {items.map((a) => (
                    <tr key={a.id}>
                      <td className="fw-semibold">{a.id}</td>
                      <td>
                        {editingId === a.id ? (
                          <div className="d-flex gap-1">
                            <input
                              name="first_name"
                              value={editForm.first_name}
                              onChange={onEditChange}
                              className="form-control form-control-sm"
                              disabled={editing}
                              style={{ width: 120 }}
                            />
                            <input
                              name="last_name"
                              value={editForm.last_name}
                              onChange={onEditChange}
                              className="form-control form-control-sm"
                              disabled={editing}
                              style={{ width: 120 }}
                            />
                          </div>
                        ) : (
                          `${a.first_name} ${a.last_name}`
                        )}
                      </td>

                      <td>
                        {editingId === a.id ? (
                          <input
                            name="email"
                            value={editForm.email}
                            onChange={onEditChange}
                            className="form-control form-control-sm"
                            disabled={editing}
                          />
                        ) : (
                          a.email
                        )}
                      </td>

                      <td>
                        {editingId === a.id ? (
                          <div className="d-flex gap-2">
                            <button className="btn btn-sm btn-primary" onClick={submitEdit} disabled={editing}>
                              Save
                            </button>
                            <button className="btn btn-sm btn-outline-secondary" onClick={cancelEdit} disabled={editing}>
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <div className="d-flex gap-2">
                            <button className="btn btn-sm btn-outline-secondary" onClick={() => startEdit(a)}>
                              Edit
                            </button>
                            <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(a.id)}>
                              Delete
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}

                  {items.length === 0 && (
                    <tr>
                      <td colSpan="4" className="text-center text-muted py-4">
                        No authors yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {editError && <div className="alert alert-danger mt-2">{editError}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}