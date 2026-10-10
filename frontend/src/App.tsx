import { useState, useEffect } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { VoiceProfiles } from "./pages/VoiceProfiles";
import { History } from "./pages/History";
import { Settings } from "./pages/Settings";

export default function App() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  return (
    <div className="app-shell">
      {/* Mobile Top Header */}
      <header className="mobile-app-header">
        <div className="mobile-brand-group">
          <span className="mobile-brand-logo">🎙️</span>
          <div className="mobile-brand-text">
            <span className="mobile-brand-title">Voice Studio</span>
            <span className="mobile-brand-badge">Hindi AI</span>
          </div>
        </div>
        <button
          type="button"
          className="mobile-hamburger-btn"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? "✕" : "☰"}
        </button>
      </header>

      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div
          className="mobile-nav-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Navigation (Sidebar on Desktop, Slide Drawer on Mobile) */}
      <nav className={`app-nav ${mobileMenuOpen ? "mobile-nav-open" : ""}`}>
        <div className="app-nav-brand-container">
          <div className="app-nav-brand">
            <span className="nav-brand-icon">🎙️</span>
            <span>Hindi Voice Studio</span>
          </div>
          <span className="nav-brand-badge">AI Studio Pro</span>
        </div>

        <div className="nav-links-group">
          <NavLink
            to="/"
            end
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="nav-icon">⚡</span>
            <span className="nav-label">Studio Dashboard</span>
          </NavLink>
          <NavLink
            to="/voices"
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="nav-icon">🎧</span>
            <span className="nav-label">100 Hindi Voices</span>
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="nav-icon">📜</span>
            <span className="nav-label">Generation History</span>
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
            onClick={() => setMobileMenuOpen(false)}
          >
            <span className="nav-icon">⚙️</span>
            <span className="nav-label">Engine Settings</span>
          </NavLink>
        </div>

        <div className="app-nav-footer">
          <div className="nav-footer-status">
            <span className="nav-status-dot"></span>
            <span>Neural Engine Ready</span>
          </div>
          <span className="nav-version-tag">v2.5 High-Definition</span>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/voices" element={<VoiceProfiles />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}

