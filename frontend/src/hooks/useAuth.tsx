import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { authApi, setAccessToken } from '../api/client';
import type { User, AuthConfig } from '../types';

interface AuthContextType {
  user: User | null;
  config: AuthConfig | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    try {
      const [configRes, userRes] = await Promise.all([
        authApi.getConfig(),
        authApi.getMe().catch(() => null),
      ]);
      setConfig(configRes.data);
      if (userRes) {
        setUser(userRes.data);
      } else {
        setUser(null);
      }
    } catch {
      setConfig(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const token = params.get('token');

    if (token) {
      setAccessToken(token);
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    refresh();
  }, []);

  const login = async () => {
    try {
      const response = await authApi.loginStart();
      const { authorization_url, state, nonce, code_verifier } = response.data;

      sessionStorage.setItem('oauth_state', state);
      sessionStorage.setItem('oauth_nonce', nonce);
      sessionStorage.setItem('oauth_code_verifier', code_verifier);

      window.location.href = authorization_url;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      const response = await authApi.logout();
      setAccessToken(null);
      setUser(null);
      window.location.href = response.data.logout_url;
    } catch (error) {
      console.error('Logout failed:', error);
      setAccessToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, config, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}