import { createContext, useContext, useState, useEffect } from "react";
import client from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("auth_token");
    const savedUser = localStorage.getItem("user");

    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user");
      }
    }
    setIsLoading(false);
  }, []);

  /**
   * Login — throws a descriptive error if the user doesn't exist
   * or credentials are wrong, so the calling component can display it.
   */
  async function login(email, password) {
    try {
      const response = await client.post("/api/v1/auth/login", { email, password });
      const { access_token, user: returnedUser } = response.data;

      localStorage.setItem("auth_token", access_token);
      localStorage.setItem("user", JSON.stringify(returnedUser));
      setToken(access_token);
      setUser(returnedUser);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 401 || status === 404) {
        throw new Error(
          detail || "No account found with this email. Please sign up first."
        );
      }
      throw new Error(detail || err.message || "Login failed. Please try again.");
    }
  }

  /**
   * Signup — throws a descriptive error if the email is already taken
   * or validation fails.
   */
  async function signup(name, email, password) {
    try {
      const response = await client.post("/api/v1/auth/signup", { name, email, password });
      const { access_token, user: returnedUser } = response.data;

      localStorage.setItem("auth_token", access_token);
      localStorage.setItem("user", JSON.stringify(returnedUser));
      setToken(access_token);
      setUser(returnedUser);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;

      if (status === 409) {
        throw new Error(
          detail || "An account with this email already exists. Please sign in."
        );
      }
      if (status === 422) {
        // Pydantic validation error
        const validationErrors = err.response?.data?.detail;
        if (Array.isArray(validationErrors)) {
          const msgs = validationErrors.map((e) => e.msg).join(". ");
          throw new Error(msgs);
        }
        throw new Error("Please check your inputs and try again.");
      }
      throw new Error(detail || err.message || "Signup failed. Please try again.");
    }
  }

  function logout() {
    // Clear user-scoped conversation history before wiping user
    if (user?.id) {
      localStorage.removeItem(`zeus_conversations_${user.id}`);
    }
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
  }

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated, isLoading, login, signup, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}