import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { createCourse, fetchCourses } from "../features/courses/coursesSlice";
import { api } from "../api/axios";

function toMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Validation error: please check inputs.";
  if (err?.message) return err.message;
  return "Something went wrong.";
}

export default function CreateCourse({ goTo }) {
  const dispatch = useDispatch();
  const { error } = useSelector((s) => s.courses);

  const [instructors, setInstructors] = useState([]);
  const [instMsg, setInstMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    title: "",
    code: "",
    year: 2026,
    seats_available: 30,
    instructor_id: 0
  });

  const loadInstructors = async () => {
    setInstMsg("");
    try {
      const res = await api.get("/instructors?skip=0&limit=50");
      setInstructors(res.data);
      if (res.data.length > 0) setForm((p) => ({ ...p, instructor_id: res.data[0].id }));
      else setInstMsg("No instructors found. Create one in the Instructors tab first.");
    } catch (err) {
      setInstMsg(`Could not load instructors: ${toMessage(err)}`);
      setInstructors([]);
      setForm((p) => ({ ...p, instructor_id: 0 }));
    }
  };

  useEffect(() => {
    loadInstructors();
  }, []);

  const onChange = (e) => {
    setSuccessMsg(""); // clear success on edit
    const { name, value } = e.target;
    setForm((p) => ({
      ...p,
      [name]: ["year", "seats_available", "instructor_id"].includes(name) ? Number(value) : value
    }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setSuccessMsg("");

    setSubmitting(true);
    try {
      // unwrap() throws if thunk rejected, returns payload if success
      const created = await dispatch(createCourse(form)).unwrap();

      // refresh list on home
      dispatch(fetchCourses());

      setSuccessMsg(`Course created: ${created.code} — ${created.title}`);

      // clear fields (keep instructor selected)
      setForm((p) => ({
        ...p,
        title: "",
        code: "",
        year: 2026,
        seats_available: 30
      }));

      // “route” to home after short delay (nice demo effect)
      if (goTo) {
        setTimeout(() => goTo("home"), 700);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card card-clean">
      <div className="card-header">
        <div className="fw-bold">Create Course</div>
        <div className="small-hint">Add a course linked to an instructor.</div>
      </div>

      <div className="card-body">
        {instMsg && <div className="alert alert-warning alert-clean py-2 mb-3">{instMsg}</div>}
        {error && <div className="alert alert-danger alert-clean py-2 mb-3">{String(error)}</div>}
        {successMsg && <div className="alert alert-success alert-clean py-2 mb-3">{successMsg}</div>}

        <form onSubmit={onSubmit} className="row g-3">
          <div className="col-12">
            <label className="form-label">Title</label>
            <input className="form-control" name="title" value={form.title} onChange={onChange} required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Code (unique)</label>
            <input className="form-control" name="code" value={form.code} onChange={onChange} required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Year</label>
            <input className="form-control" type="number" name="year" value={form.year} onChange={onChange} required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Seats Available</label>
            <input className="form-control" type="number" name="seats_available" value={form.seats_available} onChange={onChange} required />
          </div>

          <div className="col-md-6">
            <label className="form-label">Instructor</label>
            <div className="d-flex gap-2">
              <select
                className="form-select"
                name="instructor_id"
                value={form.instructor_id}
                onChange={onChange}
                disabled={instructors.length === 0}
              >
                {instructors.length === 0 && <option value={0}>No instructors</option>}
                {instructors.map((i) => (
                  <option key={i.id} value={i.id}>
                    {i.id} — {i.first_name} {i.last_name}
                  </option>
                ))}
              </select>

              <button type="button" className="btn btn-soft" onClick={loadInstructors} title="Reload instructors">
                ↻
              </button>
            </div>
          </div>

          <div className="col-12 d-flex gap-2">
            <button className="btn btn-brand" disabled={form.instructor_id === 0 || submitting}>
              {submitting ? "Creating..." : "Create"}
            </button>

            <button
              type="button"
              className="btn btn-soft"
              onClick={() =>
                setForm((p) => ({
                  ...p,
                  title: "",
                  code: "",
                  year: 2026,
                  seats_available: 30
                }))
              }
              disabled={submitting}
            >
              Clear
            </button>
          </div>

          <div className="small-hint">
            Tip: Use a code like <b>DATA236</b>. Duplicate code will return <b>409</b>.
          </div>
        </form>
      </div>
    </div>
  );
}