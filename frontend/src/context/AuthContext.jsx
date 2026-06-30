import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { login as apiLogin, register as apiRegister, logout as apiLogout, getUser } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem("auth_token"));
  const [loading, setLoading] = useState(true);

  const isAuthenticated = !!token && !!user;

  // Load user on mount if token exists
  useEffect(() => {
    const username = localStorage.getItem("auth_username");
    if (token && username) {
      getUser(username)
        .then((data) => {
          setUser(data.data || data);
        })
        .catch(() => {
          // Token expired or invalid
          localStorage.removeItem("auth_token");
          localStorage.removeItem("auth_username");
          setToken(null);
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(async (username, password) => {
    const data = await apiLogin(username, password);
    const authToken = data.token || data.access_token || data.data?.token || "";
    if (authToken) {
      localStorage.setItem("auth_token", authToken);
      setToken(authToken);
    }
    localStorage.setItem("auth_username", username);
    // Try to fetch user, fallback to basic info
    try {
      const userData = await getUser(username);
      setUser(userData.data || userData);
    } catch {
      setUser({ username });
    }
    return data;
  }, []);

  const registerUser = useCallback(async (username, email, password) => {
    const data = await apiRegister(username, email, password);
    // Auto-login after register
    const authToken = data.token || data.access_token || data.data?.token || "";
    if (authToken) {
      localStorage.setItem("auth_token", authToken);
      setToken(authToken);
    }
    localStorage.setItem("auth_username", username);
    try {
      const userData = await getUser(username);
      setUser(userData.data || userData);
    } catch {
      setUser({ username, email });
    }
    return data;
  }, []);

  const logout = useCallback(async () => {
    // Fire-and-forget: call backend to invalidate JWT
    apiLogout();
    // Clear local state immediately
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_username");
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated, loading, login, register: registerUser, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
