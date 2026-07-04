import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, auth } from "@/lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [googleEnabled, setGoogleEnabled] = useState(false);

  const refresh = useCallback(async () => {
    if (!auth.getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
    } catch {
      auth.clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    api.get("/auth/google/status").then(r => setGoogleEnabled(!!r.data?.enabled)).catch(() => {});
  }, [refresh]);

  const loginWithToken = async (token) => {
    auth.setToken(token);
    await refresh();
  };

  const logout = async () => {
    try { await api.post("/auth/logout"); } catch { /* ignore */ }
    auth.clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, refresh, setUser, logout, loginWithToken, googleEnabled }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
