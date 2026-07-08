import React from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

export default function Navbar({ auth }) {
  const navigate = useNavigate();

  function guardedNav(path, message) {
    return (e) => {
      if (!auth.loggedIn) {
        e.preventDefault();
        alert(message);
        return;
      }
      navigate(path);
    };
  }

  return (
    <header className="navbar">
      <Link className="brand" to="/">
        <span className="brand-badge" />
        Book Management
      </Link>

      <nav className="navlinks">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Home
        </NavLink>

        <a
          href="/create"
          onClick={guardedNav("/create", "Please login first to add a book.")}
          className={auth.loggedIn ? "" : "disabled-link"}
          aria-disabled={!auth.loggedIn}
        >
          Add Book
        </a>

        <a
          href="/update"
          onClick={guardedNav("/update", "Please login first to update a book.")}
          className={auth.loggedIn ? "" : "disabled-link"}
          aria-disabled={!auth.loggedIn}
        >
          Update Book
        </a>

        <a
          href="/delete"
          onClick={guardedNav("/delete", "Please login first to delete a book.")}
          className={auth.loggedIn ? "" : "disabled-link"}
          aria-disabled={!auth.loggedIn}
        >
          Delete Book
        </a>
      </nav>
    </header>
  );
}
