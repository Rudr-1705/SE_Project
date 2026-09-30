# Security

## Implemented
- **JWT Authentication** — bcrypt password hashing, configurable token expiry
- **RBAC** — 8 roles (admin, project_manager, business_analyst, architect, security_officer, compliance_officer, stakeholder, auditor) with permission matrix
- **Input Sanitization** — control character removal, length limits
- **Prompt Injection Detection** — 15 regex patterns covering common attack vectors
- **PII Masking** — SSN, credit card, email, account numbers masked before LLM calls
- **Output Sanitization** — system prompt leakage prevention
- **File Validation** — type allowlist, size limits
- **Audit Logging** — immutable AuditLog table + agent-level audit trail
- **Secret Management** — no hardcoded secrets, env-based configuration
- **Agent Permissions** — least-privilege per agent

## Deferred to Production
- **MFA** — spec requires it; prototype uses JWT only
- **Encryption at Rest** — SQLite doesn't natively encrypt; use SQLCipher or PostgreSQL with TDE
- **TLS** — development uses HTTP; production requires TLS 1.3
- **Session Isolation** — basic project-level isolation in prototype
- **Data Retention Policies** — framework exists but enforcement deferred

## Required Credentials
- `SECRET_KEY` — JWT signing key (auto-generated if not set)
- `OPENAI_API_KEY` — only if using OpenAI provider (mock works without it)
