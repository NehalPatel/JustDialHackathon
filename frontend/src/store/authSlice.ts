import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import api from '../services/api';

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  isActive: boolean;
  profile?: {
    firstName: string;
    lastName: string;
    avatar?: string | null;
  };
}

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  status: 'idle',
  error: null,
};

export const registerUser = createAsyncThunk(
  'auth/register',
  async (
    data: { email: string; password: string; firstName: string; lastName: string },
    { rejectWithValue }
  ) => {
    try {
      const res = await api.post('/auth/register', data);
      return res.data.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.message || 'Registration failed');
    }
  }
);

export const loginUser = createAsyncThunk(
  'auth/login',
  async (data: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const res = await api.post('/auth/login', data);
      return res.data.data;
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.message || 'Login failed');
    }
  }
);

export const fetchProfile = createAsyncThunk('auth/profile', async (_, { rejectWithValue }) => {
  try {
    const res = await api.get('/auth/profile');
    return res.data.data.user as UserProfile;
  } catch (err: any) {
    return rejectWithValue(err.response?.data?.message || 'Failed to load profile');
  }
});

export const refreshTokens = createAsyncThunk(
  'auth/refresh',
  async (refreshToken: string, { rejectWithValue }) => {
    try {
      const res = await api.post('/auth/refresh-token', { refreshToken });
      return res.data.data.tokens as { accessToken: string; refreshToken: string; expiresIn: number };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.message || 'Failed to refresh token');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.status = 'idle';
      state.error = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(registerUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state, action) => {
        const { user, tokens } = action.payload as any;
        state.user = user as UserProfile;
        state.accessToken = tokens.accessToken;
        state.refreshToken = tokens.refreshToken;
        localStorage.setItem('accessToken', tokens.accessToken);
        localStorage.setItem('refreshToken', tokens.refreshToken);
        state.status = 'succeeded';
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as string) || 'Registration failed';
      })
      .addCase(loginUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        const { user, tokens } = action.payload as any;
        state.user = user as UserProfile;
        state.accessToken = tokens.accessToken;
        state.refreshToken = tokens.refreshToken;
        localStorage.setItem('accessToken', tokens.accessToken);
        localStorage.setItem('refreshToken', tokens.refreshToken);
        state.status = 'succeeded';
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as string) || 'Login failed';
      })
      .addCase(fetchProfile.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.user = action.payload as UserProfile;
        state.status = 'succeeded';
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        state.status = 'failed';
        state.error = (action.payload as string) || 'Failed to load profile';
      })
      .addCase(refreshTokens.fulfilled, (state, action) => {
        const tokens = action.payload as any;
        state.accessToken = tokens.accessToken;
        state.refreshToken = tokens.refreshToken;
        localStorage.setItem('accessToken', tokens.accessToken);
        localStorage.setItem('refreshToken', tokens.refreshToken);
      });
  },
});

export const { logout } = authSlice.actions;
export default authSlice.reducer;