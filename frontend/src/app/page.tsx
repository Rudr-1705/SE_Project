'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  authAPI,
  projectsAPI,
  interviewAPI,
  requirementsAPI,
  sdlcAPI,
  srsAPI,
  approvalsAPI,
  sessionAPI,
} from '@/lib/api';

// ── Types ─────────────────────────────────────────────
type User = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization?: string;
  department?: string;
};

type Project = {
  id: string;
  name: string;
  description: string;
  use_case: string;
  status: string;
  current_stage?: string;
  jurisdiction?: string;
  created_at: string;
  updated_at?: string;
};

type Requirement = {
  id?: string;
  requirement_id: string;
  statement: string;
  category: string;
  subcategory?: string;
  priority: string;
  status?: string;
  confidence?: number;
  acceptance_criteria?: string[];
  applicable_regulations?: any[];
  risks?: any[];
  business_justification?: string;
};

type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
};

type ApprovalRequest = {
  id: string;
  title: string;
  description: string;
  request_type: string;
  status: string;
  required_roles?: string[];
  priority?: string;
  created_at?: string;
  resolved_at?: string;
};

const STAGES = [
  { id: 'interview', label: 'Interview', step: 1 },
  { id: 'extraction', label: 'Requirements', step: 2 },
  { id: 'analysis', label: 'Analysis', step: 3 },
  { id: 'sdlc', label: 'SDLC', step: 4 },
  { id: 'srs', label: 'SRS Document', step: 5 },
  { id: 'approval', label: 'Approval', step: 6 },
  { id: 'completed', label: 'Completion', step: 7 },
];

export default function App() {
  // ── Authentication State ──
  const [token, setToken] = useState<string>('');
  const [user, setUser] = useState<User | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authName, setAuthName] = useState('');
  const [authRole, setAuthRole] = useState('user');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');

  // ── Project Management State ──
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectUseCase, setNewProjectUseCase] = useState('loan_processing');
  const [newProjectJurisdiction, setNewProjectJurisdiction] = useState('India');

  // ── Wizard / Stage State ──
  const [currentStage, setCurrentStage] = useState<string>('interview');

  // ── Interview State ──
  const [messages, setMessages] = useState<Message[]>([]);
  const [interviewInput, setInterviewInput] = useState('');
  const [interviewTopics, setInterviewTopics] = useState<string[]>([]);
  const [interviewLoading, setInterviewLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // ── Requirements State ──
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [reqFilter, setReqFilter] = useState('');
  const [reqCategoryFilter, setReqCategoryFilter] = useState('all');
  const [extractLoading, setExtractLoading] = useState(false);

  // ── Analysis State ──
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState<any>(null);
  const [activeAnalysisTab, setActiveAnalysisTab] = useState('compliance');

  // ── SDLC State ──
  const [sdlcResult, setSdlcResult] = useState<any>(null);
  const [sdlcLoading, setSdlcLoading] = useState(false);

  // ── SRS State ──
  const [srsData, setSrsData] = useState<any>(null);
  const [srsLoading, setSrsLoading] = useState(false);

  // ── Approval State ──
  const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
  const [approvalComment, setApprovalComment] = useState('');
  const [approvalLoading, setApprovalLoading] = useState(false);
  const [isMounted, setIsMounted] = useState(false);

  // ── Audit State ──
  const [auditTrail, setAuditTrail] = useState<any[]>([]);

  // ── Notifications ──
  const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 4500);
  };

  // ── Initial Session Restoration ──
  useEffect(() => {
    setIsMounted(true);
    const savedToken = localStorage.getItem('aifre_jwt_token');
    if (savedToken) {
      setToken(savedToken);
      authAPI.getMe(savedToken)
        .then(userData => {
          setUser(userData);
          loadUserProjects(savedToken);
        })
        .catch(() => {
          localStorage.removeItem('aifre_jwt_token');
          setToken('');
          setUser(null);
        });
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Auth Handlers ──
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');

    try {
      let data;
      if (authMode === 'login') {
        data = await authAPI.login({ email: authEmail, password: authPassword });
      } else {
        data = await authAPI.register({
          email: authEmail,
          password: authPassword,
          full_name: authName,
          role: authRole,
        });
      }

      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('aifre_jwt_token', data.access_token);
      showToast(`Welcome back, ${data.user.full_name}!`, 'success');
      loadUserProjects(data.access_token);
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    if (token) {
      await authAPI.logout(token);
    }
    localStorage.removeItem('aifre_jwt_token');
    setToken('');
    setUser(null);
    setActiveProject(null);
    setProjects([]);
    setMessages([]);
    setRequirements([]);
    setAnalysisResults(null);
    setSdlcResult(null);
    setSrsData(null);
    setApprovals([]);
    setShowProfileModal(false);
    showToast('You have been logged out.', 'info');
  };

  const loadUserProjects = async (authToken: string) => {
    try {
      const projs = await projectsAPI.list(authToken);
      setProjects(projs);
      if (projs.length === 0) {
        setShowCreateModal(true);
      } else if (!activeProject) {
        // Automatically open the most recent project
        selectProject(projs[0], authToken);
      }
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  // ── Project Lifecycle Handlers ──
  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    try {
      const proj = await projectsAPI.create(token, {
        name: newProjectName,
        description: newProjectDesc,
        use_case: newProjectUseCase,
        jurisdiction: newProjectJurisdiction,
      });

      setProjects([proj, ...projects]);
      setShowCreateModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      showToast(`Project '${proj.name}' initialized.`, 'success');
      selectProject(proj, token);
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const selectProject = async (proj: Project, authToken: string) => {
    setActiveProject(proj);
    setShowHistoryModal(false);

    try {
      // Restore persistent session from backend
      const session = await sessionAPI.getState(authToken, proj.id);
      const stage = proj.current_stage || session.stage || 'interview';
      setCurrentStage(stage);

      // Load interview history
      const history = await interviewAPI.getHistory(authToken, proj.id);
      setMessages(history.messages || []);
      setInterviewTopics(history.topics_covered || []);

      // If interview is empty, trigger initial welcome question
      if (!history.messages || history.messages.length === 0) {
        setInterviewLoading(true);
        const initData = await interviewAPI.start(authToken, proj.id);
        setMessages([{ role: 'assistant', content: initData.question }]);
        if (initData.topic) setInterviewTopics([initData.topic]);
        setInterviewLoading(false);
      }

      // Load existing requirements
      const reqList = await requirementsAPI.list(authToken, proj.id);
      setRequirements(reqList || []);

      // Load analysis results if available
      if (session.has_analysis) {
        const analysis = await requirementsAPI.getAnalysisResults(authToken, proj.id);
        setAnalysisResults(analysis);
      }

      // Load SDLC if available
      if (session.analysis_results?.sdlc) {
        setSdlcResult(session.analysis_results.sdlc);
      }

      // Load approvals
      const apps = await approvalsAPI.list(authToken, proj.id);
      setApprovals(apps || []);
    } catch (err: any) {
      console.error('Error loading project state:', err);
    }
  };

  const navigateToStage = (stageId: string) => {
    setCurrentStage(stageId);
    if (activeProject && token) {
      projectsAPI.updateStage(token, activeProject.id, stageId).catch(() => {});

      // Auto-load stage data if not yet hydrated in React state
      if (stageId === 'analysis' && !analysisResults) {
        setAnalysisLoading(true);
        requirementsAPI.getAnalysisResults(token, activeProject.id)
          .then(res => {
            if (res && Object.keys(res).length > 0) setAnalysisResults(res);
          })
          .catch(() => {})
          .finally(() => setAnalysisLoading(false));
      } else if (stageId === 'sdlc' && !sdlcResult) {
        setSdlcLoading(true);
        sdlcAPI.getResult(token, activeProject.id)
          .then(res => {
            if (res) setSdlcResult(res);
          })
          .catch(() => {})
          .finally(() => setSdlcLoading(false));
      } else if (stageId === 'approval') {
        setApprovalLoading(true);
        approvalsAPI.list(token, activeProject.id)
          .then(apps => {
            if (apps) setApprovals(apps);
          })
          .catch(() => {})
          .finally(() => setApprovalLoading(false));
      }
    }
  };

  // ── Stage 1: Interview Handlers ──
  const handleSendAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!interviewInput.trim() || !activeProject) return;

    const userText = interviewInput.trim();
    setMessages(prev => [...prev, { role: 'user', content: userText }]);
    setInterviewInput('');
    setInterviewLoading(true);

    try {
      const data = await interviewAPI.answer(token, activeProject.id, userText);
      setMessages(prev => [...prev, { role: 'assistant', content: data.question }]);
      if (data.topic && !interviewTopics.includes(data.topic)) {
        setInterviewTopics(prev => [...prev, data.topic]);
      }
    } catch (err: any) {
      showToast(err.message, 'error');
    } finally {
      setInterviewLoading(false);
    }
  };

  const handleFinishInterviewAndExtract = async () => {
    if (!activeProject) return;
    setExtractLoading(true);

    try {
      const res = await requirementsAPI.extract(token, activeProject.id);
      setRequirements(res.requirements || []);
      showToast(`Successfully synthesized ${res.count || res.requirements?.length || 0} requirements!`, 'success');
      navigateToStage('extraction');
    } catch (err: any) {
      showToast(err.message, 'error');
    } finally {
      setExtractLoading(false);
    }
  };

  // ── Stage 2: Extraction Handlers ──
  const handleProceedToAnalysis = async (force = false) => {
    if (!activeProject) return;
    setAnalysisLoading(true);
    setCurrentStage('analysis');
    projectsAPI.updateStage(token, activeProject.id, 'analysis').catch(() => {});

    // Poll live per-agent progress
    const progressInterval = setInterval(async () => {
      try {
        const prog = await requirementsAPI.getAnalysisProgress(token, activeProject.id);
        if (prog) setAnalysisProgress(prog);
      } catch (_) {}
    }, 1500);

    try {
      const results = await requirementsAPI.analyse(token, activeProject.id, force);
      setAnalysisResults(results);
      const hasFailures = Object.values(results || {}).some((r: any) => r?.status === 'failed');
      if (hasFailures) {
        showToast('Analysis completed with partial dimension warnings.', 'info');
      } else {
        showToast('7-stage requirements analysis complete.', 'success');
      }
    } catch (err: any) {
      showToast(err.message || 'Analysis failed. Please check requirements.', 'error');
    } finally {
      clearInterval(progressInterval);
      setAnalysisLoading(false);
      setAnalysisProgress(null);
    }
  };

  // ── Stage 3: Analysis Handlers ──
  const handleProceedToSDLC = async () => {
    if (!activeProject) return;
    setSdlcLoading(true);
    setCurrentStage('sdlc');
    projectsAPI.updateStage(token, activeProject.id, 'sdlc').catch(() => {});

    try {
      const result = await sdlcAPI.analyse(token, activeProject.id);
      setSdlcResult(result);
      showToast(`Recommended SDLC: ${result.display_name}`, 'success');
    } catch (err: any) {
      showToast(err.message || 'SDLC evaluation failed', 'error');
    } finally {
      setSdlcLoading(false);
    }
  };

  // ── Stage 4: SDLC Handlers ──
  const handleProceedToSRS = async () => {
    if (!activeProject) return;
    setSrsLoading(true);
    setCurrentStage('srs');
    projectsAPI.updateStage(token, activeProject.id, 'srs').catch(() => {});

    try {
      const res = await srsAPI.generate(token, activeProject.id);
      setSrsData(res.srs_data || res);
      showToast('IEEE 29148 SRS document generated.', 'success');
    } catch (err: any) {
      showToast(err.message || 'SRS generation failed', 'error');
    } finally {
      setSrsLoading(false);
    }
  };

  // ── Stage 5: SRS Handlers ──
  const handleProceedToApproval = async () => {
    if (!activeProject) return;
    setApprovalLoading(true);
    setCurrentStage('approval');
    projectsAPI.updateStage(token, activeProject.id, 'approval').catch(() => {});

    try {
      const apps = await approvalsAPI.list(token, activeProject.id);
      setApprovals(apps || []);
    } catch (err: any) {
      showToast(err.message || 'Failed to load approvals', 'error');
    } finally {
      setApprovalLoading(false);
    }
  };

  // ── Stage 6: Approval Handlers ──
  const handleActionApproval = async (approvalId: string, action: 'approve' | 'reject' | 'modify') => {
    if (!activeProject) return;
    setApprovalLoading(true);

    try {
      const res = await approvalsAPI.action(token, activeProject.id, approvalId, action, approvalComment);
      const actionLabel = action === 'approve' ? 'Approved' : (action === 'reject' ? 'Rejected' : 'Changes Requested');
      showToast(`Approval action successful: ${actionLabel}`, 'success');
      setApprovalComment('');

      // Refresh approvals list
      const apps = await approvalsAPI.list(token, activeProject.id);
      setApprovals(apps || []);

      if (res.approval_status === 'approved' || action === 'approve') {
        navigateToStage('completed');
      }
    } catch (err: any) {
      console.error('Approval action error:', err);
      showToast(err.message || 'Approval action failed', 'error');
    } finally {
      setApprovalLoading(false);
    }
  };

  const handleLoadAuditTrail = async () => {
    if (!activeProject) return;
    try {
      const trail = await sessionAPI.getAuditTrail(token, activeProject.id);
      setAuditTrail(trail || []);
    } catch (err: any) {
      showToast(err.message, 'error');
    }
  };

  const handleDownloadPdf = async (projectId = activeProject?.id, safeName = activeProject?.name || 'SRS') => {
    if (!projectId) return;
    try {
      showToast('Downloading IEEE 29148 PDF...', 'info');
      await srsAPI.downloadPdf(token, projectId, `SRS_${safeName.replace(/\s+/g, '_')}.pdf`);
      showToast('PDF downloaded successfully.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Download failed', 'error');
    }
  };

  const handleDownloadDocx = async (projectId = activeProject?.id, safeName = activeProject?.name || 'SRS') => {
    if (!projectId) return;
    try {
      showToast('Downloading editable DOCX...', 'info');
      await srsAPI.downloadDocx(token, projectId, `SRS_${safeName.replace(/\s+/g, '_')}.docx`);
      showToast('DOCX downloaded successfully.', 'success');
    } catch (err: any) {
      showToast(err.message || 'Download failed', 'error');
    }
  };

  // ── Prevent hydration mismatch before client mount ──
  if (!isMounted) {
    return null;
  }

  // ──────────────────────────────────────────────────────
  // 1. AUTHENTICATION VIEW (If not logged in)
  // ──────────────────────────────────────────────────────
  if (!token || !user) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-blue-600 text-white font-bold text-xl shadow-sm mb-4">
            AI
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">
            AIFRE Platform
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Agentic AI Financial Requirements Engineering
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-6 shadow-sm border border-slate-200 rounded-xl sm:px-10">
            {/* Tab switch */}
            <div className="flex border-b border-slate-200 mb-6">
              <button
                type="button"
                onClick={() => setAuthMode('login')}
                className={`flex-1 pb-3 text-sm font-medium border-b-2 text-center transition-colors ${
                  authMode === 'login'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => setAuthMode('register')}
                className={`flex-1 pb-3 text-sm font-medium border-b-2 text-center transition-colors ${
                  authMode === 'register'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                Create Account
              </button>
            </div>

            {authError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              {authMode === 'register' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    value={authName}
                    onChange={e => setAuthName(e.target.value)}
                    placeholder="e.g. Eleanor Vance"
                    className="input-clean"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Corporate Email
                </label>
                <input
                  type="email"
                  required
                  value={authEmail}
                  onChange={e => setAuthEmail(e.target.value)}
                  placeholder="analyst@institution.com"
                  className="input-clean"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={e => setAuthPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="input-clean"
                />
              </div>



              <button
                type="submit"
                disabled={authLoading}
                className="w-full btn-primary py-2.5 mt-2"
              >
                {authLoading ? 'Verifying Credentials...' : authMode === 'login' ? 'Sign In' : 'Register Account'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ──────────────────────────────────────────────────────
  // 2. MAIN APPLICATION (Clean Sequential SaaS Interface)
  // ──────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-5 right-5 z-50 py-2.5 px-4 rounded-lg shadow-lg text-sm font-medium border flex items-center gap-2 animate-fade-in ${
            notification.type === 'error'
              ? 'bg-red-50 text-red-800 border-red-200'
              : notification.type === 'info'
              ? 'bg-blue-50 text-blue-800 border-blue-200'
              : 'bg-emerald-50 text-emerald-800 border-emerald-200'
          }`}
        >
          <span>{notification.message}</span>
        </div>
      )}

      {/* Top Persistent Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow-sm">
              AI
            </div>
            <div>
              <span className="font-bold text-slate-900 text-base tracking-tight">AIFRE</span>
              <span className="hidden sm:inline-block ml-2 text-xs text-slate-400 font-medium border-l border-slate-200 pl-2">
                Requirements Engineering
              </span>
            </div>

            {activeProject && (
              <div className="hidden md:flex items-center gap-2 ml-4 px-2.5 py-1 bg-slate-100 rounded-md text-xs font-medium text-slate-700">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span className="font-semibold text-slate-900">{activeProject.name}</span>
                <span className="text-slate-400">•</span>
                <span className="text-slate-600 capitalize">{activeProject.use_case.replace('_', ' ')}</span>
                {activeProject.jurisdiction && (
                  <>
                    <span className="text-slate-400">•</span>
                    <span className="badge badge-blue text-[10px] font-semibold">
                      🏛️ {activeProject.jurisdiction}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Right Header Navigation Controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <span>+ New Project</span>
            </button>

            <button
              onClick={() => setShowHistoryModal(true)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 transition-colors"
            >
              <span>Projects ({projects.length})</span>
            </button>

            {/* Profile Dropdown Trigger */}
            <div className="relative">
              <button
                onClick={() => setShowProfileModal(!showProfileModal)}
                className="flex items-center gap-2 pl-2 text-xs font-medium text-slate-700 hover:text-slate-900 focus:outline-none"
              >
                <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs border border-blue-200">
                  {user.full_name.charAt(0)}
                </div>
                <span className="hidden sm:inline">{user.full_name}</span>
              </button>

              {/* Account Dropdown Menu */}
              {showProfileModal && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-200 py-1.5 z-50 text-xs">
                  <div className="px-4 py-2 border-b border-slate-100">
                    <p className="font-semibold text-slate-900">{user.full_name}</p>
                    <p className="text-slate-500 truncate">{user.email}</p>
                    <span className="inline-block mt-1 badge badge-blue capitalize">{(user.role || 'user').replace('_', ' ')}</span>
                  </div>
                  <button
                    onClick={() => { setShowHistoryModal(true); setShowProfileModal(false); }}
                    className="w-full text-left px-4 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <span>Previous Projects</span>
                  </button>
                  <button
                    onClick={() => { handleLoadAuditTrail(); setShowProfileModal(false); }}
                    className="w-full text-left px-4 py-2 text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                  >
                    <span>Audit Log</span>
                  </button>
                  <div className="border-t border-slate-100 my-1"></div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-red-600 hover:bg-red-50 flex items-center gap-2 font-medium"
                  >
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sequential Progress Bar / Stepper */}
        {activeProject && (
          <div className="border-t border-slate-100 bg-slate-50/50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2 overflow-x-auto">
              <nav className="flex items-center justify-between min-w-[700px]">
                {STAGES.map((s, idx) => {
                  const isActive = currentStage === s.id;
                  const currentIdx = STAGES.findIndex(item => item.id === currentStage);
                  const isCompleted = idx < currentIdx;

                  return (
                    <button
                      key={s.id}
                      onClick={() => navigateToStage(s.id)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-blue-600 text-white shadow-sm'
                          : isCompleted
                          ? 'text-slate-700 hover:bg-slate-200/60'
                          : 'text-slate-400 hover:text-slate-600'
                      }`}
                    >
                      <span
                        className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                          isActive
                            ? 'bg-white text-blue-600'
                            : isCompleted
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-slate-200 text-slate-500'
                        }`}
                      >
                        {isCompleted ? '✓' : s.step}
                      </span>
                      <span>{s.label}</span>
                      {idx < STAGES.length - 1 && (
                        <span className="text-slate-300 ml-2">›</span>
                      )}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!activeProject ? (
          <div className="max-w-md mx-auto text-center py-16">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-2xl mx-auto mb-4 border border-blue-100">
              📁
            </div>
            <h3 className="text-lg font-bold text-slate-900">No Active Project</h3>
            <p className="mt-1 text-sm text-slate-500 mb-6">
              Create a project to initiate the AI-guided requirements engineering workflow.
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              + Create New Project
            </button>
          </div>
        ) : (
          <div className="space-y-6 animate-fade-in">
            {/* ─────────────────────────────────────────────
                STAGE 1: STAKEHOLDER INTERVIEW
            ───────────────────────────────────────────── */}
            {currentStage === 'interview' && (
              <div className="saas-card overflow-hidden">
                <div className="p-6 border-b border-slate-200 flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Adaptive Stakeholder Interview</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      The AI agent conducts an interactive interview to discover functional workflows, regulatory boundaries, and security constraints.
                    </p>
                  </div>
                  <button
                    onClick={handleFinishInterviewAndExtract}
                    disabled={extractLoading || messages.length < 2}
                    className="btn-primary text-xs"
                  >
                    {extractLoading ? 'Extracting Requirements...' : 'Complete & Extract Requirements →'}
                  </button>
                </div>

                {/* Topics Progress Checklist */}
                <div className="px-6 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center gap-2 overflow-x-auto text-xs">
                  <span className="text-slate-500 font-semibold uppercase text-[10px] tracking-wider">Topics Explored:</span>
                  {interviewTopics.length === 0 ? (
                    <span className="text-slate-400 italic">Conversation in progress...</span>
                  ) : (
                    interviewTopics.map((topic, i) => (
                      <span key={i} className="badge badge-blue capitalize">
                        ✓ {topic.replace('_', ' ')}
                      </span>
                    ))
                  )}
                </div>

                {/* Chat History Messages */}
                <div className="p-6 h-[460px] overflow-y-auto space-y-4 bg-slate-50/30">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-2xl rounded-xl p-4 text-sm leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'bg-white text-slate-800 border border-slate-200 shadow-sm'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1 opacity-75 text-[11px] font-semibold">
                          <span>{msg.role === 'user' ? 'Stakeholder (You)' : 'AIFRE Requirements Specialist'}</span>
                        </div>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    </div>
                  ))}
                  {interviewLoading && (
                    <div className="flex justify-start">
                      <div className="bg-white border border-slate-200 rounded-xl p-4 text-xs text-slate-500 flex items-center gap-2">
                        <span className="animate-pulse">●</span>
                        <span className="animate-pulse delay-100">●</span>
                        <span className="animate-pulse delay-200">●</span>
                        <span className="ml-1">Formulating follow-up question...</span>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>

                {/* Response Input Box */}
                <form onSubmit={handleSendAnswer} className="p-4 border-t border-slate-200 bg-white flex gap-2">
                  <input
                    type="text"
                    value={interviewInput}
                    onChange={e => setInterviewInput(e.target.value)}
                    placeholder="Provide details about requirements, constraints, KYC, transaction limits, or security..."
                    disabled={interviewLoading}
                    className="input-clean flex-1"
                  />
                  <button
                    type="submit"
                    disabled={interviewLoading || !interviewInput.trim()}
                    className="btn-primary"
                  >
                    Send Response
                  </button>
                </form>
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 2: REQUIREMENT EXTRACTION
            ───────────────────────────────────────────── */}
            {currentStage === 'extraction' && (
              <div className="space-y-4">
                <div className="saas-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Extracted Requirements Repository</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Synthesized from stakeholder answers with unique identifiers, acceptance criteria, and priority rankings.
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => navigateToStage('interview')}
                      className="btn-secondary text-xs"
                    >
                      ← Back to Interview
                    </button>
                    <button
                      onClick={() => handleProceedToAnalysis()}
                      disabled={requirements.length === 0 || analysisLoading}
                      className="btn-primary text-xs"
                    >
                      {analysisLoading ? 'Running Analysis...' : 'Proceed to Analysis →'}
                    </button>
                  </div>
                </div>

                {/* Filter and Search Bar */}
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="text"
                    placeholder="Search requirements by ID or keyword..."
                    value={reqFilter}
                    onChange={e => setReqFilter(e.target.value)}
                    className="input-clean flex-1"
                  />
                  <select
                    value={reqCategoryFilter}
                    onChange={e => setReqCategoryFilter(e.target.value)}
                    className="input-clean sm:w-48"
                  >
                    <option value="all">All Categories</option>
                    <option value="functional">Functional</option>
                    <option value="security">Security</option>
                    <option value="performance">Performance</option>
                    <option value="audit_reporting">Audit / Reporting</option>
                  </select>
                </div>

                {/* Requirements Cards */}
                <div className="grid grid-cols-1 gap-3">
                  {requirements
                    .filter(r => {
                      const matchesText = !reqFilter ||
                        r.statement.toLowerCase().includes(reqFilter.toLowerCase()) ||
                        r.requirement_id.toLowerCase().includes(reqFilter.toLowerCase());
                      const matchesCat = reqCategoryFilter === 'all' || r.category.toLowerCase().includes(reqCategoryFilter);
                      return matchesText && matchesCat;
                    })
                    .map((req, idx) => (
                      <div key={idx} className="saas-card p-5 hover:border-slate-300">
                        <div className="flex items-start justify-between gap-4 mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2 py-0.5 rounded">
                              {req.requirement_id}
                            </span>
                            <span className="badge badge-gray capitalize">{req.category}</span>
                            <span
                              className={`badge ${
                                req.priority === 'critical'
                                  ? 'badge-red'
                                  : req.priority === 'high'
                                  ? 'badge-yellow'
                                  : 'badge-blue'
                              } uppercase`}
                            >
                              {req.priority}
                            </span>
                          </div>
                          {req.confidence && (
                            <span className="text-[11px] text-slate-400 font-medium">
                              Confidence: {Math.round(req.confidence * 100)}%
                            </span>
                          )}
                        </div>

                        <p className="text-sm font-medium text-slate-900 leading-relaxed">
                          {req.statement}
                        </p>

                        {req.business_justification && (
                          <p className="text-xs text-slate-500 mt-2">
                            <span className="font-semibold text-slate-600">Rationale:</span> {req.business_justification}
                          </p>
                        )}

                        {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-slate-100">
                            <span className="text-[11px] font-semibold text-slate-600 block mb-1">
                              Acceptance Criteria:
                            </span>
                            <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                              {req.acceptance_criteria.map((ac, acIdx) => (
                                <li key={acIdx}>{ac}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 3: MULTI-AGENT ANALYSIS
            ───────────────────────────────────────────── */}
            {currentStage === 'analysis' && (
              <div className="space-y-4">
                <div className="saas-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">Multi-Agent Requirements Analysis</h3>
                      <span className="badge badge-blue text-[10px] uppercase font-bold tracking-wider">7 Dimensions</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Evaluated by specialized AI agents: Compliance, Security, Risk, Classification, Conflict, Ambiguity, and Quality Validation.
                    </p>
                  </div>
                    <div className="flex items-center gap-3">
                    <button
                      onClick={() => navigateToStage('extraction')}
                      className="btn-secondary text-xs"
                    >
                      ← Back to Requirements
                    </button>
                    {analysisResults ? (
                      <>
                        <button
                          onClick={() => handleProceedToAnalysis(true)}
                          disabled={analysisLoading}
                          className="btn-secondary text-xs"
                          title="Force re-run all 7 analysis agents"
                        >
                          {analysisLoading ? 'Re-running...' : '↻ Re-run Analysis'}
                        </button>
                        <button
                          onClick={handleProceedToSDLC}
                          disabled={sdlcLoading}
                          className="btn-primary text-xs"
                        >
                          {sdlcLoading ? 'Evaluating SDLC...' : 'Proceed to SDLC Recommendation →'}
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => handleProceedToAnalysis(false)}
                        disabled={analysisLoading}
                        className="btn-primary text-xs"
                      >
                        {analysisLoading ? 'Running Multi-Agent Analysis...' : 'Run 7-Dimension Analysis →'}
                      </button>
                    )}
                  </div>
                </div>

                {/* Loading State: Agent Pipeline Progress */}
                {analysisLoading && (
                  <div className="saas-card p-8 text-center bg-slate-50/50 border border-blue-200">
                    <div className="w-12 h-12 rounded-full border-4 border-blue-600 border-t-transparent animate-spin mx-auto mb-4"></div>
                    <h4 className="text-sm font-bold text-slate-900 mb-1">
                      Executing 7-Stage Multi-Agent Analysis Pipeline...
                    </h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
                      Local Qwen3:4B agents are evaluating compliance ({activeProject?.jurisdiction || 'Statutory'}), security threat modeling, risk registers, and IEEE 29148 validation metrics.
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl mx-auto text-left text-xs">
                      {[
                        { key: 'clarification', label: 'Clarification Agent' },
                        { key: 'classification', label: 'Classification Agent' },
                        { key: 'conflict_detection', label: 'Conflict Detection' },
                        { key: 'validation', label: 'Quality Validation' },
                        { key: 'compliance', label: 'Compliance Agent' },
                        { key: 'security', label: 'Security & Privacy' },
                        { key: 'risk_analysis', label: 'Risk Analysis Agent' },
                      ].map((ag, i) => {
                        const dimState = analysisProgress?.dimensions?.[ag.key]?.status || 'in_progress';
                        return (
                          <div key={i} className={`flex items-center gap-2 p-2.5 bg-white rounded border transition-colors ${
                            dimState === 'completed' ? 'border-emerald-200 bg-emerald-50/20 text-emerald-800' :
                            dimState === 'failed' ? 'border-red-200 bg-red-50/20 text-red-800' :
                            'border-blue-200 text-slate-700 animate-pulse'
                          }`}>
                            <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                              dimState === 'completed' ? 'bg-emerald-500' :
                              dimState === 'failed' ? 'bg-red-500' :
                              'bg-blue-600'
                            }`}></span>
                            <div className="min-w-0">
                              <p className="text-[11px] font-semibold truncate">{ag.label}</p>
                              <p className="text-[9px] text-slate-400 capitalize">{dimState.replace('_', ' ')}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Partial Failure Warning Banner */}
                {analysisResults && Object.entries(analysisResults).some(([_, val]: any) => val?.status === 'failed') && (
                  <div className="p-4 rounded-xl border border-amber-300 bg-amber-50/80 mb-6 flex items-start gap-3">
                    <span className="text-xl">⚠️</span>
                    <div className="text-xs">
                      <strong className="text-amber-900 font-bold block mb-0.5">Partial Dimension Analysis Alert</strong>
                      <p className="text-amber-800">
                        One or more analysis agents encountered an execution error. Completed dimensions are visible below, but failed dimensions require re-running.
                      </p>
                    </div>
                  </div>
                )}

                {/* Empty State: Prompt to run analysis */}
                {!analysisLoading && !analysisResults && (
                  <div className="saas-card p-10 text-center bg-white border border-slate-200">
                    <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-2xl mx-auto mb-3 border border-blue-100">
                      🔬
                    </div>
                    <h4 className="text-base font-bold text-slate-900 mb-1">Ready for Multi-Agent Analysis</h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mb-5">
                      All {requirements.length} requirements have been extracted. Click the button below to initiate multi-agent compliance, security, risk, and consistency evaluations.
                    </p>
                    <button
                      onClick={() => handleProceedToAnalysis()}
                      className="btn-primary text-xs"
                    >
                      Run 7-Dimension Analysis Pipeline →
                    </button>
                  </div>
                )}

                {/* Analysis Dimension Tabs & Content */}
                {!analysisLoading && analysisResults && (
                  <div className="saas-card overflow-hidden">
                    <div className="flex border-b border-slate-200 overflow-x-auto bg-slate-50/50">
                      {[
                        { id: 'compliance', label: '1. Compliance & Statutory' },
                        { id: 'security', label: '2. Security & Privacy' },
                        { id: 'risk', label: '3. Risk Assessment' },
                        { id: 'classification', label: '4. Classification' },
                        { id: 'conflict_detection', label: '5. Conflict Detection' },
                        { id: 'clarification', label: '6. Ambiguities & Clarification' },
                        { id: 'validation', label: '7. Quality Validation' },
                      ].map(tab => (
                        <button
                          key={tab.id}
                          onClick={() => setActiveAnalysisTab(tab.id)}
                          className={`px-4 py-3 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${
                            activeAnalysisTab === tab.id
                              ? 'border-blue-600 text-blue-600 bg-white'
                              : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100/50'
                          }`}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    <div className="p-6">
                      {/* Dimension 1: Compliance Tab */}
                      {activeAnalysisTab === 'compliance' && (
                        <div className="space-y-4">
                          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
                            <span className="text-amber-700 font-bold">🏛️</span>
                            <div>
                              <strong>Jurisdiction Framework: </strong>
                              {analysisResults?.compliance?.statutory_jurisdiction || activeProject?.jurisdiction || 'Statutory Financial Guidelines'}.
                              <span className="block mt-0.5 text-[11px] text-amber-700">
                                {analysisResults?.compliance?.disclaimer || 'Compliance analysis is machine-assisted advisory guidance derived from statutory frameworks. Final verification requires human compliance officer sign-off.'}
                              </span>
                            </div>
                          </div>
                          <div className="space-y-3">
                            {(analysisResults?.compliance?.compliance_analysis || []).map((item: any, i: number) => (
                              <div key={i} className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="font-mono text-xs font-bold text-blue-700">{item.requirement_id}</span>
                                  {item.approval_required ? (
                                    <span className="badge badge-yellow text-[10px]">Mandatory Compliance Sign-Off</span>
                                  ) : (
                                    <span className="badge badge-blue text-[10px]">Standard Oversight</span>
                                  )}
                                </div>
                                <div className="text-xs space-y-1.5 text-slate-600">
                                  <div>
                                    <strong className="text-slate-800">Applicable Regulations: </strong>
                                    {item.applicable_regulations?.map((r: any) => typeof r === 'string' ? r : `${r.name} (${r.jurisdiction || 'Statutory'})`).join(', ') || 'Statutory financial standards'}
                                  </div>
                                  <div>
                                    <strong className="text-slate-800">Mandated Controls: </strong>
                                    {item.required_controls?.join('; ') || 'Immutable audit logging and access restrictions'}
                                  </div>
                                  {item.compliance_gaps?.length > 0 && (
                                    <div className="text-red-700 font-medium">
                                      <strong>Identified Gaps: </strong>{item.compliance_gaps.join(', ')}
                                    </div>
                                  )}
                                  {item.data_retention && (
                                    <div className="text-slate-700">
                                      <strong>Data Retention: </strong>{item.data_retention}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Dimension 2: Security & Privacy Tab */}
                      {activeAnalysisTab === 'security' && (() => {
                        const secItems = Array.isArray(analysisResults?.security)
                          ? analysisResults.security
                          : (analysisResults?.security?.security_analysis || analysisResults?.security?.items || []);
                        return (
                          <div className="space-y-3">
                            {secItems.length === 0 ? (
                              <div className="p-6 text-center bg-slate-50 rounded-lg border border-slate-200">
                                <p className="text-xs font-semibold text-slate-800">Security & Privacy Controls Assessed</p>
                                <p className="text-[11px] text-slate-500 mt-0.5">Standard statutory encryption (AES-256 / TLS 1.3) and least-privilege token access controls applicable.</p>
                              </div>
                            ) : (
                              secItems.map((sec: any, i: number) => (
                                <div key={i} className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-mono text-xs font-bold text-blue-700">{sec.requirement_id || `SEC-${i + 1}`}</span>
                                    <span className={`badge ${sec.threat_level === 'critical' ? 'badge-red' : (sec.threat_level === 'high' ? 'badge-yellow' : 'badge-blue')} uppercase text-[10px]`}>
                                      {sec.threat_level || 'standard'} Threat Level
                                    </span>
                                  </div>
                                  <div className="text-xs space-y-2 text-slate-600">
                                    <div>
                                      <strong className="text-slate-800">Security Concerns: </strong>
                                      {sec.security_concerns?.join(', ') || 'Confidentiality, integrity, and tamper protection'}
                                    </div>
                                    <div>
                                      <strong className="text-slate-800">Recommended Controls: </strong>
                                      {sec.recommended_controls?.map((c: any) => typeof c === 'string' ? c : `${c.control || c.name || 'Control'} (${c.standard || 'Industry Standard'})`).join(', ') || 'AES-256 encryption at rest, TLS 1.3 in transit'}
                                    </div>
                                    {sec.privacy_concerns?.length > 0 && (
                                      <div>
                                        <strong className="text-slate-800">Privacy Safeguards: </strong>
                                        {sec.privacy_concerns.join(', ')}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        );
                      })()}

                      {/* Dimension 3: Risk Assessment Tab */}
                      {activeAnalysisTab === 'risk' && (() => {
                        const riskItems = Array.isArray(analysisResults?.risk_analysis)
                          ? analysisResults.risk_analysis
                          : Array.isArray(analysisResults?.risk)
                          ? analysisResults.risk
                          : (analysisResults?.risk_analysis?.risk_assessment || analysisResults?.risk?.risk_assessment || analysisResults?.risk_analysis?.risks || analysisResults?.risk?.risks || []);
                        return (
                          <div className="space-y-3">
                            {riskItems.length === 0 ? (
                              <div className="p-6 text-center bg-slate-50 rounded-lg border border-slate-200">
                                <p className="text-xs font-semibold text-slate-800">Risk Assessment Register</p>
                                <p className="text-[11px] text-slate-500 mt-0.5">Operational resilience and statutory compliance risk mitigations registered.</p>
                              </div>
                            ) : (
                              riskItems.map((risk: any, i: number) => (
                                <div key={i} className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="font-bold text-xs text-slate-800">
                                      {risk.risk_id || `RSK-00${i + 1}`}: {(risk.category || 'Operational').toUpperCase()} RISK
                                    </span>
                                    <span className={`badge ${risk.risk_level === 'high' || risk.risk_level === 'critical' ? 'badge-red' : 'badge-yellow'} uppercase text-[10px]`}>
                                      {risk.risk_level?.toUpperCase() || 'MEDIUM'}
                                    </span>
                                  </div>
                                  <p className="text-xs text-slate-700 mb-2">{risk.description || 'Statutory and operational risk management.'}</p>
                                  <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-100">
                                    <strong className="text-slate-800">Mitigation Strategy: </strong>
                                    {risk.mitigation || 'Continuous monitoring and automated controls.'}
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        );
                      })()}

                      {/* Dimension 4: Classification Tab */}
                      {activeAnalysisTab === 'classification' && (
                        <div className="space-y-3">
                          {(analysisResults?.classification?.classifications || []).map((cls: any, i: number) => (
                            <div key={i} className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
                              <div className="flex items-center justify-between mb-1.5">
                                <span className="font-mono text-xs font-bold text-blue-700">{cls.requirement_id}</span>
                                <div className="flex items-center gap-1.5">
                                  <span className="badge badge-blue text-[10px] uppercase font-bold">{cls.primary_category}</span>
                                  {cls.subcategory && (
                                    <span className="badge bg-slate-100 text-slate-700 text-[10px]">{cls.subcategory}</span>
                                  )}
                                </div>
                              </div>
                              <p className="text-xs text-slate-600 mt-1">
                                <strong className="text-slate-800">Classification Rationale: </strong>
                                {cls.rationale || 'Categorized according to IEEE 29148 requirements taxonomy.'}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Dimension 5: Conflict Detection Tab */}
                      {activeAnalysisTab === 'conflict_detection' && (
                        <div className="space-y-3">
                          {(!analysisResults?.conflict_detection?.conflicts || analysisResults?.conflict_detection?.conflicts?.length === 0) ? (
                            <div className="p-6 text-center bg-slate-50 rounded-lg border border-slate-200">
                              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center text-sm mx-auto mb-2">✓</div>
                              <p className="text-xs font-semibold text-slate-800">No Direct Inconsistencies or Contradictions Detected</p>
                              <p className="text-[11px] text-slate-500 mt-0.5">All functional and non-functional requirements exhibit mutually consistent constraints.</p>
                            </div>
                          ) : (
                            analysisResults?.conflict_detection?.conflicts?.map((c: any, i: number) => (
                              <div key={i} className="p-4 rounded-lg border border-red-200 bg-red-50/20">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-bold text-xs text-red-800">{c.conflict_id || `CONFLICT-${i + 1}`}: {c.conflict_type?.toUpperCase()}</span>
                                  <span className="badge badge-red text-[10px]">{c.severity?.toUpperCase()}</span>
                                </div>
                                <p className="text-xs text-slate-700 mb-2">{c.description}</p>
                                <div className="text-xs text-slate-600 bg-white p-2.5 rounded border border-slate-200">
                                  <strong className="text-slate-800">Resolution Strategy: </strong>
                                  {c.resolution_strategy}
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {/* Dimension 6: Ambiguities / Clarification Tab */}
                      {activeAnalysisTab === 'clarification' && (
                        <div className="space-y-3">
                          {(!analysisResults?.clarification?.questions || analysisResults?.clarification?.questions?.length === 0) ? (
                            <div className="p-6 text-center bg-slate-50 rounded-lg border border-slate-200">
                              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center text-sm mx-auto mb-2">✓</div>
                              <p className="text-xs font-semibold text-slate-800">Requirements Specification Clear & Unambiguous</p>
                              <p className="text-[11px] text-slate-500 mt-0.5">No critical omissions or underspecified constraints detected in the elicited baseline.</p>
                            </div>
                          ) : (
                            analysisResults?.clarification?.questions?.map((q: any, i: number) => (
                              <div key={i} className="p-4 rounded-lg border border-slate-200 bg-white shadow-sm">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-mono text-xs font-bold text-blue-700">{q.target_requirement}</span>
                                  <span className="badge badge-yellow capitalize text-[10px]">{q.priority} Priority</span>
                                </div>
                                <p className="text-xs font-semibold text-slate-800 mb-1">{q.question}</p>
                                <p className="text-[11px] text-slate-500">Reason: {q.reason}</p>
                              </div>
                            ))
                          )}
                        </div>
                      )}

                      {/* Dimension 7: Validation Tab */}
                      {activeAnalysisTab === 'validation' && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                            {Object.entries(analysisResults?.validation?.validation_results || {}).map(([metric, val]: any, i) => (
                              <div key={i} className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center">
                                <span className="text-xs text-slate-500 font-semibold uppercase">{metric}</span>
                                <p className="text-2xl font-bold text-slate-900 mt-1">
                                  {typeof val === 'number' ? `${Math.round(val * 100)}%` : val}
                                </p>
                              </div>
                            ))}
                          </div>
                          {analysisResults?.validation?.recommendations?.length > 0 && (
                            <div className="p-4 bg-white rounded-lg border border-slate-200">
                              <strong className="text-xs text-slate-800 block mb-2">Quality Recommendations:</strong>
                              <ul className="text-xs text-slate-600 space-y-1 list-disc pl-4">
                                {analysisResults.validation.recommendations.map((rec: string, rIdx: number) => (
                                  <li key={rIdx}>{rec}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 4: SDLC RECOMMENDATION
            ───────────────────────────────────────────── */}
            {currentStage === 'sdlc' && (
              <div className="space-y-4">
                <div className="saas-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">SDLC Methodology Recommendation</h3>
                      <span className="badge badge-blue text-[10px] uppercase font-bold tracking-wider">6 Models Evaluated</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Deterministic multi-criteria evaluation comparing 6 software development life-cycle models based on requirements and analysis findings.
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => navigateToStage('analysis')}
                      className="btn-secondary text-xs"
                    >
                      ← Back to Analysis
                    </button>
                    {sdlcResult ? (
                      <button
                        onClick={handleProceedToSRS}
                        disabled={srsLoading}
                        className="btn-primary text-xs"
                      >
                        {srsLoading ? 'Generating SRS...' : 'Proceed to SRS Generation →'}
                      </button>
                    ) : (
                      <button
                        onClick={handleProceedToSDLC}
                        disabled={sdlcLoading}
                        className="btn-primary text-xs"
                      >
                        {sdlcLoading ? 'Evaluating SDLC...' : 'Evaluate Methodologies →'}
                      </button>
                    )}
                  </div>
                </div>

                {/* Loading State */}
                {sdlcLoading && (
                  <div className="saas-card p-8 text-center bg-slate-50/50 border border-blue-200">
                    <div className="w-12 h-12 rounded-full border-4 border-blue-600 border-t-transparent animate-spin mx-auto mb-4"></div>
                    <h4 className="text-sm font-bold text-slate-900 mb-1">
                      Evaluating 6 SDLC Methodologies...
                    </h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto">
                      Executing multi-criteria fitness scoring weighted against regulatory criticality, verification rigor, and delivery velocity.
                    </p>
                  </div>
                )}

                {/* Empty State */}
                {!sdlcLoading && !sdlcResult && (
                  <div className="saas-card p-10 text-center bg-white border border-slate-200">
                    <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center text-2xl mx-auto mb-3 border border-blue-100">
                      ⚖️
                    </div>
                    <h4 className="text-base font-bold text-slate-900 mb-1">SDLC Recommendation Ready</h4>
                    <p className="text-xs text-slate-500 max-w-md mx-auto mb-5">
                      Requirements and 7-dimension analysis have been synthesized. Click below to generate multi-criteria fitness scores and governance trade-offs for all 6 models.
                    </p>
                    <button
                      onClick={handleProceedToSDLC}
                      className="btn-primary text-xs"
                    >
                      Evaluate SDLC Methodologies →
                    </button>
                  </div>
                )}

                {/* Populated SDLC Results */}
                {!sdlcLoading && sdlcResult && (
                  <div className="space-y-4">
                    {/* Recommended Card */}
                    <div className="saas-card p-6 border-blue-200 bg-blue-50/20">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="badge badge-blue text-xs uppercase font-bold">Recommended Methodology</span>
                          <h4 className="text-lg font-bold text-slate-900">{sdlcResult.display_name}</h4>
                        </div>
                        <span className="text-2xl font-bold text-blue-700">
                          {Math.round(sdlcResult.recommended_score * 100)}% Match
                        </span>
                      </div>
                      <p className="text-sm text-slate-700 leading-relaxed mb-4">
                        {sdlcResult.rationale}
                      </p>

                      {sdlcResult.trade_offs && sdlcResult.trade_offs.length > 0 && (
                        <div className="bg-white p-4 rounded-lg border border-slate-200 mb-2">
                          <strong className="text-xs text-slate-800 block mb-2">Key Lifecycle Governance Trade-Offs:</strong>
                          <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
                            {sdlcResult.trade_offs.map((to: string, i: number) => (
                              <li key={i}>{to}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* Methodology Comparison Table */}
                    <div className="saas-card p-6">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4">
                        Comparative Model Fitness Scores
                      </h4>
                      <div className="space-y-3">
                        {Object.entries(sdlcResult.scores || {}).map(([model, score]: any, i) => {
                          const isRec = model === sdlcResult.recommended_model;
                          const pct = Math.round(score * 100);

                          return (
                            <div key={i} className="flex items-center gap-4 text-xs">
                              <span className="w-40 font-semibold text-slate-800 capitalize">
                                {model.replace(/_/g, ' ')}
                              </span>
                              <div className="flex-1 bg-slate-100 rounded-full h-3 overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-500 ${
                                    isRec ? 'bg-blue-600' : 'bg-slate-400'
                                  }`}
                                  style={{ width: `${pct}%` }}
                                ></div>
                              </div>
                              <span className={`w-14 text-right font-mono font-bold ${isRec ? 'text-blue-700' : 'text-slate-600'}`}>
                                {pct}%
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* 6-Model Comparative Catalog */}
                    {sdlcResult.evaluated_models && (
                      <div className="saas-card p-6">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-4">
                          Detailed Methodology Evaluations (6 Models)
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {sdlcResult.evaluated_models.map((m: any, idx: number) => (
                            <div
                              key={idx}
                              className={`p-4 rounded-xl border ${
                                m.is_recommended
                                  ? 'border-blue-400 bg-blue-50/20 shadow-sm'
                                  : 'border-slate-200 bg-white'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <h5 className="font-bold text-xs text-slate-900">{m.display_name}</h5>
                                <span className={`badge ${m.is_recommended ? 'badge-blue font-bold' : 'bg-slate-100 text-slate-700'} text-[11px]`}>
                                  {Math.round(m.score * 100)}% Match
                                </span>
                              </div>
                              <p className="text-xs text-slate-600 mb-3">{m.description}</p>
                              <div className="space-y-1.5 text-[11px]">
                                <div>
                                  <span className="font-semibold text-emerald-700">Advantages: </span>
                                  <span className="text-slate-600">{m.pros?.join('; ')}</span>
                                </div>
                                <div>
                                  <span className="font-semibold text-amber-700">Governance Challenges: </span>
                                  <span className="text-slate-600">{m.cons?.join('; ')}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 5: SRS DOCUMENT (Keep ONLY SRS)
            ───────────────────────────────────────────── */}
            {currentStage === 'srs' && (
              <div className="space-y-4">
                <div className="saas-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Software Requirements Specification (IEEE 29148)</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Formal, verifiable SRS ready for architectural review, regulatory examination, and sign-off.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      onClick={() => navigateToStage('sdlc')}
                      className="btn-secondary text-xs"
                    >
                      ← Back to SDLC
                    </button>

                    {/* Download Buttons with Bearer Auth */}
                    <button
                      type="button"
                      onClick={() => handleDownloadPdf()}
                      className="btn-secondary text-xs font-semibold text-blue-700 border-blue-200 hover:bg-blue-50"
                    >
                      📄 Download PDF
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownloadDocx()}
                      className="btn-secondary text-xs font-semibold text-blue-700 border-blue-200 hover:bg-blue-50"
                    >
                      📝 Download DOCX
                    </button>

                    <button
                      onClick={handleProceedToApproval}
                      disabled={approvalLoading}
                      className="btn-primary text-xs"
                    >
                      Submit for Sign-Off →
                    </button>
                  </div>
                </div>

                {/* SRS Structured Preview */}
                <div className="saas-card p-8 bg-white border border-slate-200">
                  <div className="border-b border-slate-200 pb-6 mb-6">
                    <span className="badge badge-blue text-[11px] mb-2 uppercase tracking-wide">IEEE Std 29148-2018</span>
                    <h2 className="text-2xl font-bold text-slate-900">{activeProject.name}</h2>
                    <p className="text-sm text-slate-500 mt-1">Software Requirements Specification Baseline 1.0</p>
                  </div>

                  {srsData?.sections?.map((sec: any, idx: number) => (
                    <div key={idx} className="mb-8">
                      <h4 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-1.5 mb-3">
                        {sec.num}. {sec.title}
                      </h4>
                      {sec.content && (
                        <p className="text-xs text-slate-600 leading-relaxed mb-4">{sec.content}</p>
                      )}

                      {/* Subsections */}
                      {sec.subsections?.map((sub: any, sIdx: number) => (
                        <div key={sIdx} className="mb-4 pl-3 border-l-2 border-slate-100">
                          <h5 className="text-xs font-semibold text-slate-800 mb-1">
                            {sub.num} {sub.title}
                          </h5>
                          {sub.content && <p className="text-xs text-slate-600 leading-relaxed mb-2">{sub.content}</p>}
                          {sub.items && (
                            <ul className="text-xs text-slate-600 list-disc pl-4 space-y-1">
                              {sub.items.map((it: string, itIdx: number) => (
                                <li key={itIdx}>{it}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}

                      {/* Requirements table if functional */}
                      {sec.requirements && (
                        <div className="mt-3 overflow-x-auto">
                          <table className="w-full text-left text-xs border border-slate-200 rounded-lg">
                            <thead className="bg-slate-50 text-slate-700">
                              <tr>
                                <th className="p-2.5 font-semibold">ID</th>
                                <th className="p-2.5 font-semibold">Specification Statement</th>
                                <th className="p-2.5 font-semibold">Priority</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {sec.requirements.map((r: any, rIdx: number) => (
                                <tr key={rIdx} className="hover:bg-slate-50/50">
                                  <td className="p-2.5 font-mono font-bold text-blue-700">{r.requirement_id}</td>
                                  <td className="p-2.5 text-slate-800">{r.statement}</td>
                                  <td className="p-2.5 uppercase font-medium text-slate-600">{r.priority}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 6: HUMAN APPROVAL WORKFLOW
            ───────────────────────────────────────────── */}
            {currentStage === 'approval' && (
              <div className="space-y-4">
                <div className="saas-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Formal Human Approval & Governance</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Multi-stakeholder sign-off on requirements baseline and SDLC governance controls.
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => navigateToStage('srs')}
                      className="btn-secondary text-xs"
                    >
                      ← Back to SRS
                    </button>
                    {approvals.some(a => a.status === 'approved') && (
                      <button
                        onClick={() => navigateToStage('completed')}
                        className="btn-primary text-xs"
                      >
                        Complete Project →
                      </button>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                  {approvals.map((app, idx) => (
                    <div key={idx} className="saas-card p-6 border-slate-200">
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div>
                          <span className="badge badge-blue text-[10px] uppercase font-bold tracking-wider mb-1">
                            {app.request_type?.replace(/_/g, ' ')}
                          </span>
                          <h4 className="text-base font-bold text-slate-900">{app.title}</h4>
                          <p className="text-xs text-slate-600 mt-1">{app.description}</p>
                        </div>
                        <span
                          className={`badge ${
                            app.status === 'approved'
                              ? 'badge-green'
                              : app.status === 'rejected'
                              ? 'badge-red'
                              : 'badge-yellow'
                          } uppercase text-xs`}
                        >
                          {app.status}
                        </span>
                      </div>

                      {app.status === 'pending' && (
                        <div className="mt-4 pt-4 border-t border-slate-100 space-y-3">
                          <textarea
                            value={approvalComment}
                            onChange={e => setApprovalComment(e.target.value)}
                            placeholder="Enter review comments or conditional sign-off notes..."
                            className="input-clean text-xs h-20 resize-none"
                          />
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => handleActionApproval(app.id, 'approve')}
                              disabled={approvalLoading}
                              className="btn-primary text-xs bg-emerald-600 hover:bg-emerald-700"
                            >
                              Approve Baseline
                            </button>
                            <button
                              onClick={() => handleActionApproval(app.id, 'modify')}
                              disabled={approvalLoading}
                              className="btn-secondary text-xs text-amber-700 border-amber-300 hover:bg-amber-50"
                            >
                              Request Changes
                            </button>
                            <button
                              onClick={() => handleActionApproval(app.id, 'reject')}
                              disabled={approvalLoading}
                              className="btn-secondary text-xs text-red-700 border-red-300 hover:bg-red-50"
                            >
                              Reject
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ─────────────────────────────────────────────
                STAGE 7: PROJECT COMPLETION
            ───────────────────────────────────────────── */}
            {currentStage === 'completed' && (
              <div className="space-y-6">
                <div className="saas-card p-8 text-center bg-white border border-slate-200">
                  <div className="w-16 h-16 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center text-3xl mx-auto mb-4 border border-emerald-100">
                    ✓
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900">Project Baseline Approved</h3>
                  <p className="text-sm text-slate-500 max-w-xl mx-auto mt-2">
                    '{activeProject.name}' requirements specification has completed the full agentic engineering lifecycle and has been formally approved for implementation.
                  </p>

                  <div className="flex flex-wrap items-center justify-center gap-4 mt-6">
                    <button
                      type="button"
                      onClick={() => handleDownloadPdf()}
                      className="btn-primary text-xs"
                    >
                      📄 Download Approved SRS (PDF)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownloadDocx()}
                      className="btn-secondary text-xs"
                    >
                      📝 Download Approved SRS (DOCX)
                    </button>
                    <button
                      onClick={() => setShowCreateModal(true)}
                      className="btn-secondary text-xs"
                    >
                      + Create Next Project
                    </button>
                  </div>
                </div>

                {/* Audit Trail Viewer */}
                <div className="saas-card p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-bold text-slate-900">Complete Immutable Audit Trail</h4>
                    <button
                      onClick={handleLoadAuditTrail}
                      className="btn-secondary text-xs py-1"
                    >
                      Refresh Logs
                    </button>
                  </div>

                  <div className="space-y-2 max-h-80 overflow-y-auto">
                    {auditTrail.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">Click Refresh to load recorded transaction audit logs.</p>
                    ) : (
                      auditTrail.map((log, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-semibold text-slate-800 capitalize">{log.agent || log.event_type}</span>
                            <span className="text-slate-400 mx-2">•</span>
                            <span className="text-slate-600">{log.action}</span>
                          </div>
                          <span className="text-slate-400 font-mono text-[11px]">{log.timestamp?.slice(0, 19).replace('T', ' ')}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* ─────────────────────────────────────────────
          MODAL: CREATE PROJECT
      ───────────────────────────────────────────── */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-md w-full p-6 animate-fade-in">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Financial Project</h3>
            <p className="text-xs text-slate-500 mb-4">
              Initialize a new requirements engineering lifecycle.
            </p>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={e => setNewProjectName(e.target.value)}
                  placeholder="e.g. Commercial Loan Origination Suite"
                  className="input-clean"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Scope Description</label>
                <textarea
                  value={newProjectDesc}
                  onChange={e => setNewProjectDesc(e.target.value)}
                  placeholder="Brief summary of domain requirements and objectives..."
                  className="input-clean h-20 resize-none text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">Domain Use Case</label>
                  <select
                    value={newProjectUseCase}
                    onChange={e => setNewProjectUseCase(e.target.value)}
                    className="input-clean text-xs"
                  >
                    <option value="loan_processing">Loan Processing</option>
                    <option value="digital_onboarding">Customer Onboarding</option>
                    <option value="payment_processing">Payment Processing</option>
                    <option value="fraud_detection">Fraud Detection</option>
                    <option value="regulatory_reporting">Regulatory Reporting</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                    Regulatory Jurisdiction
                  </label>
                  <select
                    value={newProjectJurisdiction}
                    onChange={e => setNewProjectJurisdiction(e.target.value)}
                    className="input-clean text-xs font-medium"
                  >
                    <optgroup label="India (South Asia)">
                      <option value="India">India — RBI Master Directions, DPDP Act 2023, PMLA</option>
                    </optgroup>
                    <optgroup label="North America">
                      <option value="United States">United States — Federal Reserve, OCC, CFPB, GLBA</option>
                      <option value="Canada">Canada — OSFI B-10 & B-13, PIPEDA, FINTRAC</option>
                    </optgroup>
                    <optgroup label="Europe & United Kingdom">
                      <option value="United Kingdom">United Kingdom — FCA Handbook, PRA, UK GDPR</option>
                      <option value="European Union">European Union — EBA Guidelines, GDPR, PSD2, AMLD5</option>
                    </optgroup>
                    <optgroup label="Asia-Pacific & Middle East">
                      <option value="Singapore">Singapore — MAS Technology Risk Guidelines, PDPA</option>
                      <option value="Australia">Australia — APRA CPS 234, Privacy Act 1988</option>
                      <option value="UAE / DIFC">UAE / DIFC — DFSA Regulatory Framework, Data Protection</option>
                    </optgroup>
                    <optgroup label="Global Standards">
                      <option value="International">International / Cross-Border — Basel III, FATF Directives</option>
                    </optgroup>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newProjectName.trim()}
                  className="btn-primary text-xs"
                >
                  Create & Start Interview
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────
          MODAL: PROJECT HISTORY
      ───────────────────────────────────────────── */}
      {showHistoryModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl border border-slate-200 max-w-lg w-full p-6 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900">Project History</h3>
              <button
                onClick={() => setShowHistoryModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg leading-none"
              >
                ×
              </button>
            </div>

            <div className="space-y-3 max-h-96 overflow-y-auto">
              {projects.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No projects found. Create your first project above.</p>
              ) : (
                projects.map((proj) => {
                  const isCurrent = activeProject?.id === proj.id;
                  return (
                    <div
                      key={proj.id}
                      className={`p-4 rounded-lg border text-xs transition-colors flex items-center justify-between ${
                        isCurrent
                          ? 'border-blue-500 bg-blue-50/20'
                          : 'border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <strong className="text-slate-900 text-sm">{proj.name}</strong>
                          {isCurrent && <span className="badge badge-blue">Active</span>}
                        </div>
                        <p className="text-slate-500 mt-0.5 capitalize">
                          {proj.use_case.replace('_', ' ')} • Stage: {proj.current_stage || 'interview'}
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {!isCurrent && (
                          <button
                            onClick={() => selectProject(proj, token)}
                            className="btn-secondary text-xs py-1"
                          >
                            Open
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleDownloadPdf(proj.id, proj.name)}
                          className="text-xs text-blue-600 hover:underline px-2 py-1"
                        >
                          SRS PDF
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
