# Architecture

## Stack
- **Backend:** Python 3.14 + FastAPI (async)
- **Frontend:** Next.js 15 + TypeScript + Tailwind CSS
- **Database:** SQLite + SQLAlchemy (async) — abstracts to PostgreSQL
- **Vector DB:** ChromaDB (local, in-process)
- **LLM:** Mock provider (dev) / OpenAI provider (production)
- **Auth:** JWT + bcrypt + RBAC (8 roles)

## Agent Architecture
Central `Orchestrator` state machine coordinates 13 specialised agents:
1. **Stakeholder Interaction** — adaptive interviews
2. **Requirement Extraction** — structured extraction from text/documents
3. **Clarification** — detects ambiguity, generates targeted questions
4. **Classification** — multi-label categorisation
5. **Conflict Detection** — contradictions and duplicates
6. **Compliance** — regulatory mapping (advisory only)
7. **Security & Privacy** — threat analysis and control recommendations
8. **Risk Analysis** — business, technical, compliance risk assessment
9. **SDLC Selection** — deterministic scoring + LLM rationale
10. **Documentation** — SRS, user stories, use cases, RTM generation
11. **Validation** — quality checks across 10 dimensions
12. **Human Approval** — routes decisions to required roles
13. **Coordinator** (Orchestrator) — pipeline execution, session state, audit

## Data Flow
```
Stakeholder Input / Document Upload
    → Ingestion (parse, chunk, embed)
    → Extraction Agent → raw requirements
    → Clarification Agent → targeted questions
    → Classification Agent → categorised requirements
    → Conflict Detection → flags conflicts/duplicates
    → Compliance Agent → regulatory mapping (advisory)
    → Security Agent → threat/control analysis
    → Risk Agent → risk assessment
    → Validation Agent → quality scoring
    → Human Approval → approved requirements
    → Documentation Agent → artefacts (SRS, RTM, etc.)
    → SDLC Agent → methodology recommendation
```

## Security Layers
1. JWT auth + RBAC (8 roles, permission matrix)
2. Input sanitization (control chars, length limits)
3. Prompt injection detection (15 patterns)
4. PII masking before LLM calls
5. Output sanitization (system prompt leakage)
6. Audit logging (all events)
