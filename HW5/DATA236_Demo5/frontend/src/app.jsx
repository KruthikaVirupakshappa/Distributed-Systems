import React, { useState } from "react";
import Home from "./pages/Home";
import CreateCourse from "./pages/CreateCourse";
import UpdateCourse from "./pages/UpdateCourse";
import Instructors from "./pages/Instructors";

export default function App() {
  const [tab, setTab] = useState("home");

  const goTo = (nextTab) => setTab(nextTab);

  return (
    <div className="container py-4 app-shell">
      <div className="hero mb-3">
        <div className="d-flex align-items-start justify-content-between flex-wrap gap-2">
          <div>
            <h2 className="brand-title mb-1">Course Manager</h2>
            <p className="brand-subtitle">Simple UI for managing instructors and courses.</p>
          </div>

          <div className="d-flex align-items-center gap-2">
            <span className="badge badge-soft"></span>
            <span className="badge badge-soft"></span>
          </div>
        </div>

        <div className="mt-3">
          <ul className="nav nav-pills gap-2">
            <li className="nav-item">
              <button className={`nav-link ${tab === "home" ? "active" : ""}`} onClick={() => goTo("home")}>
                Courses
              </button>
            </li>
            <li className="nav-item">
              <button className={`nav-link ${tab === "create" ? "active" : ""}`} onClick={() => goTo("create")}>
                Create Course
              </button>
            </li>
            <li className="nav-item">
              <button className={`nav-link ${tab === "update" ? "active" : ""}`} onClick={() => goTo("update")}>
                Update Course
              </button>
            </li>
            <li className="nav-item">
              <button className={`nav-link ${tab === "instructors" ? "active" : ""}`} onClick={() => goTo("instructors")}>
                Instructors
              </button>
            </li>
          </ul>
        </div>
      </div>

      {tab === "home" && <Home />}
      {tab === "create" && <CreateCourse goTo={goTo} />}
      {tab === "update" && <UpdateCourse />}
      {tab === "instructors" && <Instructors />}

      <div className="mt-4 footer-note">
        
      </div>
    </div>
  );
}