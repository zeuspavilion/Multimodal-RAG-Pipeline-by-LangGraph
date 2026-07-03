import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        {/* Brand header */}
        <div className="auth-brand">
          <div className="auth-brand-logo">Z</div>
        </div>

        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-subtitle">
          Sign in to continue to your conversations
        </p>

        {/* Error toast */}
        {error && (
          <div className="auth-error" role="alert">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="8" cy="8" r="7" />
              <line x1="8" y1="5" x2="8" y2="9" />
              <circle cx="8" cy="11.5" r="0.5" fill="currentColor" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label htmlFor="login-email" className="auth-label">Email</label>
            <input
              id="login-email"
              type="email"
              required
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError(""); }}
              placeholder="you@example.com"
              className="auth-input"
              autoComplete="email"
              disabled={isSubmitting}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="login-password" className="auth-label">Password</label>
            <input
              id="login-password"
              type="password"
              required
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              placeholder="••••••••"
              className="auth-input"
              autoComplete="current-password"
              disabled={isSubmitting}
            />
          </div>

          <button
            id="login-submit"
            type="submit"
            className={`auth-button ${isSubmitting ? "auth-button-loading" : ""}`}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="auth-spinner-wrapper">
                <span className="auth-spinner" />
                <span>Signing in…</span>
              </span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <p className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="auth-link">
            Create one →
          </Link>
        </p>
      </div>
    </div>
  );
}
