import { NavLink, Outlet } from "react-router-dom";

export function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1 className="brand-title">Industrial Engineering Copilot</h1>
          <p className="brand-tagline">From Engineering Requirements to Product Decisions</p>
        </div>
        <nav className="app-nav" aria-label="Primary">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : undefined)}>
            Dashboard
          </NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">Phase 1 foundation — product intelligence coming later.</footer>
    </div>
  );
}
