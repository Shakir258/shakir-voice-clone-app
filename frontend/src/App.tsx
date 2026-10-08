import { NavLink, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { VoiceProfiles } from "./pages/VoiceProfiles";
import { History } from "./pages/History";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <div className="app-nav-brand">My Voice Studio</div>
        <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
          Dashboard
        </NavLink>
        <NavLink to="/voices" className={({ isActive }) => (isActive ? "active" : "")}>
          Voice Profiles
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => (isActive ? "active" : "")}>
          History
        </NavLink>
        <NavLink to="/settings" className={({ isActive }) => (isActive ? "active" : "")}>
          Settings
        </NavLink>
      </nav>
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
