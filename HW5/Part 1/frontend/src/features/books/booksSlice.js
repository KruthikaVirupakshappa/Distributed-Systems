import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/axios";

const errMsg = (err, fallback) => {
  if (err.response?.data?.detail) return err.response.data.detail;
  if (err.message) return `${fallback}: ${err.message}`;
  return fallback;
};

export const fetchBooks = createAsyncThunk("books/fetchBooks", async (_, thunkAPI) => {
  try {
    const res = await api.get("/books");
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to fetch books"));
  }
});

export const createBook = createAsyncThunk("books/createBook", async (payload, thunkAPI) => {
  try {
    const res = await api.post("/books", payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to create book"));
  }
});

export const updateBook = createAsyncThunk("books/updateBook", async ({ id, payload }, thunkAPI) => {
  try {
    const res = await api.put(`/books/${id}`, payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to update book"));
  }
});

export const deleteBook = createAsyncThunk("books/deleteBook", async (id, thunkAPI) => {
  try {
    await api.delete(`/books/${id}`);
    return id;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to delete book"));
  }
});

const booksSlice = createSlice({
  name: "books",
  initialState: { items: [], loading: false, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchBooks.pending, (s) => {
        s.loading = true;
        s.error = null;
      })
      .addCase(fetchBooks.fulfilled, (s, a) => {
        s.loading = false;
        s.items = a.payload;
      })
      .addCase(fetchBooks.rejected, (s, a) => {
        s.loading = false;
        s.error = a.payload;
      })

      .addCase(createBook.fulfilled, (s, a) => {
        s.items.push(a.payload);
      })
      .addCase(createBook.rejected, (s, a) => {
        s.error = a.payload;
      })

      .addCase(updateBook.fulfilled, (s, a) => {
        const idx = s.items.findIndex((b) => b.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
      })
      .addCase(updateBook.rejected, (s, a) => {
        s.error = a.payload;
      })

      .addCase(deleteBook.fulfilled, (s, a) => {
        s.items = s.items.filter((b) => b.id !== a.payload);
      })
      .addCase(deleteBook.rejected, (s, a) => {
        s.error = a.payload;
      });
  },
});

export default booksSlice.reducer;