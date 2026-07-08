import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import LoginBar from "./components/LoginBar.jsx";

import Home from "./pages/Home.jsx";
import CreateUser from "./pages/createUser.jsx";
import UpdateUser from "./pages/updateUser.jsx";
import DeleteUser from "./pages/deleteUser.jsx";

import { fetchUsers, createUser, updateUser, deleteUser } from "./api/usersApi.js";

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

  // Users data
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch users only when logged in
  useEffect(() => {
    (async () => {
      if (!auth.loggedIn) {
        setUsers([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const data = await fetchUsers();
        setUsers(data);
      } catch (e) {
        console.error("fetchUsers failed:", e);
        // If session expired, backend returns 401; UI will show not logged in after next /auth/me check.
      } finally {
        setLoading(false);
      }
    })();
  }, [auth.loggedIn]);

  // Create (props)
  async function onAdd(newUser) {
    const created = await createUser(newUser);
    setUsers((prev) => [...prev, created]);
    navigate("/");
  }

  // Update (props)
  async function onUpdate(id, updatedUser) {
    const updated = await updateUser(id, updatedUser);
    setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)));
    navigate("/");
  }

  // Delete (props)
  async function onDelete(id) {
    await deleteUser(id);
    setUsers((prev) => prev.filter((u) => u.id !== id));
    navigate("/");
  }

  return (
    <div className="container">
      <Navbar auth={auth} />

      {/* Login session demo UI */}
      <LoginBar auth={auth} setAuth={setAuth} />

      <Routes>
        <Route path="/" element={<Home users={users} loading={loading} auth={auth} />} />
        <Route path="/create" element={<RequireAuth auth={auth}> <CreateUser onAdd={onAdd} auth={auth} /></RequireAuth> }/>
        <Route path="/update/:id" element={<UpdateUser onUpdate={onUpdate} auth={auth} />} />
        <Route path="/delete/:id" element={<DeleteUser onDelete={onDelete} auth={auth} />} />
      </Routes>
    </div>
  );
}