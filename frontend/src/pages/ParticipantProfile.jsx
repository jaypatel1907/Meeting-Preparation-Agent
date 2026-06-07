import { useParams, Link } from 'react-router-dom';
import { mockParticipants, mockMeetings } from '../mockData';

export default function ParticipantProfile() {
  const { id } = useParams();
  const participant = mockParticipants.find(p => p.id === id) || mockParticipants[0];
  const meetings = mockMeetings
    .filter(m => m.participantId === participant.id)
    .sort((a, b) => new Date(a.date) - new Date(b.date));

  const allCommitments = meetings.flatMap(m => m.commitments);
  const overdueItems = allCommitments.filter(c => c.status === 'Overdue');
  const pendingItems = allCommitments.filter(c => c.status === 'Pending');

  return (
    <div>
      {/* Profile Header */}
      <div className="profile-header">
        <img src={participant.avatar} alt={participant.name} className="profile-avatar" />
        <div className="profile-meta">
          <h1>{participant.name}</h1>
          <p>{participant.role}</p>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
          <Link to={`/prep/${participant.id}`} className="btn btn-primary btn-lg">Generate Meeting Prep →</Link>
        </div>
      </div>

      {/* Participant Selector */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        {mockParticipants.map(p => (
          <Link key={p.id} to={`/participant/${p.id}`}
            className={`btn ${participant.id === p.id ? 'btn-primary' : 'btn-ghost'}`}>
            <img src={p.avatar} alt={p.name} className="p-avatar" style={{ width: '18px', height: '18px' }} />
            {p.name}
          </Link>
        ))}
      </div>

      <div className="grid-2">
        {/* Left: Profile + Commitments */}
        <div className="col">

          {/* Memory Profile */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">🧠 Memory Profile</div>
              <span className="badge badge-blue">AI Generated</span>
            </div>

            <div className="info-row">
              <div className="info-label">Interests & Expertise</div>
              <div className="tag-group">
                {participant.profile.interests.map(i => <span key={i} className="badge badge-blue">{i}</span>)}
                {participant.profile.skills.map(i => <span key={i} className="badge badge-purple">{i}</span>)}
              </div>
            </div>

            <div className="divider"></div>

            <div className="info-row">
              <div className="info-label">Communication Style</div>
              <div className="info-value">{participant.profile.communicationStyle}</div>
            </div>

            <div className="info-row">
              <div className="info-label">Contribution History</div>
              <div className="info-value">{participant.profile.contributionHistory}</div>
            </div>

            <div className="divider"></div>

            <div className="info-row">
              <div className="info-label">Recurring Concerns</div>
              <div className="alert alert-yellow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                {participant.profile.recurringConcerns}
              </div>
            </div>
          </div>

          {/* Commitments */}
          {(overdueItems.length > 0 || pendingItems.length > 0) && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">📋 Open Commitments</div>
              </div>
              {overdueItems.map(c => (
                <div className="commitment-item" key={c.id}>
                  <span className="commitment-task">{c.task}</span>
                  <span className="badge badge-red">Overdue</span>
                </div>
              ))}
              {pendingItems.map(c => (
                <div className="commitment-item" key={c.id}>
                  <span className="commitment-task">{c.task}</span>
                  <span className="badge badge-yellow">Pending</span>
                </div>
              ))}
            </div>
          )}

          {/* Risks */}
          {overdueItems.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">⚠️ Risk Detection</div>
              </div>
              <div className="alert alert-red">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {overdueItems.length} overdue commitment(s) may damage trust. Resolve before next meeting.
              </div>
              <div className="alert alert-yellow">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                Long period since last health follow-up — personal touch recommended.
              </div>
            </div>
          )}
        </div>

        {/* Right: Timeline */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🕐 Relationship Timeline</div>
            <span className="badge badge-purple">{meetings.length} meetings</span>
          </div>
          <div className="timeline">
            {meetings.map((m, idx) => {
              const hasOverdue = m.commitments.some(c => c.status === 'Overdue');
              const hasPending = m.commitments.some(c => c.status === 'Pending');
              const dotClass = hasOverdue ? 'red' : hasPending ? 'yellow' : '';
              return (
                <div className="timeline-item" key={m.id}>
                  <div className="timeline-left">
                    <div className={`t-dot ${dotClass}`}></div>
                    <div className="t-line"></div>
                  </div>
                  <div className="t-content">
                    <div className="t-date">
                      {new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </div>
                    <div className="t-title">{m.topic}</div>
                    <div className="t-desc">{m.notes}</div>
                    {m.commitments.length > 0 && (
                      <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {m.commitments.map(c => {
                          const bc = c.status === 'Overdue' ? 'badge-red' : c.status === 'Completed' ? 'badge-green' : 'badge-yellow';
                          return <span key={c.id} className={`badge ${bc}`}>{c.status}: {c.task}</span>;
                        })}
                      </div>
                    )}
                    {m.events.map(e => (
                      <span key={e} className="badge badge-blue" style={{ marginTop: '8px', display: 'inline-flex' }}>📌 {e}</span>
                    ))}
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
