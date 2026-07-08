import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/axios";

const errMsg = (err, fallback) => {
  if (err.response?.data?.detail) return err.response.data.detail;
  if (err.message) return `${fallback}: ${err.message}`;
  return fallback;
};

export const fetchAuthors = createAsyncThunk(
  "authors/fetchAuthors",
  async (_, thunkAPI) => {
    try {
      const res = await api.get("/authors");
      return res.data;
    } catch (err) {
      return thunkAPI.rejectWithValue(errMsg(err, "Failed to fetch authors"));
    }
  }
);

export const createAuthor = createAsyncThunk(
  "authors/createAuthor",
  async (payload, thunkAPI) => {
    try {
      const res = await api.post("/authors", payload);
      return res.data;
    } catch (err) {
      return thunkAPI.rejectWithValue(errMsg(err, "Failed to create author"));
    }
  }
);

export const updateAuthor = createAsyncThunk(
  "authors/updateAuthor",
  async ({ id, payload }, thunkAPI) => {
    try {
      const res = await api.put(`/authors/${id}`, payload);
      return res.data;
    } catch (err) {
      return thunkAPI.rejectWithValue(errMsg(err, "Failed to update author"));
    }
  }
);

export const deleteAuthor = createAsyncThunk(
  "authors/deleteAuthor",
  async (id, thunkAPI) => {
    try {
      await api.delete(`/authors/${id}`);
      return id;
    } catch (err) {
      return thunkAPI.rejectWithValue(errMsg(err, "Failed to delete author"));
    }
  }
);

const authorsSlice = createSlice({
  name: "authors",
  initialState: {
    items: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchAuthors.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAuthors.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
      })
      .addCase(fetchAuthors.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      .addCase(createAuthor.fulfilled, (state, action) => {
        state.items.push(action.payload);
      })
      .addCase(createAuthor.rejected, (state, action) => {
        state.error = action.payload;
      })

      .addCase(updateAuthor.fulfilled, (state, action) => {
        const idx = state.items.findIndex((a) => a.id === action.payload.id);
        if (idx !== -1) state.items[idx] = action.payload;
      })
      .addCase(updateAuthor.rejected, (state, action) => {
        state.error = action.payload;
      })

      .addCase(deleteAuthor.fulfilled, (state, action) => {
        state.items = state.items.filter((a) => a.id !== action.payload);
      })
      .addCase(deleteAuthor.rejected, (state, action) => {
        state.error = action.payload;
      });
  },
});

export default authorsSlice.reducer;