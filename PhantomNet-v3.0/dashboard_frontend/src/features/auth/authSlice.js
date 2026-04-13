import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as api from '../../services/api';
import { toast } from 'react-toastify';

// Async thunk for user login
export const loginUser = createAsyncThunk(
  'auth/loginUser',
  async ({ username, password, totpCode, recoveryCode }, { rejectWithValue }) => {
    try {
      const response = await api.login(username, password, totpCode, recoveryCode);
      toast.success('Login successful!');
      return response;
    } catch (error) {
      toast.error(error.message);
      return rejectWithValue(error.message);
    }
  }
);

// Async thunk for fetching user details
export const fetchUser = createAsyncThunk(
  'auth/fetchUser',
  async (_, { rejectWithValue }) => {
    try {
      const user = await api.getMe();
      return user;
    } catch (error) {
      // Don't show toast for fetchUser errors, as it might happen on initial load if not authenticated
      return rejectWithValue(error.message);
    }
  }
);

// Async thunk for user logout
export const logoutUser = createAsyncThunk(
  'auth/logoutUser',
  async (_, { rejectWithValue }) => {
    try {
      await api.logout();
      toast.success('Logged out successfully!');
      return true;
    } catch (error) {
      toast.error(error.message);
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    twoFaRequired: false,
    challengeId: null,
  },
  reducers: {
    setTwoFaRequired: (state, action) => {
      state.twoFaRequired = action.payload.required;
      state.challengeId = action.payload.challengeId;
    },
    clearAuthError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login User
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.twoFaRequired = false;
        state.challengeId = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        if (action.payload === '2FA_REQUIRED') {
          state.twoFaRequired = true;
          state.error = 'Two-factor authentication is required.';
        } else {
          state.error = action.payload;
        }
      })
      // Fetch User
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = !!action.payload;
        state.user = action.payload;
        state.error = null;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.error = action.payload;
      })
      // Logout User
      .addCase(logoutUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(logoutUser.fulfilled, (state) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.error = null;
        state.twoFaRequired = false;
        state.challengeId = null;
      })
      .addCase(logoutUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { setTwoFaRequired, clearAuthError } = authSlice.actions;

export default authSlice.reducer;