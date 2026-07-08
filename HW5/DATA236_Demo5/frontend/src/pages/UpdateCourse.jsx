import React, { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { updateCourse } from "../features/courses/coursesSlice";
import { api } from "../api/axios";

function toMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return "Validation error: please check inputs.";
  if (err?.message) return err.message;
  return "Something went wrong.";
}

export default function UpdateCourse() {
  const dispatch = useDispatch();
  const { error } = useSelector((s) => s.courses);

  const [instructors, setInstructors] = useState([]);
  const [instMsg, setInstMsg] = useState("");

  const [id, setId] = useState(1);
  const [payload, setPayload] = useState({
    title: "",
    code: "",
    year: "",
    seats_available: "",
    instructor_id: ""
  });

  const loadInstructors = async () => {
    setInstMsg("");
    try {
      const res = await api.get("/instructors?skip=0&limit=50");
      setInstructors(res.data);
    } catch (err) {
      setInstMsg(`Could not load instructors: ${toMessage(err)}`);
      setInstructors([]);
    }
  };

  useEffect(() => {
    loadInstructors();
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    setPayload((p) => ({ ...p, [name]: value }));
  };

  const onSubmit = (e) => {
    e.preventDefault();
    const clean = {};
    for (const [k, v] of Object.entries(payload)) {
      if (v === "") continue;
      clean[k] = ["year", "seats_available", "instructor_id"].includes(k) ? Number(v) : v;
    }
    dispatch(updateCourse({ id: Number(id), payload: clean }));
  };

  return (
    <div className="card card-clean">
      <div className="card-header">
        <div className="fw-bold">Update Course</div>
        <div className="small-hint">Update fields for a course by ID (only filled fields are sent).</div>
      </div>

      <div className="card-body">
        {instMsg && <div className="alert alert-warning alert-clean py-2 mb-3">{instMsg}</div>}
        {error && <div className="alert alert-danger alert-clean py-2 mb-3">{String(error)}</div>}

        <form onSubmit={onSubmit} className="row g-3">
          <div className="col-12">
            <label className="form-label">Course ID</label>
            <input className="form-control" type="number" value={id} onChange={(e) => setId(e.target.value)} />
          </div>

          <div className="col-12">
            <label className="form-label">New Title (optional)</label>
            <input className="form-control" name="title" value={payload.title} onChange={onChange} />
          </div>

          <div className="col-md-6">
            <label className="form-label">New Code (optional, unique)</label>
            <input className="form-control" name="code" value={payload.code} onChange={onChange} />
          </div>

          <div className="col-md-6">
            <label className="form-label">New Year (optional)</label>
            <input className="form-control" type="number" name="year" value={payload.year} onChange={onChange} />
          </div>

          <div className="col-md-6">
            <label className="form-label">New Seats (optional)</label>
            <input className="form-control" type="number" name="seats_available" value={payload.seats_available} onChange={onChange} />
          </div>

          <div className="col-md-6">
            <label className="form-label">New Instructor (optional)</label>
            <div className="d-flex gap-2">
              <select className="form-select" name="instructor_id" value={payload.instructor_id} onChange={onChange}>
                <option value="">(no change)</option>
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
            <button className="btn btn-brand">Update</button>
            <button
              type="button"
              className="btn btn-soft"
              onClick={() => setPayload({ title: "", code: "", year: "", seats_available: "", instructor_id: "" })}
            >
              Clear
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}