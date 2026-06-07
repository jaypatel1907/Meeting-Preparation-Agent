import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { mockParticipants, mockMeetings } from '../mockData';
import { BrainCircuit, Loader2, CheckSquare, AlertTriangle, MessageCircle, List } from 'lucide-react';

export default function MeetingPrep() {
  const { id } = useParams();
  const participant = mockParticipants.find(p => p.id === id) || mockParticipants[0];
  const meetings = mockMeetings.filter(m => m.participantId === participant.id);
  
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [brief, setBrief] = useState(null);

  const generateBrief = () => {
    setLoading(true);
    setBrief(null);
    setLoadingStep(1); // Fetching memory
    
    setTimeout(() => {
      setLoadingStep(2); // Analyzing with LLM
      
      setTimeout(() => {
        setLoading(false);
        // Generate mock AI response based on historical data
        const overdue = meetings.flatMap(m => m.commitments).filter(c => c.status === 'Overdue');
        const pending = meetings.flatMap(m => m.commitments).filter(c => c.status === 'Pending');
        
        setBrief({
          summary: `You have an active technical relationship with ${participant.name}. They are highly engaged in open source but recently faced some personal health issues and technical blockers with Vercel.`,
          agenda: [
            `Check in on their recovery from the flu.`,
            `Provide the updated .env template to unblock their Vercel deployment.`,
            `Review Architecture changes in PR #42.`,
            `Discuss timeline for HackBaroda integration.`
          ],
          risks: overdue.map(c => `Overdue commitment: ${c.task}`),
          starters: [
            `"Hey ${participant.name}, how are you feeling? Did you recover from the flu?"`,
            `"I know you were blocked on the Vercel deployment, let's fix that first."`
          ],
          commitments: [...overdue, ...pending]
        });
      }, 1500);
    }, 1500);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Smart Meeting Prep</h1>
        <p className="page-subtitle">Powered by Hindsight Memory & Groq LLM</p>
      </div>

      {!loading && !brief && (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px 20px' }}>
          <img src={participant.avatar} alt={participant.name} style={{ width: '80px', height: '80px', borderRadius: '50%', marginBottom: '16px' }} />
          <h2>Generate Prep Brief for {participant.name}</h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto 32px auto' }}>
            The AI will retrieve all past meeting notes, extract pending commitments, and generate a customized agenda.
          </p>
          <button className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '1.1rem' }} onClick={generateBrief}>
            <BrainCircuit size={20} /> Generate Brief
          </button>
        </div>
      )}

      {loading && (
        <div className="glass-panel loader-container">
          <div className="spinner"></div>
          <h3 style={{ margin: 0 }}>
            {loadingStep === 1 ? 'Retrieving historical context from Hindsight...' : 'Synthesizing agenda with Groq LLM...'}
          </h3>
          <div style={{ width: '300px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '10px', overflow: 'hidden' }}>
            <div style={{ width: loadingStep === 1 ? '50%' : '90%', height: '100%', background: 'var(--accent)', transition: 'width 1.5s ease' }}></div>
          </div>
        </div>
      )}

      {brief && !loading && (
        <div className="grid-2">
          {/* Left Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div className="glass-panel" style={{ borderTop: '4px solid var(--accent)' }}>
              <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <BrainCircuit size={20} color="var(--accent)" /> AI Relationship Summary
              </h3>
              <p style={{ margin: 0, lineHeight: 1.6, fontSize: '1.05rem' }}>{brief.summary}</p>
            </div>

            <div className="glass-panel">
              <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <List size={20} color="var(--accent)" /> Recommended Agenda
              </h3>
              <ul style={{ margin: 0, paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {brief.agenda.map((item, i) => (
                  <li key={i} style={{ fontSize: '1.05rem' }}>{item}</li>
                ))}
              </ul>
            </div>

            <div className="glass-panel">
              <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MessageCircle size={20} color="var(--accent)" /> Suggested Conversation Starters
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {brief.starters.map((starter, i) => (
                  <div key={i} style={{ padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', fontStyle: 'italic', borderLeft: '3px solid var(--accent)' }}>
                    {starter}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            
            {brief.commitments.length > 0 && (
              <div className="glass-panel" style={{ border: '1px solid rgba(245,158,11,0.3)' }}>
                <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--warning)' }}>
                  <CheckSquare size={20} /> Pending Commitments
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {brief.commitments.map(c => (
                    <div key={c.id} style={{ padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 500 }}>{c.task}</span>
                      <span className={`badge ${c.status.toLowerCase()}`}>{c.status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {brief.risks.length > 0 && (
              <div className="glass-panel" style={{ border: '1px solid rgba(239,68,68,0.3)' }}>
                <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}>
                  <AlertTriangle size={20} /> Potential Risks Detected
                </h3>
                <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--danger)' }}>
                  {brief.risks.map((risk, i) => (
                    <li key={i} style={{ marginBottom: '8px' }}>{risk}</li>
                  ))}
                  <li>Long period since last direct follow-up on health concern.</li>
                </ul>
              </div>
            )}

            <div className="glass-panel">
               <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '1rem', color: 'var(--text-muted)' }}>Memory Sources Used</h3>
               <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                 <span className="badge" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>Meeting: PR #42 Review</span>
                 <span className="badge" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>Meeting: Health Check</span>
                 <span className="badge" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>Meeting: Deployment Help</span>
               </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
