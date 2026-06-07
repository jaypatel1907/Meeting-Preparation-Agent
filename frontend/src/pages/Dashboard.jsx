import { Link } from 'react-router-dom';
import { mockParticipants, mockMeetings } from '../mockData';

export default function Dashboard() {
  const allCommitments = mockMeetings.flatMap(m => m.commitments);
  const pending  = allCommitments.filter(c => c.status === 'Pending').length;
  const overdue  = allCommitments.filter(c => c.status === 'Overdue').length;
  const completed = allCommitments.filter(c => c.status === 'Completed').length;

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your community meeting overview, powered by persistent memory.</p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Meetings</div>
          <div className="stat-value blue">{mockMeetings.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active Participants</div>
          <div className="stat-value green">{mockParticipants.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Actions</div>
          <div className="stat-value yellow">{pending}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Overdue Commitments</div>
          <div className="stat-value red">{overdue}</div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid-2">

        {/* Participants */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
              Participants
            </div>
            <span className="badge badge-blue">{mockParticipants.length} Active</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {mockParticipants.map(p => {
              const meetings = mockMeetings.filter(m => m.participantId === p.id);
              const pOverdue = meetings.flatMap(m => m.commitments).filter(c => c.status === 'Overdue').length;
              return (
                <div className="participant-row" key={p.id}>
                  <img src={p.avatar} alt={p.name} className="p-avatar-lg" />
                  <div className="p-info">
                    <div className="p-name">{p.name}</div>
                    <div className="p-role">{p.role}</div>
                  </div>
                  {pOverdue > 0 && <span className="badge badge-red">{pOverdue} overdue</span>}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <Link to={`/participant/${p.id}`} className="btn btn-ghost">Timeline</Link>
                    <Link to={`/prep/${p.id}`} className="btn btn-primary">Prep →</Link>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Commitment Tracker */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
              Commitment Tracker
            </div>
          </div>
          <div>
            {allCommitments.map(c => {
              const badgeClass = c.status === 'Overdue' ? 'badge-red' : c.status === 'Completed' ? 'badge-green' : 'badge-yellow';
              return (
                <div className="commitment-item" key={c.id}>
                  <span className="commitment-task">{c.task}</span>
                  <span className={`badge ${badgeClass}`}>{c.status}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Activity Timeline */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-header">
            <div className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>
              Recent Meeting Activity
            </div>
          </div>
          <div className="timeline">
            {[...mockMeetings].reverse().map(m => {
              const participant = mockParticipants.find(p => p.id === m.participantId);
              return (
                <div className="timeline-item" key={m.id}>
                  <div className="timeline-left">
                    <div className="t-dot"></div>
                    <div className="t-line"></div>
                  </div>
                  <div className="t-content">
                    <div className="t-date">{new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} · {participant?.name}</div>
                    <div className="t-title">{m.topic}</div>
                    <div className="t-desc">{m.notes.length > 120 ? m.notes.slice(0, 120) + '...' : m.notes}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
