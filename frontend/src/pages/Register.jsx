import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { icons } from "../components/icons.jsx";
import AuthBrandPanel from "../components/AuthBrandPanel.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-shell">
      <AuthBrandPanel />

      <div className="auth-form-panel">
        <div className="auth-card">
          <h2>Create account</h2>
          {error && <div className="alert error">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="field">
              <label>Email</label>
              <div className="input-icon-wrap">
                <span className="input-icon">{icons.mail}</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  required
                />
              </div>
            </div>
            <div className="field">
              <label>Password (min 8 characters)</label>
              <div className="input-icon-wrap">
                <span className="input-icon">{icons.lock}</span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  tabIndex={-1}
                >
                  {showPassword ? icons.eyeOff : icons.eye}
                </button>
              </div>
            </div>
            <button className="btn" type="submit" disabled={busy} style={{ width: "100%" }}>
              {busy ? (
                <span className="btn-busy-content">
                  {icons.spinner}
                  Creating...
                </span>
              ) : (
                "Create account"
              )}
            </button>
          </form>
          <p className="muted" style={{ marginTop: 16, fontSize: 13 }}>
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}