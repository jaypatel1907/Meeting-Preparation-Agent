import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, CalendarDays, BrainCircuit } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ParticipantProfile from './pages/ParticipantProfile';
import MeetingPrep from './pages/MeetingPrep';

function Sidebar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <div className="sidebar">
      <div className="sidebar-logo">
        <BrainCircuit size={28} color="#3b82f6" /> MeetPrep AI
      </div>
      <div className="nav-links">
        <Link to="/" className={`nav-item ${isActive('/')}`}><LayoutDashboard size={20} /> Dashboard</Link>
        <Link to="/participant/p1" className={`nav-item ${location.pathname.includes('/participant') ? 'active' : ''}`}><Users size={20} /> Profiles & Timeline</Link>
        <Link to="/prep/p1" className={`nav-item ${location.pathname.includes('/prep') ? 'active' : ''}`}><CalendarDays size={20} /> Smart Meeting Prep</Link>
      </div>
      
      <div style={{ marginTop: 'auto', padding: '16px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '12px', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Memory Engine</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem', fontWeight: '500' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 10px #10b981' }}></div>
          Hindsight Active
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Sidebar />
        <div className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/participant/:id" element={<ParticipantProfile />} />
            <Route path="/prep/:id" element={<MeetingPrep />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
