import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { saveTokens, clearTokens, getAccessToken, getRefreshToken } from './tokenStorage';
import { me, login as apiLogin, register as apiRegister, logout as apiLogout } from '../api';

const AuthCtx = createContext({
  accessToken: '',
  refreshToken: '',
  user: null,
  isAuthenticated: false,
  isHydrating: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  setUser: () => {},
});

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [user, setUser] = useState(null);
  const [isHydrating, setIsHydrating] = useState(true);

  const syncAuthState = async (fallbackUser = null) => {
    const access = await getAccessToken();
    const refresh = await getRefreshToken();
    setAccessToken(access || '');
    setRefreshToken(refresh || '');
    if (!access) {
      setUser(null);
      return null;
    }
    let resolvedUser = fallbackUser;
    if (!resolvedUser) {
      try {
        resolvedUser = await me();
      } catch {
        resolvedUser = null;
      }
    }
    setUser(resolvedUser || null);
    return resolvedUser || null;
  };

  useEffect(() => {
    let mounted = true;
    (async () => {
      if (!mounted) return;
      await syncAuthState();
      if (!mounted) return;
      setIsHydrating(false);
    })();
    return () => { mounted = false; };
  }, []);

  const login = async (username, password) => {
    const u = await apiLogin(username, password);
    return syncAuthState(u || null);
  };

  const register = async (payload) => {
    const result = await apiRegister(payload);
    if (result?.requires_verification || result?.requires_otp) {
      await syncAuthState(null);
      return result;
    }
    return syncAuthState(result || null);
  };

  const logout = async () => {
    try { await apiLogout(); } catch {}
    await clearTokens();
    setAccessToken('');
    setRefreshToken('');
    setUser(null);
  };

  const isAuthenticated = !!accessToken && !!user;
  const value = useMemo(() => ({
    accessToken, refreshToken, user, isAuthenticated, isHydrating, login, register, logout, setUser
  }), [accessToken, refreshToken, user, isAuthenticated, isHydrating]);

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  return useContext(AuthCtx);
}
