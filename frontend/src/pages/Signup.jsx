import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Signup() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    // Client-side validation
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setIsSubmitting(true);

    try {
      await signup(name, email, password);
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

        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">
          Get started with Zeus — it only takes a moment
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
            <label htmlFor="signup-name" className="auth-label">Full name</label>
            <input
              id="signup-name"
              type="text"
              required
              value={name}
              onChange={(e) => { setName(e.target.value); setError(""); }}
              placeholder="Jane Doe"
              className="auth-input"
              autoComplete="name"
              disabled={isSubmitting}
            />
          </div>

          <div className="auth-field">
            <label htmlFor="signup-email" className="auth-label">Email</label>
            <input
              id="signup-email"
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
            <label htmlFor="signup-password" className="auth-label">Password</label>
            <input
              id="signup-password"
              type="password"
              required
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              placeholder="Min. 8 characters"
              className="auth-input"
              autoComplete="new-password"
              disabled={isSubmitting}
            />
          </div>

          <button
            id="signup-submit"
            type="submit"
            className={`auth-button ${isSubmitting ? "auth-button-loading" : ""}`}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span className="auth-spinner-wrapper">
                <span className="auth-spinner" />
                <span>Creating account…</span>
              </span>
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login" className="auth-link">
            Sign in →
          </Link>
        </p>
      </div>
    </div>
  );
}
