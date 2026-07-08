import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
});

export async function fetchUsers() {
  const res = await api.get("/users");
  return res.data;
}

export async function fetchUserById(id) {
  const res = await api.get(`/users/${id}`);
  return res.data;
}

export async function createUser(payload) {
  const res = await api.post("/users", payload);
  return res.data;
}

export async function updateUser(id, payload) {
  const res = await api.put(`/users/${id}`, payload);
  return res.data;
}

export async function deleteUser(id) {
  const res = await api.delete(`/users/${id}`);
  return res.data;
}

export async function login(userId) {
  // login uses query param for demo simplicity
  const res = await api.post(`/auth/login?user_id=${userId}`);
  return res.data;
}

export async function logout() {
  const res = await api.post("/auth/logout");
  return res.data;
}

export async function me() {
  const res = await api.get("/auth/me");
  return res.data;
}