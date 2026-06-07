import { BrowserRouter, Routes, Route, NavLink, useLocation } from 'react-router-dom';
import { mockParticipants } from './mockData';
import Dashboard from './pages/Dashboard';
import ParticipantProfile from './pages/ParticipantProfile';
import MeetingPrep from './pages/MeetingPrep';

function Sidebar() {
  const location = useLocation();

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">🧠</div>
        <div className="brand-name">Meet<span>Prep</span> AI</div>
      </div>

      {/* Nav */}
      <div className="sidebar-section">
        <div className="sidebar-section-label">Navigation</div>
        <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          Dashboard
        </NavLink>
        <NavLink to="/prep/p1" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          Smart Meeting Prep
        </NavLink>
      </div>

      {/* Participants */}
      <div className="sidebar-section">
        <div className="sidebar-section-label">Participants</div>
        {mockParticipants.map(p => (
          <NavLink
            key={p.id}
            to={`/participant/${p.id}`}
            className={({ isActive }) => `participant-link ${isActive ? 'active' : ''}`}
          >
            <img src={p.avatar} alt={p.name} className="p-avatar" />
            <span>{p.name}</span>
          </NavLink>
        ))}
      </div>

      {/* Memory Status */}
      <div className="memory-status">
        <div className="status-dot"></div>
        Hindsight Memory Active
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="layout">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/participant/:id" element={<ParticipantProfile />} />
            <Route path="/prep/:id" element={<MeetingPrep />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
