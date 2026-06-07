import React from 'react';
import { mockParticipants, mockMeetings } from '../mockData';
import { Link } from 'react-router-dom';
import { Clock, CheckCircle, AlertCircle, Users } from 'lucide-react';

export default function Dashboard() {
  const totalMeetings = mockMeetings.length;
  const activeParticipants = mockParticipants.length;
  
  // Calculate commitments
  const allCommitments = mockMeetings.flatMap(m => m.commitments);
  const pending = allCommitments.filter(c => c.status === 'Pending').length;
  const overdue = allCommitments.filter(c => c.status === 'Overdue').length;

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Meeting Insights</h1>
        <p className="page-subtitle">Overview of your community interactions and pending actions.</p>
      </div>

      <div className="grid-4" style={{ marginBottom: '32px' }}>
        <div className="glass-panel stat-card">
          <div className="stat-label">Total Meetings</div>
          <div className="stat-value">{totalMeetings}</div>
          <Clock size={24} style={{ position: 'absolute', right: '24px', top: '24px', opacity: 0.2 }} />
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-label">Active Participants</div>
          <div className="stat-value">{activeParticipants}</div>
          <Users size={24} style={{ position: 'absolute', right: '24px', top: '24px', opacity: 0.2 }} />
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-label">Pending Actions</div>
          <div className="stat-value" style={{ color: 'var(--warning)' }}>{pending}</div>
          <AlertCircle size={24} style={{ position: 'absolute', right: '24px', top: '24px', opacity: 0.2, color: 'var(--warning)' }} />
        </div>
        <div className="glass-panel stat-card">
          <div className="stat-label">Overdue Commitments</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>{overdue}</div>
          <AlertCircle size={24} style={{ position: 'absolute', right: '24px', top: '24px', opacity: 0.2, color: 'var(--danger)' }} />
        </div>
      </div>

      <div className="grid-2">
        <div className="glass-panel">
          <h3 style={{ marginTop: 0, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={20} color="var(--accent)" /> Recent Participants
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {mockParticipants.map(p => (
              <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '12px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                <img src={p.avatar} alt={p.name} style={{ width: '48px', height: '48px', borderRadius: '50%' }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>{p.name}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{p.role}</div>
                </div>
                <Link to={`/participant/${p.id}`} className="btn">View Profile</Link>
                <Link to={`/prep/${p.id}`} className="btn btn-primary">Prepare</Link>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel">
          <h3 style={{ marginTop: 0, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={20} color="var(--danger)" /> Action Tracker
          </h3>
          <div className="timeline">
            {allCommitments.map(c => (
              <div className="timeline-item" key={c.id}>
                <div className="timeline-dot" style={{ background: c.status === 'Overdue' ? 'var(--danger)' : c.status === 'Completed' ? 'var(--success)' : 'var(--warning)', boxShadow: 'none' }}></div>
                <div className="timeline-content">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div className="timeline-title">{c.task}</div>
                    <span className={`badge ${c.status.toLowerCase()}`}>{c.status}</span>
                  </div>
                  <div className="timeline-date">Due: {c.dueDate}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
