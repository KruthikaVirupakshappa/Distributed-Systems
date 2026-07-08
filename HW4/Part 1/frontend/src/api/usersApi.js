import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
});

export async function fetchBooks() {
  const res = await api.get("/books");
  return res.data;
}

export async function fetchBookById(id) {
  const res = await api.get(`/books/${id}`);
  return res.data;
}

export async function createBook(payload) {
  const res = await api.post("/books", payload);
  return res.data;
}

export async function updateBook(id, payload) {
  const res = await api.put(`/books/${id}`, payload);
  return res.data;
}

export async function deleteBook(id) {
  const res = await api.delete(`/books/${id}`);
  return res.data;
}

export async function login(email, password) {
  // login uses query param for demo simplicity
  const res = await api.post("/auth/login", { email, password });
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