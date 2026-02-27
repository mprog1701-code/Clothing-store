import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { saveTokens, clearTokens, getAccessToken, getRefreshToken } from './tokenStorage';
import { me, login as apiLogin, register as apiRegister, logout as apiLogout } from '../api';

const AuthCtx = createContext({
  accessToken: '',
  refreshToken: '',
  user: null,
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

  useEffect(() => {
    let mounted = true;
    (async () => {
      const access = await getAccessToken();
      const refresh = await getRefreshToken();
      if (!mounted) return;
      setAccessToken(access || '');
      setRefreshToken(refresh || '');
      if (access) {
        try {
          const u = await me();
          if (!mounted) return;
          setUser(u || null);
        } catch {
          setUser(null);
        }
      } else {
        setUser(null);
      }
      setIsHydrating(false);
    })();
    return () => { mounted = false; };
  }, []);

  const login = async (username, password) => {
    const u = await apiLogin(username, password);
    const access = await getAccessToken();
    const refresh = await getRefreshToken();
    setAccessToken(access || '');
    setRefreshToken(refresh || '');
    setUser(u || null);
    return u;
  };

  const register = async (payload) => {
    const u = await apiRegister(payload);
    const access = await getAccessToken();
    const refresh = await getRefreshToken();
    setAccessToken(access || '');
    setRefreshToken(refresh || '');
    setUser(u || null);
    return u;
  };

  const logout = async () => {
    try { await apiLogout(); } catch {}
    await clearTokens();
    setAccessToken('');
    setRefreshToken('');
    setUser(null);
  };

  const value = useMemo(() => ({
    accessToken, refreshToken, user, isHydrating, login, register, logout, setUser
  }), [accessToken, refreshToken, user, isHydrating]);

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function useAuth() {
  return useContext(AuthCtx);
}
