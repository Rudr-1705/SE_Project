'use client';

import { useState, useEffect, useRef } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// ── Types ─────────────────────────────────────────────
type User = { id: string; email: string; full_name: string; role: string };
type Project = { id: string; name: string; description: string; use_case: string; status: string; created_at: string };
type Requirement = { id: string; requirement_id: string; statement: string; category: string; priority: string; status: string; confidence: number; is_ambiguous: boolean; is_conflicting: boolean; acceptance_criteria: any[]; applicable_regulations: any[]; risks: any[]; evidence: any[] };
type Message = { role: string; content: string };

// ── API helpers ───────────────────────────────────────
async function api(path: string, opts: { method?: string; body?: any; token?: string; isForm?: boolean } = {}) {
  const headers: Record<string, string> = {};
  if (opts.token) headers['Authorization'] = `Bearer ${opts.token}`;
  if (!opts.isForm) headers['Content-Type'] = 'application/json';
  const config: RequestInit = { method: opts.method || 'GET', headers };
  if (opts.body) config.body = opts.isForm ? opts.body : JSON.stringify(opts.body);
  const res = await fetch(`${API}${path}`, config);
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `Error ${res.status}`); }
  return res.json();
}

// ── Icons (inline SVG) ────────────────────────────────
const Icons = {
  dashboard: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>,
  chat: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>,
  doc: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
  req: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" /></svg>,
  shield: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>,
  check: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  chart: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" /></svg>,
  export: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>,
  audit: <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
};

const priorityColor: Record<string, string> = { critical: 'badge-red', high: 'badge-yellow', medium: 'badge-blue', low: 'badge-green' };
const statusColor: Record<string, string> = { raw: 'badge-purple', extracted: 'badge-blue', analysed: 'badge-yellow', approved: 'badge-green', rejected: 'badge-red', pending_approval: 'badge-yellow' };

// ── Main App ──────────────────────────────────────────
export default function Home() {
  const [page, setPage] = useState('dashboard');
  const [token, setToken] = useState('');
  const [user, setUser] = useState<User | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [sdlc, setSdlc] = useState<any>(null);
  const [artefact, setArtefact] = useState<any>(null);
  const [auditTrail, setAuditTrail] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auth state
  const [email, setEmail] = useState('admin@aifre.com');
  const [password, setPassword] = useState('admin1234');
  const [fullName, setFullName] = useState('Admin User');

  // Interview state
  const [interviewInput, setInterviewInput] = useState('');
  const [interviewProgress, setInterviewProgress] = useState(0);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  // ── Auth ──
  const handleLogin = async () => {
    setLoading(true); setError('');
    try {
      const data = await api('/auth/login', { method: 'POST', body: { email, password } });
      setToken(data.access_token); setUser(data.user);
      const projs = await api('/projects', { token: data.access_token });
      setProjects(projs);
    } catch (e: any) {
      // Try register
      try {
        const data = await api('/auth/register', { method: 'POST', body: { email, password, full_name: fullName, role: 'admin' } });
        setToken(data.access_token); setUser(data.user);
      } catch (e2: any) { setError(e2.message); }
    }
    setLoading(false);
  };

  // ── Project ──
  const createProject = async () => {
    setLoading(true);
    try {
      const proj = await api('/projects', { method: 'POST', token, body: { name: 'Loan Processing System', description: 'Digital loan origination and processing platform with KYC/AML compliance', use_case: 'loan_processing' } });
      setProject(proj);
      setProjects([proj, ...projects]);
      setPage('interview');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Interview ──
  const startInterview = async () => {
    if (!project) return;
    setLoading(true);
    try {
      const data = await api(`/projects/${project.id}/interview/start?stakeholder_role=business_analyst`, { method: 'POST', token });
      setMessages([{ role: 'assistant', content: data.question }]);
      setInterviewProgress(data.progress * 100);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  const sendAnswer = async () => {
    if (!project || !interviewInput.trim()) return;
    const userMsg = interviewInput;
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInterviewInput('');
    setLoading(true);
    try {
      const data = await api(`/projects/${project.id}/interview/answer?answer=${encodeURIComponent(userMsg)}`, { method: 'POST', token });
      setMessages(prev => [...prev, { role: 'assistant', content: data.question }]);
      setInterviewProgress((data.progress || 0) * 100);
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Extraction ──
  const extractRequirements = async () => {
    if (!project) return;
    setLoading(true);
    try {
      const conversationText = messages.map(m => `${m.role}: ${m.content}`).join('\n');
      const data = await api(`/projects/${project.id}/requirements/extract?text=${encodeURIComponent(conversationText)}&source_type=conversation`, { method: 'POST', token });
      setRequirements(data.requirements || []);
      setPage('requirements');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Analysis ──
  const runAnalysis = async () => {
    if (!project) return;
    setLoading(true);
    try {
      const data = await api(`/projects/${project.id}/requirements/analyse`, { method: 'POST', token });
      setAnalysis(data);
      setPage('analysis');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── SDLC ──
  const runSdlc = async () => {
    if (!project) return;
    setLoading(true);
    try {
      const data = await api(`/projects/${project.id}/sdlc/analyse`, { method: 'POST', token });
      setSdlc(data);
      setPage('sdlc');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Artefacts ──
  const generateArtefact = async (type: string) => {
    if (!project) return;
    setLoading(true);
    try {
      const data = await api(`/projects/${project.id}/artefacts/generate?artefact_type=${type}&project_name=${encodeURIComponent(project.name)}`, { method: 'POST', token });
      setArtefact(data);
      setPage('artefacts');
    } catch (e: any) { setError(e.message); }
    setLoading(false);
  };

  // ── Audit ──
  const loadAudit = async () => {
    if (!project) return;
    try {
      const data = await api(`/projects/${project.id}/audit-trail`, { token });
      setAuditTrail(data);
    } catch (e: any) { setError(e.message); }
  };

  // ── Login screen ──
  if (!token) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'linear-gradient(135deg, #0a0f1c 0%, #1a1040 50%, #0a0f1c 100%)' }}>
        <div className="glass-card animate-fade-in" style={{ maxWidth: 420, width: '100%', textAlign: 'center' }}>
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 40, marginBottom: 8 }}>🏦</div>
            <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4, background: 'linear-gradient(135deg, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>AIFRE</h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>AI Financial Requirements Engineering</p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input className="input-field" placeholder="Full Name" value={fullName} onChange={e => setFullName(e.target.value)} />
            <input className="input-field" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
            <input className="input-field" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
            <button className="btn-primary" onClick={handleLogin} disabled={loading} style={{ marginTop: 8 }}>
              {loading ? '⏳ Authenticating...' : '🔐 Login / Register'}
            </button>
          </div>
          {error && <p style={{ color: 'var(--danger)', marginTop: 12, fontSize: 13 }}>{error}</p>}
        </div>
      </div>
    );
  }

  // ── Sidebar ──
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.dashboard },
    { id: 'interview', label: 'Interview', icon: Icons.chat },
    { id: 'requirements', label: 'Requirements', icon: Icons.req },
    { id: 'analysis', label: 'Analysis', icon: Icons.shield },
    { id: 'sdlc', label: 'SDLC Analysis', icon: Icons.chart },
    { id: 'artefacts', label: 'Artefacts', icon: Icons.export },
    { id: 'approvals', label: 'Approvals', icon: Icons.check },
    { id: 'audit', label: 'Audit Trail', icon: Icons.audit },
  ];

  return (
    <div style={{ display: 'flex' }}>
      {/* Sidebar */}
      <div className="sidebar">
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 24, fontWeight: 700, background: 'linear-gradient(135deg, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>🏦 AIFRE</div>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Financial RE Platform</p>
        </div>
        <nav style={{ flex: 1 }}>
          {navItems.map(item => (
            <a key={item.id} className={`sidebar-link ${page === item.id ? 'active' : ''}`} onClick={() => { setPage(item.id); if (item.id === 'audit') loadAudit(); }} style={{ cursor: 'pointer' }}>
              {item.icon} {item.label}
            </a>
          ))}
        </nav>
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 16 }}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{user?.full_name}</div>
          <div className="badge badge-blue" style={{ marginTop: 4 }}>{user?.role}</div>
        </div>
      </div>

      {/* Main content */}
      <div className="main-content">
        {error && <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid var(--danger)', borderRadius: 10, padding: '10px 16px', marginBottom: 16, color: '#f87171', fontSize: 13 }}>⚠️ {error} <button onClick={() => setError('')} style={{ float: 'right', background: 'none', border: 'none', color: '#f87171', cursor: 'pointer' }}>✕</button></div>}

        {/* Dashboard */}
        {page === 'dashboard' && (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>Dashboard</h1>
            <p style={{ color: 'var(--text-muted)', marginBottom: 32 }}>Agentic AI Financial Requirements Engineering</p>

            {!project ? (
              <div className="glass-card" style={{ textAlign: 'center', maxWidth: 500, margin: '60px auto' }}>
                <div style={{ fontSize: 48, marginBottom: 16 }}>🚀</div>
                <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Create Your First Project</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: 24, fontSize: 14 }}>Start with a Loan Processing System to demonstrate the full requirements engineering pipeline.</p>
                <button className="btn-primary" onClick={createProject} disabled={loading}>{loading ? '⏳ Creating...' : '+ Create Loan Processing Project'}</button>
              </div>
            ) : (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
                  {[
                    { label: 'Requirements', value: requirements.length, color: '#60a5fa' },
                    { label: 'Analysed', value: analysis ? '✓' : '—', color: '#34d399' },
                    { label: 'SDLC', value: sdlc?.display_name || '—', color: '#a78bfa' },
                    { label: 'Artefacts', value: artefact ? '1+' : '—', color: '#fbbf24' },
                  ].map((stat, i) => (
                    <div key={i} className="glass-card" style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 28, fontWeight: 700, color: stat.color }}>{stat.value}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{stat.label}</div>
                    </div>
                  ))}
                </div>

                <div className="glass-card" style={{ marginBottom: 16 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>📋 {project.name}</h3>
                  <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 12 }}>{project.description}</p>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <span className="badge badge-blue">{project.use_case}</span>
                    <span className="badge badge-green">{project.status}</span>
                  </div>
                </div>

                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Workflow Steps</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                  {[
                    { step: '1', label: 'Stakeholder Interview', action: () => { setPage('interview'); startInterview(); }, done: messages.length > 0 },
                    { step: '2', label: 'Extract Requirements', action: extractRequirements, done: requirements.length > 0 },
                    { step: '3', label: 'Run Analysis Pipeline', action: runAnalysis, done: !!analysis },
                    { step: '4', label: 'SDLC Analysis', action: runSdlc, done: !!sdlc },
                    { step: '5', label: 'Generate SRS', action: () => generateArtefact('srs'), done: !!artefact },
                    { step: '6', label: 'View Audit Trail', action: () => { setPage('audit'); loadAudit(); }, done: auditTrail.length > 0 },
                  ].map((s, i) => (
                    <div key={i} className="glass-card" style={{ cursor: 'pointer', opacity: loading ? 0.6 : 1 }} onClick={() => !loading && s.action()}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 32, height: 32, borderRadius: '50%', background: s.done ? 'var(--success)' : 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 600 }}>{s.done ? '✓' : s.step}</div>
                        <span style={{ fontSize: 14, fontWeight: 500 }}>{s.label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Interview */}
        {page === 'interview' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <h1 style={{ fontSize: 24, fontWeight: 700 }}>💬 Stakeholder Interview</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Adaptive requirements gathering</p>
              </div>
              {messages.length === 0 && <button className="btn-primary" onClick={startInterview} disabled={loading}>{loading ? '⏳' : '▶ Start Interview'}</button>}
              {messages.length > 2 && <button className="btn-secondary" onClick={extractRequirements} disabled={loading}>📥 Extract Requirements</button>}
            </div>

            {interviewProgress > 0 && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                  <span>Interview Progress</span><span>{Math.round(interviewProgress)}%</span>
                </div>
                <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${interviewProgress}%` }} /></div>
              </div>
            )}

            <div className="glass-card" style={{ minHeight: 400, display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 8, paddingBottom: 16 }}>
                {messages.length === 0 && <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: 80 }}>Click "Start Interview" to begin adaptive requirements gathering</div>}
                {messages.map((msg, i) => (
                  <div key={i} className={`chat-bubble ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
                    {msg.content}
                  </div>
                ))}
                {loading && <div className="chat-bubble chat-bubble-ai animate-pulse">🤔 Thinking...</div>}
                <div ref={chatEndRef} />
              </div>
              <div style={{ display: 'flex', gap: 8, borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                <input className="input-field" placeholder="Type your answer..." value={interviewInput} onChange={e => setInterviewInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendAnswer()} />
                <button className="btn-primary" onClick={sendAnswer} disabled={loading || !interviewInput.trim()}>Send</button>
              </div>
            </div>
          </div>
        )}

        {/* Requirements */}
        {page === 'requirements' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <h1 style={{ fontSize: 24, fontWeight: 700 }}>📋 Requirements ({requirements.length})</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Extracted and structured requirements</p>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn-secondary" onClick={runAnalysis} disabled={loading}>🔍 Run Analysis</button>
                <button className="btn-primary" onClick={extractRequirements} disabled={loading}>📥 Re-extract</button>
              </div>
            </div>

            {requirements.length === 0 ? (
              <div className="glass-card" style={{ textAlign: 'center', padding: 60 }}>
                <p style={{ color: 'var(--text-muted)' }}>No requirements yet. Start an interview or upload a document.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {requirements.map((req, i) => (
                  <div key={i} className="glass-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontWeight: 700, color: 'var(--accent)', fontSize: 13 }}>{req.requirement_id || `REQ-${i+1}`}</span>
                        <span className={`badge ${priorityColor[req.priority] || 'badge-blue'}`}>{req.priority}</span>
                        <span className={`badge ${statusColor[req.status] || 'badge-blue'}`}>{req.status}</span>
                      </div>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Confidence: {((req.confidence || 0) * 100).toFixed(0)}%</span>
                    </div>
                    <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 8 }}>{req.statement}</p>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', fontSize: 12 }}>
                      <span className="badge badge-purple">{req.category}</span>
                      {req.is_ambiguous && <span className="badge badge-yellow">⚠ Ambiguous</span>}
                      {req.is_conflicting && <span className="badge badge-red">⚡ Conflict</span>}
                      {(req.applicable_regulations || []).map((r: any, j: number) => (
                        <span key={j} className="badge badge-blue">{typeof r === 'string' ? r : r.name || r}</span>
                      ))}
                    </div>
                    {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
                      <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(42,53,80,0.5)' }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 4 }}>ACCEPTANCE CRITERIA</div>
                        <ul style={{ fontSize: 13, color: 'var(--text-secondary)', paddingLeft: 16 }}>
                          {req.acceptance_criteria.map((ac: any, j: number) => <li key={j}>{ac}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Analysis */}
        {page === 'analysis' && (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>🔍 Analysis Results</h1>
            {!analysis ? (
              <div className="glass-card" style={{ textAlign: 'center', padding: 60 }}>
                <p style={{ color: 'var(--text-muted)' }}>No analysis run yet.</p>
                <button className="btn-primary" onClick={runAnalysis} disabled={loading} style={{ marginTop: 16 }}>Run Analysis Pipeline</button>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {Object.entries(analysis).map(([key, value]: [string, any]) => (
                  <div key={key} className="glass-card">
                    <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12, textTransform: 'capitalize' }}>
                      {key === 'compliance' ? '⚖️' : key === 'security' ? '🔒' : key === 'risk_analysis' ? '⚠️' : key === 'validation' ? '✅' : key === 'classification' ? '🏷️' : key === 'conflict_detection' ? '⚡' : key === 'clarification' ? '❓' : '📊'} {key.replace(/_/g, ' ')}
                    </h3>
                    {value && typeof value === 'object' && (
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                        {value.disclaimer && <p style={{ color: 'var(--warning)', fontSize: 12, marginBottom: 8 }}>⚠ {value.disclaimer}</p>}
                        {value.count !== undefined && <p>Items: {value.count}</p>}
                        {value.total_analysed !== undefined && <p>Analysed: {value.total_analysed}</p>}
                        {value.issue_count !== undefined && <p>Issues: {value.issue_count}</p>}
                        {value.conflict_count !== undefined && <p>Conflicts: {value.conflict_count}</p>}
                        {value.duplicate_count !== undefined && <p>Duplicates: {value.duplicate_count}</p>}
                        {value.overall_risk_level && <p>Risk Level: <span className={`badge ${value.overall_risk_level === 'high' ? 'badge-red' : 'badge-yellow'}`}>{value.overall_risk_level}</span></p>}
                        {value.validation_results && (
                          <div style={{ marginTop: 8 }}>
                            {Object.entries(value.validation_results).map(([k, v]: [string, any]) => (
                              <div key={k} style={{ marginBottom: 6 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                                  <span>{k.replace(/_/g, ' ')}</span><span>{typeof v === 'number' ? `${(v * 100).toFixed(0)}%` : v}</span>
                                </div>
                                {typeof v === 'number' && <div className="score-meter"><div className="score-meter-fill" style={{ width: `${v * 100}%`, background: v > 0.8 ? 'var(--success)' : v > 0.6 ? 'var(--warning)' : 'var(--danger)' }} /></div>}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* SDLC */}
        {page === 'sdlc' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div>
                <h1 style={{ fontSize: 24, fontWeight: 700 }}>📊 SDLC Analysis</h1>
                <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Methodology recommendation with factors and rationale</p>
              </div>
              <button className="btn-primary" onClick={runSdlc} disabled={loading}>{loading ? '⏳' : '🔄 Run Analysis'}</button>
            </div>

            {!sdlc ? (
              <div className="glass-card" style={{ textAlign: 'center', padding: 60 }}>
                <p style={{ color: 'var(--text-muted)' }}>Run SDLC analysis to get a methodology recommendation.</p>
              </div>
            ) : (
              <div>
                <div className="glass-card" style={{ marginBottom: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 14, color: 'var(--text-muted)', marginBottom: 8 }}>RECOMMENDED MODEL</div>
                  <div style={{ fontSize: 32, fontWeight: 700, color: 'var(--accent)', marginBottom: 8 }}>{sdlc.display_name || sdlc.recommended_model}</div>
                  <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>Confidence: {((sdlc.recommended_score || sdlc.confidence || 0) * 100).toFixed(0)}%</div>
                  <div className="badge badge-yellow" style={{ marginTop: 8 }}>⚠ Requires Approval</div>
                </div>

                {sdlc.rationale && (
                  <div className="glass-card" style={{ marginBottom: 16 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>📝 Rationale</h3>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{typeof sdlc.rationale === 'string' ? sdlc.rationale : sdlc.recommendation?.rationale || JSON.stringify(sdlc.rationale)}</p>
                  </div>
                )}

                {sdlc.scores && (
                  <div className="glass-card" style={{ marginBottom: 16 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>📈 Model Scores</h3>
                    {Object.entries(sdlc.scores).map(([model, data]: [string, any]) => {
                      const score = typeof data === 'number' ? data : data?.score || 0;
                      return (
                        <div key={model} style={{ marginBottom: 10 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 3 }}>
                            <span style={{ textTransform: 'capitalize' }}>{model.replace(/_/g, ' ')}</span>
                            <span>{(score * 100).toFixed(0)}%</span>
                          </div>
                          <div className="score-meter">
                            <div className="score-meter-fill" style={{ width: `${score * 100}%`, background: model === (sdlc.recommended_model) ? 'linear-gradient(90deg, var(--accent), var(--purple))' : 'var(--text-muted)' }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {sdlc.factors && (
                  <div className="glass-card">
                    <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>🎯 Decision Factors</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                      {Object.entries(sdlc.factors).map(([factor, value]: [string, any]) => (
                        <div key={factor} style={{ fontSize: 13 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{factor.replace(/_/g, ' ')}</span>
                            <span>{(Number(value) * 100).toFixed(0)}%</span>
                          </div>
                          <div className="score-meter"><div className="score-meter-fill" style={{ width: `${Number(value) * 100}%`, background: Number(value) > 0.7 ? 'var(--danger)' : Number(value) > 0.4 ? 'var(--warning)' : 'var(--success)' }} /></div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Artefacts */}
        {page === 'artefacts' && (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>📄 Artefact Generation</h1>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
              {[
                { type: 'srs', label: 'SRS Document', icon: '📑' },
                { type: 'user_stories', label: 'User Stories', icon: '👤' },
                { type: 'use_cases', label: 'Use Cases', icon: '🔄' },
                { type: 'rtm', label: 'Traceability Matrix', icon: '🔗' },
                { type: 'compliance_matrix', label: 'Compliance Matrix', icon: '⚖️' },
                { type: 'threat_risk_register', label: 'Risk Register', icon: '⚠️' },
                { type: 'sdlc_workflow', label: 'SDLC Workflow', icon: '📊' },
                { type: 'acceptance_criteria', label: 'Acceptance Criteria', icon: '✅' },
              ].map(a => (
                <div key={a.type} className="glass-card" style={{ cursor: 'pointer', textAlign: 'center' }} onClick={() => generateArtefact(a.type)}>
                  <div style={{ fontSize: 28, marginBottom: 8 }}>{a.icon}</div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{a.label}</div>
                </div>
              ))}
            </div>

            {artefact && (
              <div className="glass-card">
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>{artefact.title || artefact.artefact_type}</h3>
                <pre style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', lineHeight: 1.6, maxHeight: 500, overflowY: 'auto' }}>
                  {typeof artefact.content === 'string' ? artefact.content : JSON.stringify(artefact.content || artefact, null, 2)}
                </pre>
                {artefact.source_requirements && artefact.source_requirements.length > 0 && (
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Source requirements: </span>
                    {artefact.source_requirements.map((id: string, i: number) => (
                      <span key={i} className="badge badge-blue" style={{ marginLeft: 4 }}>{id}</span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Approvals */}
        {page === 'approvals' && (
          <div className="animate-fade-in">
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>✅ Approval Workflow</h1>
            <div className="glass-card" style={{ textAlign: 'center', padding: 40 }}>
              <p style={{ color: 'var(--text-muted)', marginBottom: 16 }}>Approval requests are generated when the system identifies decisions requiring human authorization:</p>
              <ul style={{ textAlign: 'left', maxWidth: 500, margin: '0 auto', color: 'var(--text-secondary)', fontSize: 14, lineHeight: 2 }}>
                <li>📋 Final requirement baselines</li>
                <li>⚖️ Regulatory interpretations</li>
                <li>🔒 High-risk security requirements</li>
                <li>⚡ Conflicting stakeholder decisions</li>
                <li>🏗️ Architecture-critical requirements</li>
                <li>📊 SDLC methodology selection</li>
                <li>🔄 Changes to approved requirements</li>
                <li>🚀 Production readiness decisions</li>
              </ul>
            </div>
          </div>
        )}

        {/* Audit Trail */}
        {page === 'audit' && (
          <div className="animate-fade-in">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h1 style={{ fontSize: 24, fontWeight: 700 }}>🕐 Audit Trail</h1>
              <button className="btn-secondary" onClick={loadAudit}>🔄 Refresh</button>
            </div>
            {auditTrail.length === 0 ? (
              <div className="glass-card" style={{ textAlign: 'center', padding: 40 }}>
                <p style={{ color: 'var(--text-muted)' }}>No audit events yet. Run the analysis pipeline to generate audit entries.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {auditTrail.map((entry: any, i: number) => (
                  <div key={i} className="glass-card" style={{ padding: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <span className="badge badge-purple">{entry.agent}</span>
                        <span className="badge badge-blue">{entry.action}</span>
                        <span className={`badge ${entry.status === 'success' ? 'badge-green' : 'badge-yellow'}`}>{entry.status}</span>
                      </div>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{entry.timestamp?.split('T')[1]?.split('.')[0] || entry.timestamp}</span>
                    </div>
                    {entry.confidence !== undefined && (
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>Confidence: {(entry.confidence * 100).toFixed(0)}%</div>
                    )}
                    {entry.issues && entry.issues.length > 0 && (
                      <div style={{ marginTop: 4, fontSize: 12, color: 'var(--warning)' }}>{entry.issues.join('; ')}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {loading && <div style={{ position: 'fixed', bottom: 24, right: 24, background: 'var(--accent)', color: 'white', padding: '8px 16px', borderRadius: 20, fontSize: 13, boxShadow: '0 4px 20px var(--accent-glow)' }} className="animate-pulse">⚙️ Processing...</div>}
      </div>
    </div>
  );
}
