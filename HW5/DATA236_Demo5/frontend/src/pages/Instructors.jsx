import React, { useEffect, useState } from "react";
import { api } from "../api/axios";

function toMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Validation error: please check inputs.";
  if (err?.message) return err.message;
  return "Something went wrong.";
}

export default function Instructors() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState("secondary");

  const [form, setForm] = useState({ first_name: "", last_name: "", email: "" });

  const load = async () => {
    setLoading(true);
    setMsg("");
    try {
      const res = await api.get("/instructors?skip=0&limit=50");
      setItems(res.data);
    } catch (err) {
      setMsgType("danger");
      setMsg(`Load failed: ${toMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    if (!form.email.trim()) {
      setMsgType("warning");
      setMsg("Email is required.");
      return;
    }

    try {
      await api.post("/instructors", form);
      setMsgType("success");
      setMsg("Instructor created.");
      setForm({ first_name: "", last_name: "", email: "" });
      await load();
    } catch (err) {
      setMsgType("danger");
      setMsg(`Create failed: ${toMessage(err)}`);
    }
  };

  return (
    <div className="row g-3">
      <div className="col-md-5">
        <div className="card card-clean">
          <div className="card-header">
            <div className="fw-bold">Create Instructor</div>
            <div className="small-hint">Add an instructor to use in course creation.</div>
          </div>

          <div className="card-body">
            {msg && <div className={`alert alert-${msgType} alert-clean py-2`}>{msg}</div>}

            <form onSubmit={onSubmit} className="row g-2">
              <div className="col-12">
                <label className="form-label">First Name</label>
                <input className="form-control" name="first_name" value={form.first_name} onChange={onChange} required />
              </div>

              <div className="col-12">
                <label className="form-label">Last Name</label>
                <input className="form-control" name="last_name" value={form.last_name} onChange={onChange} required />
              </div>

              <div className="col-12">
                <label className="form-label">Email (unique)</label>
                <input className="form-control" name="email" value={form.email} onChange={onChange} required />
              </div>

              <div className="col-12 d-flex gap-2">
                <button className="btn btn-brand" type="submit">Create</button>
                <button className="btn btn-soft" type="button" onClick={load}>Refresh</button>
              </div>
            </form>

            <div className="small-hint mt-3">
              Duplicate email → <b>409 Conflict</b> (good to demo constraint handling).
            </div>
          </div>
        </div>
      </div>

      <div className="col-md-7">
        <div className="card card-clean">
          <div className="card-header d-flex align-items-center justify-content-between">
            <div>
              <div className="fw-bold">Instructors</div>
              <div className="small-hint">List of available instructors.</div>
            </div>
            <button className="btn btn-soft btn-sm" onClick={load}>Refresh</button>
          </div>

          <div className="card-body">
            {loading && <div className="alert alert-info alert-clean py-2 mb-3">Loading...</div>}

            <div className="table-responsive table-clean">
              <table className="table table-sm mb-0">
                <thead>
                  <tr>
                    <th style={{ width: 70 }}>ID</th>
                    <th>First</th>
                    <th>Last</th>
                    <th>Email</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((i) => (
                    <tr key={i.id}>
                      <td className="fw-semibold">{i.id}</td>
                      <td>{i.first_name}</td>
                      <td>{i.last_name}</td>
                      <td>{i.email}</td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan="4" className="text-center text-muted py-4">
                        No instructors yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="small-hint mt-2">
              Create a course in the “Create Course” tab using the instructor dropdown.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}