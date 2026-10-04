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
            Sales
          </NavLink>
          <NavLink to="/catalog" className={({ isActive }) => (isActive ? "active" : undefined)}>
            Catalog
          </NavLink>
          <NavLink
            to="/validation"
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            Validation
          </NavLink>
          <NavLink
            to="/quotation"
            className={({ isActive }) => (isActive ? "active" : undefined)}
          >
            Quotations
          </NavLink>
          <NavLink to="/rfq" className={({ isActive }) => (isActive ? "active" : undefined)}>
            RFQ Extract
          </NavLink>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        Phase 5A recommendation — RFQ to validated quotation with sales decision control.
      </footer>
    </div>
  );
}
