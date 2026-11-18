import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { api, hasToken, setToken } from './api';

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const HOME_BY_ROLE = { citizen: '/citizen', cmo: '/cmo', officer: '/officer' };

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(hasToken());

  useEffect(() => {
    if (!hasToken()) return;
    api('/api/auth/me').then(setUser).catch(() => setToken(null)).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener('auth:expired', onExpired);
    return () => window.removeEventListener('auth:expired', onExpired);
  }, []);

  const finish = useCallback((res) => {
    setToken(res.access_token);
    setUser(res.user);
    return res.user;
  }, []);

  const login = useCallback(async (email, password) =>
    finish(await api('/api/auth/login', { method: 'POST', json: { email, password } })), [finish]);

  const register = useCallback(async (payload) =>
    finish(await api('/api/auth/register', { method: 'POST', json: payload })), [finish]);

  const logout = useCallback(async () => {
    try { await api('/api/auth/logout', { method: 'POST' }); } catch { /* token may already be invalid */ }
    setToken(null);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading, login, register, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
