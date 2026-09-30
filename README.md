# AIFRE — Agentic AI Financial Requirements Engineering

A multi-agent AI platform for automated requirements engineering of financial systems, featuring adaptive stakeholder interviews, RAG-grounded compliance analysis, SDLC methodology selection, and human-in-the-loop approval workflows.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+

### Backend
```bash
cd backend
pip install -r requirements.txt
pip install "sqlalchemy[asyncio]" greenlet
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Run Tests
```bash
cd backend
python test_e2e.py
```

## Architecture

**13 specialised AI agents** coordinated by a central orchestrator:

```
Stakeholder Interview → Extraction → Clarification → Classification
→ Conflict Detection → Compliance → Security → Risk Analysis
→ Validation → Documentation → SDLC Selection → Human Approval
```

### Key Features
- **Adaptive Interviews** — context-aware stakeholder questioning
- **RAG-Grounded Analysis** — evidence-based compliance with citations
- **13 Agent Pipeline** — each agent has specific responsibilities and escalation logic
- **SDLC Selection** — deterministic multi-criteria scoring + LLM rationale
- **Human Approval** — role-based approval gates for critical decisions
- **Audit Trail** — immutable logging of all actions and decisions
- **Requirement Versioning** — full history, never destructive
- **Security** — prompt injection detection, PII masking, RBAC (8 roles)
- **Evaluation Framework** — 13 test cases across 9 categories

### Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI (async) |
| Frontend | Next.js + TypeScript + Tailwind |
| Database | SQLite + SQLAlchemy |
| Vector DB | ChromaDB |
| LLM | Mock provider (dev) / OpenAI (prod) |
| Auth | JWT + bcrypt + RBAC |

## Documentation
See `docs/` for:
- [Architecture](docs/ARCHITECTURE.md)
- [Agents](docs/AGENTS.md)
- [Security](docs/SECURITY.md)
- [Evaluation](docs/EVALUATION.md)
- [RAG Policy](docs/RAG_POLICY.md)
- [Requirements Schema](docs/REQUIREMENTS_SCHEMA.md)
- [Engineering Decisions](docs/DECISIONS.md)

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System health check |
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/projects` | POST/GET | Project CRUD |
| `/api/projects/{id}/interview/start` | POST | Start stakeholder interview |
| `/api/projects/{id}/interview/answer` | POST | Answer interview question |
| `/api/projects/{id}/requirements/extract` | POST | Extract requirements |
| `/api/projects/{id}/requirements/analyse` | POST | Run analysis pipeline |
| `/api/projects/{id}/sdlc/analyse` | POST | SDLC recommendation |
| `/api/projects/{id}/artefacts/generate` | POST | Generate SRS, RTM, etc. |
| `/api/projects/{id}/approvals` | POST/GET | Approval workflow |
| `/api/projects/{id}/audit-trail` | GET | Audit trail |
| `/api/evaluation/run` | POST | Run evaluation framework |
