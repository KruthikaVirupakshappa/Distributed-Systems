import React, { useEffect, useState } from "react";
import { login, logout, me } from "../api/usersApi.js";

export default function LoginBar({ auth, setAuth }) {
  const [userIdInput, setUserIdInput] = useState("");

  // On refresh, check if cookie session exists
  useEffect(() => {
    (async () => {
      try {
        const data = await me();
        setAuth({ loggedIn: true, userId: data.user_id });
      } catch {
        setAuth({ loggedIn: false, userId: null });
      }
    })();
  }, [setAuth]);

  async function handleLogin(e) {
    e.preventDefault();
    const id = Number(userIdInput);
    if (!id) return;

    try {
      const res = await login(id);
      setAuth({ loggedIn: true, userId: res.user_id });
      setUserIdInput("");
    } catch (err) {
      alert("Login failed. Make sure that user_id exists in DB.");
      console.error(err);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setAuth({ loggedIn: false, userId: null });
    }
  }

  return (
    <div className="loginbar">
      {auth.loggedIn ? (
        <>
          <div className="loginbar-text">
            ✅ Logged in as <b>User ID {auth.userId}</b>
          </div>
          <button className="btn danger" onClick={handleLogout}>
            Logout
          </button>
        </>
      ) : (
        <form className="loginbar-form" onSubmit={handleLogin}>
          <div className="loginbar-text">
            🔒 Not logged in
          </div>

          <input
            className="loginbar-input"
            placeholder="Enter user_id (e.g. 1)"
            value={userIdInput}
            onChange={(e) => setUserIdInput(e.target.value)}
          />

          <button className="btn primary" type="submit">
            Login
          </button>
        </form>
      )}
    </div>
  );
}