import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { icons } from "./icons.jsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: icons.grid, end: true },
  { to: "/contacts", label: "Contacts", icon: icons.users },
  { to: "/templates", label: "Templates", icon: icons.fileText },
  { to: "/campaigns", label: "Campaigns", icon: icons.megaphone },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const initials = (user?.email?.[0] || "?").toUpperCase();

  useEffect(() => {
    const match = navItems.find((item) =>
      item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)
    );
    const section = match ? match.label : "Campaign";
    document.title = `${section} · Email Automation`;
    setNavOpen(false); // close the mobile drawer whenever the route changes
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <header className="mobile-topbar">
        <button
          className="mobile-nav-toggle"
          onClick={() => setNavOpen(true)}
          aria-label="Open menu"
        >
          {icons.menu}
        </button>
        <span className="brand-word" style={{ fontSize: 14 }}>
          Email <span className="brand-word-accent">Automation</span>
        </span>
      </header>

      {navOpen && <div className="sidebar-scrim" onClick={() => setNavOpen(false)} />}

      <aside className={`sidebar ${navOpen ? "open" : ""}`}>
        <div className="brand-lockup">
          <span className="brand-mark">{icons.logoMark}</span>
          <span className="brand-word">
            Email <span className="brand-word-accent">Automation</span>
          </span>
          <button
            className="mobile-nav-close"
            onClick={() => setNavOpen(false)}
            aria-label="Close menu"
          >
            {icons.x}
          </button>
        </div>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
        <div style={{ marginTop: "auto", paddingTop: 20 }}>
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initials}</div>
            <div className="sidebar-email">{user?.email}</div>
          </div>
          <button className="logout" onClick={logout}>
            {icons.logout}
            <span>Log out</span>
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}