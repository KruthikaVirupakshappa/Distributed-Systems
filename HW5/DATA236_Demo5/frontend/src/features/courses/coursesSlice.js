import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { api } from "../../api/axios";

const errMsg = (err, fallback) => {
  if (err.response?.data?.detail) return err.response.data.detail;
  // Network-style errors (backend down, wrong port, CORS preflight failure)
  if (err.message) return `${fallback}: ${err.message}`;
  return fallback;
};

export const fetchCourses = createAsyncThunk("courses/fetchCourses", async (_, thunkAPI) => {
  try {
    const res = await api.get("/courses");
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to fetch courses"));
  }
});

export const createCourse = createAsyncThunk("courses/createCourse", async (payload, thunkAPI) => {
  try {
    const res = await api.post("/courses", payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to create course"));
  }
});

export const updateCourse = createAsyncThunk("courses/updateCourse", async ({ id, payload }, thunkAPI) => {
  try {
    const res = await api.put(`/courses/${id}`, payload);
    return res.data;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to update course"));
  }
});

export const deleteCourse = createAsyncThunk("courses/deleteCourse", async (id, thunkAPI) => {
  try {
    await api.delete(`/courses/${id}`);
    return id;
  } catch (err) {
    return thunkAPI.rejectWithValue(errMsg(err, "Failed to delete course"));
  }
});

const coursesSlice = createSlice({
  name: "courses",
  initialState: { items: [], loading: false, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCourses.pending, (s) => { s.loading = true; s.error = null; })
      .addCase(fetchCourses.fulfilled, (s, a) => { s.loading = false; s.items = a.payload; })
      .addCase(fetchCourses.rejected, (s, a) => { s.loading = false; s.error = a.payload; })

      .addCase(createCourse.fulfilled, (s, a) => { s.items.push(a.payload); })
      .addCase(createCourse.rejected, (s, a) => { s.error = a.payload; })

      .addCase(updateCourse.fulfilled, (s, a) => {
        const idx = s.items.findIndex((c) => c.id === a.payload.id);
        if (idx !== -1) s.items[idx] = a.payload;
      })
      .addCase(updateCourse.rejected, (s, a) => { s.error = a.payload; })

      .addCase(deleteCourse.fulfilled, (s, a) => {
        s.items = s.items.filter((c) => c.id !== a.payload);
      })
      .addCase(deleteCourse.rejected, (s, a) => { s.error = a.payload; });
  }
});

export default coursesSlice.reducer;