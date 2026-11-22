/**
 * Typed API client for the AIFRE backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

type FetchOptions = {
  method?: string;
  body?: any;
  token?: string;
  isFormData?: boolean;
};

export async function apiFetch<T = any>(path: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, token, isFormData = false } = options;

  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isFormData) headers['Content-Type'] = 'application/json';

  const config: RequestInit = { method, headers };
  if (body) {
    config.body = isFormData ? body : JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}${path}`, config);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── Auth ──
export const authAPI = {
  register: (data: { email: string; password: string; full_name: string; role?: string }) =>
    apiFetch('/auth/register', { method: 'POST', body: data }),

  login: (data: { email: string; password: string }) =>
    apiFetch('/auth/login', { method: 'POST', body: data }),

  getMe: (token: string) =>
    apiFetch('/auth/me', { token }),

  logout: (token: string) =>
    apiFetch('/auth/logout', { method: 'POST', token }).catch(() => {}),
};

// ── Projects ──
export const projectsAPI = {
  list: (token: string) =>
    apiFetch('/projects', { token }),

  create: (token: string, data: { name: string; description?: string; use_case?: string }) =>
    apiFetch('/projects', { method: 'POST', body: data, token }),

  get: (token: string, id: string) =>
    apiFetch(`/projects/${id}`, { token }),

  updateStage: (token: string, id: string, stage: string) =>
    apiFetch(`/projects/${id}/stage`, { method: 'PUT', body: { stage }, token }),
};

// ── Interview ──
export const interviewAPI = {
  start: (token: string, projectId: string, role = 'business_analyst') =>
    apiFetch(`/projects/${projectId}/interview/start?stakeholder_role=${role}`, { method: 'POST', token }),

  answer: (token: string, projectId: string, answer: string) =>
    apiFetch(`/projects/${projectId}/interview/answer?answer=${encodeURIComponent(answer)}`, { method: 'POST', token }),

  getHistory: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/interview/history`, { token }),
};

// ── Requirements ──
export const requirementsAPI = {
  list: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/requirements`, { token }),

  extract: (token: string, projectId: string, text = '') =>
    apiFetch(`/projects/${projectId}/requirements/extract${text ? `?text=${encodeURIComponent(text)}` : ''}`, { method: 'POST', token }),

  analyse: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/requirements/analyse`, { method: 'POST', token }),

  getAnalysisResults: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/requirements/analysis-results`, { token }),
};

// ── SDLC ──
export const sdlcAPI = {
  analyse: (token: string, projectId: string, factors?: any) =>
    apiFetch(`/projects/${projectId}/sdlc/analyse`, { method: 'POST', body: factors, token }),

  getResult: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/sdlc/result`, { token }),
};

// ── SRS Document ──
export const srsAPI = {
  generate: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/srs/generate`, { method: 'POST', token }),

  preview: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/srs/preview`, { token }),

  getPdfDownloadUrl: (projectId: string) =>
    `${API_BASE}/projects/${projectId}/srs/download/pdf`,

  getDocxDownloadUrl: (projectId: string) =>
    `${API_BASE}/projects/${projectId}/srs/download/docx`,
};

// ── Approvals ──
export const approvalsAPI = {
  list: (token: string, projectId: string, status = '') =>
    apiFetch(`/projects/${projectId}/approvals${status ? `?status=${status}` : ''}`, { token }),

  action: (token: string, projectId: string, approvalId: string, action: string, comments = '') =>
    apiFetch(`/projects/${projectId}/approvals/${approvalId}/action`, {
      method: 'POST',
      body: { action, comments },
      token,
    }),
};

// ── Audit & Session ──
export const sessionAPI = {
  getState: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/session`, { token }),

  getAuditTrail: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/audit-trail`, { token }),
};
