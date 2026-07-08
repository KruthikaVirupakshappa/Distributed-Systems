import React, { useState } from "react";
import Home from "./pages/Home";
import CreateBook from "./pages/CreateBook";
import UpdateBook from "./pages/UpdateBook";
import Authors from "./pages/Authors";

export default function App() {
  const [tab, setTab] = useState("home");

  const goTo = (nextTab) => setTab(nextTab);

  return (
    <div className="container py-4 app-shell">
      <div className="hero mb-3">
        <div className="d-flex align-items-start justify-content-between flex-wrap gap-2">
          <div>
            <h2 className="brand-title mb-1">Library Management System</h2>
            <p className="brand-subtitle">Simple UI for managing authors and books.</p>
          </div>

          <div className="d-flex align-items-center gap-2">
            <span className="badge badge-soft"></span>
            <span className="badge badge-soft"></span>
          </div>
        </div>

        <div className="mt-3">
          <ul className="nav nav-pills gap-2">
            <li className="nav-item">
              <button
                className={`nav-link ${tab === "home" ? "active" : ""}`}
                onClick={() => goTo("home")}
              >
                Books
              </button>
            </li>

            <li className="nav-item">
              <button
                className={`nav-link ${tab === "create" ? "active" : ""}`}
                onClick={() => goTo("create")}
              >
                Create Book
              </button>
            </li>

            <li className="nav-item">
              <button
                className={`nav-link ${tab === "update" ? "active" : ""}`}
                onClick={() => goTo("update")}
              >
                Update Book
              </button>
            </li>

            <li className="nav-item">
              <button
                className={`nav-link ${tab === "authors" ? "active" : ""}`}
                onClick={() => goTo("authors")}
              >
                Authors
              </button>
            </li>
          </ul>
        </div>
      </div>

      {tab === "home" && <Home />}
      {tab === "create" && <CreateBook goTo={goTo} />}
      {tab === "update" && <UpdateBook />}
      {tab === "authors" && <Authors />}

      <div className="mt-4 footer-note"></div>
    </div>
  );
}