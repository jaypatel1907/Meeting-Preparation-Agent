import React from 'react';
import { useParams } from 'react-router-dom';
import { mockParticipants, mockMeetings } from '../mockData';
import { Calendar, MessageSquare, AlertTriangle, Lightbulb } from 'lucide-react';

export default function ParticipantProfile() {
  const { id } = useParams();
  const participant = mockParticipants.find(p => p.id === id) || mockParticipants[0];
  const meetings = mockMeetings.filter(m => m.participantId === participant.id).sort((a, b) => new Date(b.date) - new Date(a.date));

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <img src={participant.avatar} alt={participant.name} style={{ width: '80px', height: '80px', borderRadius: '50%', border: '2px solid var(--accent)' }} />
        <div>
          <h1 className="page-title">{participant.name}'s Memory Profile</h1>
          <p className="page-subtitle">{participant.role}</p>
        </div>
      </div>

      <div className="grid-2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className="glass-panel">
            <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}><Lightbulb size={20} color="var(--warning)" /> Intelligence Profile</h3>
            
            <div style={{ marginBottom: '16px' }}>
              <div className="form-label">Interests & Expertise</div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                {participant.profile.interests.map(i => <span key={i} className="badge" style={{ background: 'rgba(59,130,246,0.1)', color: 'var(--accent)', border: '1px solid rgba(59,130,246,0.3)' }}>{i}</span>)}
                {participant.profile.skills.map(i => <span key={i} className="badge" style={{ background: 'rgba(16,185,129,0.1)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.3)' }}>{i}</span>)}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div className="form-label">Communication Style</div>
              <p style={{ margin: '8px 0 0 0', fontSize: '0.95rem' }}>{participant.profile.communicationStyle}</p>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div className="form-label">Contribution History</div>
              <p style={{ margin: '8px 0 0 0', fontSize: '0.95rem' }}>{participant.profile.contributionHistory}</p>
            </div>
            
            <div>
              <div className="form-label">Recurring Concerns</div>
              <div style={{ padding: '12px', background: 'rgba(239,68,68,0.1)', borderLeft: '3px solid var(--danger)', borderRadius: '4px', marginTop: '8px', fontSize: '0.95rem' }}>
                {participant.profile.recurringConcerns}
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
             <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}><AlertTriangle size={20} /> Active Risks</h3>
             <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--text-muted)' }}>
               {meetings.flatMap(m => m.commitments).filter(c => c.status === 'Overdue').map(c => (
                 <li key={c.id} style={{ marginBottom: '8px' }}>Overdue: {c.task}</li>
               ))}
               <li>Long period since last direct follow-up on health concern.</li>
             </ul>
          </div>

        </div>

        <div>
          <div className="glass-panel">
            <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}><Calendar size={20} color="var(--accent)" /> Relationship Timeline</h3>
            <div className="timeline">
              {meetings.map(m => (
                <div className="timeline-item" key={m.id}>
                  <div className="timeline-dot"></div>
                  <div className="timeline-content">
                    <div className="timeline-date">{new Date(m.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric'})}</div>
                    <div className="timeline-title">{m.topic}</div>
                    <p className="timeline-desc">{m.notes}</p>
                    {m.commitments.length > 0 && (
                      <div style={{ marginTop: '12px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>Commitments Made</div>
                        {m.commitments.map(c => (
                          <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                            <span>• {c.task}</span>
                            <span className={`badge ${c.status.toLowerCase()}`}>{c.status}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
