# Engineering Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database | SQLite + SQLAlchemy async | Zero-config for prototype; ORM abstracts to PostgreSQL |
| Vector DB | ChromaDB (in-process) | No external service needed; pip install |
| LLM | Mock provider (dev) | Full pipeline runs without API key; OpenAI interface ready |
| Embeddings | ChromaDB default (local) | No API key; sentence-transformers optional |
| Auth | JWT + bcrypt | Simple, stateless, no external IdP dependency |
| RBAC | Permission matrix dict | 8 roles × resource/action; no complex framework needed |
| Agent I/O | Pydantic AgentInput/AgentOutput | Typed, validated, serializable |
| SDLC scoring | Weighted multi-criteria | Deterministic, reproducible, transparent |
| Versioning | Immutable RequirementVersion table | Never destroys history; full snapshot stored |
| Frontend | Next.js + TypeScript + Tailwind | Rich interactive UI, type safety |
| Compliance | Advisory only + human escalation | LLM never final authority on legal/compliance |
| Prompt injection | 15 regex patterns + output sanitization | Defense in depth; patterns detect common attacks |
| PII masking | Regex-based before LLM calls | SSN, credit card, email, account numbers masked |
| Knowledge base | Seeded at startup from code | 10 loan-processing domain items; extensible via document upload |
| Audit | Immutable AuditLog table + orchestrator trail | Dual audit: DB-level + agent-level |
| MFA | Deferred to production | Spec requires it but prototype uses JWT; documented in SECURITY.md |
