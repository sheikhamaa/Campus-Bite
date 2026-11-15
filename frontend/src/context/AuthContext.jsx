import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import api, { setAuthToken } from '../api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('campusbite_token'));
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('campusbite_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setAuthToken(token);
    if (token) {
      localStorage.setItem('campusbite_token', token);
    } else {
      localStorage.removeItem('campusbite_token');
    }
    setIsLoading(false);
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('campusbite_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('campusbite_user');
    }
  }, [user]);

  const login = async (payload) => {
    const { data } = await api.post('/api/auth/login', payload);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const register = async (payload) => {
    const { data } = await api.post('/api/auth/register', payload);
    setToken(null);
    setUser(null);
    return data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(
    () => ({ token, user, isLoading, login, register, logout, setUser }),
    [token, user, isLoading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
