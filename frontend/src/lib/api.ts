/**
 * API client for the AIFRE backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

type FetchOptions = {
  method?: string;
  body?: any;
  token?: string;
  isFormData?: boolean;
};

async function apiFetch<T = any>(path: string, options: FetchOptions = {}): Promise<T> {
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
};

// ── Projects ──
export const projectsAPI = {
  list: (token: string) =>
    apiFetch('/projects', { token }),

  create: (token: string, data: { name: string; description?: string; use_case?: string }) =>
    apiFetch('/projects', { method: 'POST', body: data, token }),

  get: (token: string, id: string) =>
    apiFetch(`/projects/${id}`, { token }),
};

// ── Requirements ──
export const requirementsAPI = {
  list: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/requirements`, { token }),

  create: (token: string, projectId: string, data: any) =>
    apiFetch(`/projects/${projectId}/requirements`, { method: 'POST', body: data, token }),

  extract: (token: string, projectId: string, text: string, sourceType = 'conversation') =>
    apiFetch(`/projects/${projectId}/requirements/extract?text=${encodeURIComponent(text)}&source_type=${sourceType}`, { method: 'POST', token }),

  analyse: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/requirements/analyse`, { method: 'POST', token }),
};

// ── Documents ──
export const documentsAPI = {
  list: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/documents`, { token }),

  upload: (token: string, projectId: string, file: File, docType = 'general') => {
    const form = new FormData();
    form.append('file', file);
    form.append('doc_type', docType);
    form.append('title', file.name);
    return apiFetch(`/projects/${projectId}/documents`, {
      method: 'POST', body: form, token, isFormData: true,
    });
  },
};

// ── SDLC ──
export const sdlcAPI = {
  analyse: (token: string, projectId: string, factors?: any) =>
    apiFetch(`/projects/${projectId}/sdlc/analyse`, { method: 'POST', body: factors, token }),

  getResult: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/sdlc/result`, { token }),
};

// ── Artefacts ──
export const artefactsAPI = {
  generate: (token: string, projectId: string, type: string, name = '') =>
    apiFetch(`/projects/${projectId}/artefacts/generate?artefact_type=${type}&project_name=${encodeURIComponent(name)}`, { method: 'POST', token }),
};

// ── Interview ──
export const interviewAPI = {
  start: (token: string, projectId: string, role = 'business_analyst') =>
    apiFetch(`/projects/${projectId}/interview/start?stakeholder_role=${role}`, { method: 'POST', token }),

  answer: (token: string, projectId: string, answer: string) =>
    apiFetch(`/projects/${projectId}/interview/answer?answer=${encodeURIComponent(answer)}`, { method: 'POST', token }),
};

// ── Approvals ──
export const approvalsAPI = {
  list: (token: string, projectId: string, status = '') =>
    apiFetch(`/projects/${projectId}/approvals${status ? `?status=${status}` : ''}`, { token }),

  create: (token: string, projectId: string, data: any) =>
    apiFetch(`/projects/${projectId}/approvals`, { method: 'POST', body: data, token }),

  action: (token: string, projectId: string, approvalId: string, data: any) =>
    apiFetch(`/projects/${projectId}/approvals/${approvalId}/action`, { method: 'POST', body: data, token }),
};

// ── Session/Audit ──
export const sessionAPI = {
  getState: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/session`, { token }),

  getAuditTrail: (token: string, projectId: string) =>
    apiFetch(`/projects/${projectId}/audit-trail`, { token }),
};

// ── System ──
export const systemAPI = {
  health: () => apiFetch('/health'),

  runEvaluation: () => apiFetch('/evaluation/run', { method: 'POST' }),

  getTestCases: () => apiFetch('/evaluation/test-cases'),
};
