import { Link, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";

import { fetchDevAccessToken } from "../api/client";
import { useAuth } from "../context/AuthContext";

type Props = {
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageShell({ title, description, children }: Props) {
  const { isAuthenticated, login, logout } = useAuth();
  const navigate = useNavigate();

  async function handleDevLogin() {
    try {
      const token = await fetchDevAccessToken();
      login(token);
      navigate("/scout-reports");
    } catch {
      window.alert("Dev login failed. Make sure backend is running.");
    }
  }

  return (
    <div className="page-shell">
      <header className="topbar">
        <h1>StatScout</h1>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/scout-reports">Scout Reports</Link>
          <Link to="/match-analyzer">Match Analyzer</Link>
          {isAuthenticated ? (
            <button onClick={logout} type="button">
              Logout
            </button>
          ) : (
            <button onClick={handleDevLogin} type="button">
              Dev Login
            </button>
          )}
        </nav>
      </header>
      <main>
        <h2>{title}</h2>
        <p>{description}</p>
        {children}
      </main>
    </div>
  );
}
