import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import * as api from '../../services/api';
import { toast } from 'react-toastify';

// Async thunks for user management
export const fetchUsers = createAsyncThunk(
  'users/fetchUsers',
  async (_, { rejectWithValue }) => {
    try {
      const users = await api.fetchUsers();
      return users;
    } catch (error) {
      toast.error(`Failed to fetch users: ${error.message}`);
      return rejectWithValue(error.message);
    }
  }
);

export const updateUserRole = createAsyncThunk(
  'users/updateUserRole',
  async ({ userId, role }, { rejectWithValue }) => {
    try {
      const updatedUser = await api.updateUserRoles(userId, [role]);
      toast.success('User role updated successfully!');
      return updatedUser;
    } catch (error) {
      toast.error(`Failed to update user role: ${error.message}`);
      return rejectWithValue(error.message);
    }
  }
);

export const disableUser = createAsyncThunk(
  'users/disableUser',
  async (userId, { rejectWithValue }) => {
    try {
      await api.disableUser(userId);
      toast.success('User disabled successfully!');
      return userId; // Return the ID of the disabled user
    } catch (error) {
      toast.error(`Failed to disable user: ${error.message}`);
      return rejectWithValue(error.message);
    }
  }
);

export const enableUser = createAsyncThunk(
  'users/enableUser',
  async (userId, { rejectWithValue }) => {
    try {
      await api.enableUser(userId);
      toast.success('User enabled successfully!');
      return userId; // Return the ID of the enabled user
    } catch (error) {
      toast.error(`Failed to enable user: ${error.message}`);
      return rejectWithValue(error.message);
    }
  }
);

const userSlice = createSlice({
  name: 'users',
  initialState: {
    users: [],
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.users = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(updateUserRole.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateUserRole.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.users.findIndex(user => user.id === action.payload.id);
        if (index !== -1) {
          state.users[index] = action.payload;
        }
      })
      .addCase(updateUserRole.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(disableUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(disableUser.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.users.findIndex(user => user.id === action.payload);
        if (index !== -1) {
          state.users[index].disabled = true; // Assuming a 'disabled' field
        }
      })
      .addCase(disableUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(enableUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(enableUser.fulfilled, (state, action) => {
        state.loading = false;
        const index = state.users.findIndex(user => user.id === action.payload);
        if (index !== -1) {
          state.users[index].disabled = false; // Assuming a 'disabled' field
        }
      })
      .addCase(enableUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export default userSlice.reducer;