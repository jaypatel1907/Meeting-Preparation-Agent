import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { mockParticipants, mockMeetings } from '../mockData';

const BRIEFS = {
  p1: {
    summary: "You have an active, technically-focused relationship with Alex. They are a strong open-source contributor who recently faced a flu and a Vercel deployment blocker. Two commitments are unresolved — address these early to maintain trust.",
    agenda: [
      "Check in on flu recovery — start on a personal note.",
      "Provide the updated .env template to unblock Vercel deployment.",
      "Review architecture changes in PR #42 together.",
      "Discuss HackBaroda project integration timeline."
    ],
    risks: [
      "Overdue: PR #42 review was promised on May 18 — still pending.",
      "Overdue: .env template was not sent by June 6 deadline.",
      "No health follow-up since May 28 — consider acknowledging."
    ],
    starters: [
      "\"Hey Alex, how are you feeling now? Hope the flu's behind you!\"",
      "\"I have the updated .env template ready — let's fix the Vercel issue first.\""
    ],
    commitments: [
      { id: 'c1', task: 'Review PR #42', status: 'Pending' },
      { id: 'c2', task: 'Send .env template', status: 'Overdue' }
    ],
    sources: ['Meeting: PR #42 Review (May 18)', 'Meeting: Health Check (May 28)', 'Meeting: Deployment Help (Jun 5)']
  },
  p2: {
    summary: "Sarah is a dedicated mentor focused on community growth and preventing burnout. She is well-organized and prefers video calls. Your last interaction was about the mentorship program structure.",
    agenda: [
      "Review progress on the approved mentorship budget.",
      "Get an update on the new 1-on-1 session structure.",
      "Discuss participant engagement metrics from last workshop.",
      "Plan next monthly workshop agenda together."
    ],
    risks: [
      "No major risks detected.",
      "Monitor for mentor burnout — Sarah frequently manages multiple responsibilities."
    ],
    starters: [
      "\"Sarah, how has the new mentorship structure been working so far?\"",
      "\"Did the approved budget help with the session planning?\""
    ],
    commitments: [
      { id: 'c3', task: 'Approve mentorship budget', status: 'Completed' }
    ],
    sources: ['Meeting: Mentorship Program Launch (May 20)']
  },
  p3: {
    summary: "John is a results-driven event organizer managing sponsorships and logistics for hackathons. He prefers short, action-oriented communication. He has no open commitments currently.",
    agenda: [
      "Review sponsor retention strategy for next event.",
      "Discuss budget constraints and potential solutions.",
      "Confirm logistics plan for upcoming hackathon.",
      "Align on marketing and promotion timeline."
    ],
    risks: [
      "No overdue commitments detected.",
      "Sponsor budget constraints were mentioned as a recurring concern — come prepared with solutions."
    ],
    starters: [
      "\"John, quick update — what's the sponsor status for the next event?\"",
      "\"Have the budget constraints been resolved since last time?\""
    ],
    commitments: [],
    sources: ['Memory: Role & Profile Analysis', 'General: Event Organizer Context']
  }
};

export default function MeetingPrep() {
  const { id } = useParams();
  const participant = mockParticipants.find(p => p.id === id) || mockParticipants[0];

  const [step, setStep] = useState('idle'); // idle | loading | done
  const [loadLabel, setLoadLabel] = useState('');
  const [progress, setProgress] = useState(0);
  const brief = BRIEFS[participant.id] || BRIEFS['p1'];

  const runGenerate = () => {
    setStep('loading');
    setProgress(20);
    setLoadLabel('Connecting to Hindsight memory layer...');

    setTimeout(() => {
      setProgress(55);
      setLoadLabel('Retrieving historical context for ' + participant.name + '...');
    }, 1000);

    setTimeout(() => {
      setProgress(80);
      setLoadLabel('Synthesizing meeting brief with Groq LLM...');
    }, 2200);

    setTimeout(() => {
      setProgress(100);
      setLoadLabel('Brief ready!');
    }, 3200);

    setTimeout(() => {
      setStep('done');
    }, 3600);
  };

  const reset = () => setStep('idle');

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Smart Meeting Prep</h1>
        <p className="page-subtitle">AI-powered brief generated from Hindsight persistent memory + Groq LLM.</p>
      </div>

      {/* Participant selector */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
        {mockParticipants.map(p => (
          <Link key={p.id} to={`/prep/${p.id}`} onClick={reset}
            className={`btn ${participant.id === p.id ? 'btn-primary' : 'btn-ghost'}`}>
            <img src={p.avatar} alt={p.name} className="p-avatar" style={{ width: '18px', height: '18px' }} />
            {p.name}
          </Link>
        ))}
      </div>

      {/* IDLE */}
      {step === 'idle' && (
        <div className="card">
          <div className="gen-screen">
            <img src={participant.avatar} alt={participant.name} className="gen-avatar" />
            <div className="gen-title">Prepare for Meeting with {participant.name}</div>
            <p className="gen-desc">
              Click Generate to retrieve {participant.name}'s full memory from Hindsight —
              including past meetings, open commitments, and preferences — then synthesize
              a personalized brief using Groq LLM.
            </p>
            <button className="btn btn-primary btn-lg" onClick={runGenerate}>
              🧠 Generate Meeting Brief
            </button>
          </div>
        </div>
      )}

      {/* LOADING */}
      {step === 'loading' && (
        <div className="card">
          <div className="loading-box">
            <div className="spinner"></div>
            <div className="loading-title">{loadLabel}</div>
            <div className="loading-sub">Accessing Hindsight memory · Running Groq synthesis</div>
            <div className="progress-bar-wrap">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{progress}%</div>
          </div>
        </div>
      )}

      {/* DONE */}
      {step === 'done' && (
        <div>
          {/* Summary bar */}
          <div className="card" style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '16px', padding: '14px 20px' }}>
            <img src={participant.avatar} alt={participant.name} style={{ width: '40px', height: '40px', borderRadius: '50%' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: '14px' }}>{participant.name} · {participant.role}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Brief generated from {brief.sources.length} memory source(s)</div>
            </div>
            <button className="btn btn-ghost" onClick={reset}>↺ Regenerate</button>
          </div>

          <div className="grid-2">
            {/* LEFT */}
            <div className="col">

              {/* AI Summary */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">🧠 AI Relationship Summary</div>
                  <span className="badge badge-blue">From Memory</span>
                </div>
                <p style={{ fontSize: '13.5px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
                  {brief.summary}
                </p>
              </div>

              {/* Agenda */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">📋 Recommended Agenda</div>
                </div>
                <ol className="agenda-list">
                  {brief.agenda.map((item, i) => (
                    <li key={i} className="agenda-item">
                      <span className="agenda-num">{i + 1}</span>
                      {item}
                    </li>
                  ))}
                </ol>
              </div>

              {/* Conversation Starters */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">💬 Conversation Starters</div>
                </div>
                {brief.starters.map((s, i) => (
                  <div key={i} className="starter-card">{s}</div>
                ))}
              </div>

            </div>

            {/* RIGHT */}
            <div className="col">

              {/* Commitments */}
              {brief.commitments.length > 0 ? (
                <div className="card">
                  <div className="card-header">
                    <div className="card-title">⚠️ Open Commitments to Address</div>
                  </div>
                  {brief.commitments.map(c => {
                    const bc = c.status === 'Overdue' ? 'badge-red' : 'badge-yellow';
                    return (
                      <div className="commitment-item" key={c.id}>
                        <span className="commitment-task">{c.task}</span>
                        <span className={`badge ${bc}`}>{c.status}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="card">
                  <div className="card-header"><div className="card-title">✅ Commitments</div></div>
                  <div className="alert alert-blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                    No open commitments — you're all clear!
                  </div>
                </div>
              )}

              {/* Risks */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">🚨 Risk Detection</div>
                </div>
                {brief.risks.map((r, i) => (
                  <div key={i} className={`alert ${r.includes('No') ? 'alert-blue' : i === 0 ? 'alert-red' : 'alert-yellow'}`}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    {r}
                  </div>
                ))}
              </div>

              {/* Memory Sources */}
              <div className="card">
                <div className="card-header">
                  <div className="card-title">🗂 Memory Sources Used</div>
                  <span className="badge badge-green">Hindsight</span>
                </div>
                <div className="source-tags">
                  {brief.sources.map((s, i) => (
                    <span key={i} className="source-tag">📄 {s}</span>
                  ))}
                </div>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
