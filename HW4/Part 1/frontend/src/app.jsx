import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import LoginBar from "./components/LoginBar.jsx";

import Home from "./pages/Home.jsx";
import CreateBook from "./pages/createBook.jsx";
import UpdateBook from "./pages/updateBook.jsx";
import DeleteBook from "./pages/deleteBook.jsx";

import { fetchBooks, createBook, updateBook, deleteBook } from "./api/usersApi.js";

export default function App() {
  const navigate = useNavigate();

  function RequireAuth({ auth, children }) {
    if (!auth.loggedIn) {
      return (
        <div className="card">
          <div className="card-header">
            <div className="page-title">Login Required</div>
          </div>
          <div className="card-body">
            <div className="notice">Please login to access this page.</div>
          </div>
        </div>
      );
    }
    return children;
  }

  // Auth state (cookie session is checked inside LoginBar via /auth/me)
  const [auth, setAuth] = useState({ loggedIn: false, userId: null });

  // Books data
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch books only when logged in
  useEffect(() => {
    (async () => {
      if (!auth.loggedIn) {
        setBooks([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await fetchBooks();
        setBooks(data);
      } catch (e) {
        console.error("fetchBooks failed:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [auth.loggedIn]);

  // Create (props)
  async function onAdd(newBook) {
    const created = await createBook(newBook);
    setBooks((prev) => [...prev, created]);
    navigate("/");
  }

  // Update (props)
  async function onUpdate(id, updatedBook) {
    const updated = await updateBook(id, updatedBook);
    setBooks((prev) => prev.map((b) => (b.id === id ? updated : b)));
    navigate("/");
  }

  // Delete (props)
  async function onDelete(id) {
    await deleteBook(id);
    setBooks((prev) => prev.filter((b) => b.id !== id));
    navigate("/");
  }

  return (
    <div className="container">
      <Navbar auth={auth} />

      <LoginBar auth={auth} setAuth={setAuth} />

      <Routes>
        <Route path="/" element={<Home books={books} loading={loading} auth={auth} />} />

        <Route
          path="/create"
          element={
            <RequireAuth auth={auth}>
              <CreateBook onAdd={onAdd} auth={auth} />
            </RequireAuth>
          }
        />

        <Route
          path="/update/:id"
          element={
            <RequireAuth auth={auth}>
              <UpdateBook onUpdate={onUpdate} auth={auth} />
            </RequireAuth>
          }
        />

        <Route
          path="/delete/:id"
          element={
            <RequireAuth auth={auth}>
              <DeleteBook onDelete={onDelete} auth={auth} />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  );
}
