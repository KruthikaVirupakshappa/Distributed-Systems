import React, { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchCourses, deleteCourse } from "../features/courses/coursesSlice";
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
  const { items, loading, error } = useSelector((s) => s.courses);

  const [instructors, setInstructors] = useState([]);
  const [instError, setInstError] = useState("");

  const instructorMap = useMemo(() => {
    const m = new Map();
    instructors.forEach((i) => m.set(i.id, `${i.first_name} ${i.last_name}`));
    return m;
  }, [instructors]);

  const loadInstructors = async () => {
    setInstError("");
    try {
      const res = await api.get("/instructors?skip=0&limit=200");
      setInstructors(res.data);
    } catch (err) {
      setInstError(`Instructor fetch failed → ${getErrText(err)}  (GET /instructors)`);
      setInstructors([]);
    }
  };

  const refreshAll = async () => {
    dispatch(fetchCourses());
    await loadInstructors();
  };

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="card card-clean">
      <div className="card-header d-flex align-items-center justify-content-between">
        <div>
          <div className="fw-bold">Courses</div>
          <div className="small-hint">View, refresh, and delete courses.</div>
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
            <div className="small mt-1">If this looks like a network error, confirm backend is running on :8006.</div>
          </div>
        )}

        {instError && <div className="alert alert-warning alert-clean py-2 mb-3">{instError}</div>}

        <div className="table-responsive table-clean">
          <table className="table table-sm mb-0">
            <thead>
              <tr>
                <th style={{ width: 70 }}>ID</th>
                <th>Title</th>
                <th style={{ width: 130 }}>Code</th>
                <th style={{ width: 90 }}>Year</th>
                <th style={{ width: 90 }}>Seats</th>
                <th style={{ width: 200 }}>Instructor</th>
                <th style={{ width: 110 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {items.map((c) => {
                const name = instructorMap.get(c.instructor_id);
                return (
                  <tr key={c.id}>
                    <td className="fw-semibold">{c.id}</td>
                    <td>{c.title}</td>
                    <td>
                      <span className="badge badge-soft">{c.code}</span>
                    </td>
                    <td>{c.year}</td>
                    <td>{c.seats_available}</td>
                    <td>{name ? name : `ID: ${c.instructor_id}`}</td>
                    <td>
                      <button className="btn btn-outline-danger btn-sm" onClick={() => dispatch(deleteCourse(c.id))}>
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}

              {items.length === 0 && (
                <tr>
                  <td colSpan="7" className="text-center text-muted py-4">
                    No courses yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="small-hint mt-2">
          
        </div>
      </div>
    </div>
  );
}