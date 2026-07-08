import React, { useEffect, useState } from "react";
import { login, logout, me } from "../api/usersApi.js";

export default function LoginBar({ auth, setAuth }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

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

    try {
      await login(email, password);
      const data = await me(); // get user_id from session
      setAuth({ loggedIn: true, userId: data.user_id });
      setEmail("");
      setPassword("");
    } catch (err) {
      alert("Login failed. Check email and password.");
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
    <div className="loginbar compact">
      {auth.loggedIn ? (
        <>
          <div className="loginbar-text">
            ✅ Logged in (User ID <b>{auth.userId}</b>)
          </div>
          <button className="btn danger" onClick={handleLogout}>
            Logout
          </button>
        </>
      ) : (
        <>
          <div className="loginbar-text">🔒 Not logged in</div>

          <form className="loginbar-inline" onSubmit={handleLogin}>
            <input
              className="loginbar-input"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <input
              className="loginbar-input"
              placeholder="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <button className="btn primary" type="submit">
              Login
            </button>
          </form>
        </>
      )}
    </div>
  );
}
