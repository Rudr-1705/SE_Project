# AIFRE — Agentic AI Financial Requirements Engineering

A production-grade, multi-agent AI platform that automates the end-to-end Software Requirements Engineering (RE) lifecycle for financial systems. Designed in compliance with IEEE Std 29148, AIFRE guides analysts through adaptive stakeholder interviews, extracts structured requirements, executes 7-dimension analytical audits, determines the optimal SDLC methodology, generates downloadable IEEE-aligned SRS documents (PDF & DOCX), and enforces cryptographic human-in-the-loop approval workflows.

---

##  Key Capabilities

1. **Sequential SaaS Workflow**:
   - Streamlined, distraction-free wizard eliminating dashboard clutter.
   - Sequential flow: `Register/Login → Create Project → Stakeholder Interview → Extraction → Analysis (7 Agents) → SDLC Selection → SRS Generation → Approval Sign-Off → Project Completion`.
2. **Local LLM First (Ollama + Qwen3:4B)**:
   - Configurable LLM provider architecture supporting Ollama (`qwen3:4b`), OpenAI (`gpt-4o`), and deterministic test mock.
   - Optimized for local 16GB RAM CPU systems with non-thinking mode and thread tuning.
   - Resilient structured JSON outputs, markdown stripping, and prompt context isolation.
3. **Multi-Agent Requirements Analysis**:
   - **Interview Agent**: Adaptive questioning with context tracking and domain-specific follow-ups.
   - **Extraction Agent**: Extracts Functional (`FR-LOAN-XXX`) and Non-Functional (`NFR-SEC-XXX`, `NFR-PERF-XXX`) requirements with priorities and acceptance criteria.
   - **Clarification Agent**: Detects ambiguities and flags missing details.
   - **Classification Agent**: Categorizes requirements into functional, security, performance, data, and regulatory tiers.
   - **Conflict Detection Agent**: Identifies contradictions, duplicates, and architectural trade-offs.
   - **Compliance Agent**: Cross-references requirements against KYC, AML, and Data Protection directives with regulatory citations.
   - **Security Agent**: Threat modeling, STRIDE mapping, and confidentiality/integrity control assignment.
   - **Risk Analysis Agent**: Evaluates risk severity, likelihood, and mitigation strategies.
   - **Validation Agent**: Quantitative scoring of completeness, consistency, testability, and traceability.
   - **SDLC Recommendation Agent**: Multi-criteria weighted matrix with qualitative architectural rationale.
4. **IEEE Std 29148 SRS Document Generator**:
   - Generates fully populated, professional **PDF** (with headers, footers, page numbering) and editable **DOCX** files across all 11 IEEE sections.
   - Dedicated preview and one-click download endpoints.
5. **Human-in-the-Loop Governance & Audit Trail**:
   - Role-Based Access Control (RBAC) with cryptographic JWT and bcrypt password hashing.
   - Formal sign-off gates (Approve, Reject, Request Changes) with immutable audit logging.

---

##  Architecture

```
                                  ┌─────────────────────────────┐
                                  │      Next.js Frontend       │
                                  │   (Tailwind SaaS Wizard)    │
                                  └──────────────┬──────────────┘
                                                 │ HTTP / REST (JWT)
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │       FastAPI Gateway       │
                                  │  (/api/auth, /api/projects) │
                                  └──────────────┬──────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
       ┌───────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────┐
       │     Agent Engine      │   │     Persistence Layer     │   │      LLM Gateway      │
       │  13 Specialized Agents│   │   SQLite + SQLAlchemy     │   │  Ollama (Qwen3:4B)    │
       │  (Extraction, SDLC,   │   │   (aiosqlite + Schema     │   │  OpenAI (GPT-4o)      │
       │   Compliance, SRS)    │   │    Migrations + Chroma)   │   │  Deterministic Mock   │
       └───────────────────────┘   └───────────────────────────┘   └───────────────────────┘
```

---

##  Quick Start Guide

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (Node 20+ recommended)
- **Ollama**: (Optional for local LLM inference)

---

### Step 1: LLM Setup (Ollama with Qwen3:4B)

1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Start the Ollama background daemon:
   ```bash
   ollama serve
   ```
3. In a separate terminal, pull the recommended Qwen3:4B model (fast & lean for 16GB RAM CPU systems):
   ```bash
   ollama pull qwen3:4b
   ```
   *(Note: If running without Ollama, you can set `LLM_PROVIDER=mock` in `backend/.env` for instant offline testing.)*

---

### Step 2: Backend Setup

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
5. Start the backend server:
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Backend will be running at `http://localhost:8000`. Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

---

### Step 3: Frontend Setup

1. Open a new terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env.local
   ```
4. Start the development server:
   ```bash
   npm run dev
   ```
5. Open your browser and navigate to `http://localhost:3000`.

---

### Step 4: Run Automated Verification Tests

Verify that all 13 stages of the pipeline and API work correctly:
```bash
cd backend
python test_e2e.py
```
Expected output:
```
[PASS] ALL 13 END-TO-END TESTS PASSED SUCCESSFULLY
```

---

##  Step-by-Step Demo Procedure for Professor Evaluation

Follow this structured script when presenting AIFRE to professors, committee members, or evaluators:

### 1. Introduction & Theoretical Motivation (1–2 minutes)
- **Core Problem**: Traditional Requirements Engineering in financial software is manual, slow, error-prone, and heavily penalized by regulatory oversights (KYC, AML, GDPR).
- **Solution**: AIFRE provides an Agentic AI architecture that guides non-technical stakeholders from initial elicitation to a signed-off IEEE Std 29148 SRS with full regulatory traceability.

### 2. Live Walkthrough & Demonstration (5–7 minutes)

#### Stage 1: Authentication & Zero-Mock Security
- Open `http://localhost:3000`.
- Show that no hardcoded demo accounts exist. Register a new user:
  - Full Name: `Prof. Evaluator`
  - Email: `evaluator@university.edu`
  - Password: `SecurePassword123!`
  - Role: `Admin` / `Project Manager`
- Log in and demonstrate JWT token persistence across page refreshes (`F5`).

#### Stage 2: Project Creation
- Enter the project details:
  - **Project Name**: `NextGen Commercial Lending Platform`
  - **Description**: `Cloud-native SME loan underwriting system with biometric KYC, automated credit decisioning, and AML sanctions screening.`
  - **Domain**: `Loan Processing`
- Click **Create Project & Begin Interview**. Note that the user is immediately routed into the sequential wizard.

#### Stage 3: Adaptive Stakeholder Interview
- Point out the AI Lead Interviewer.
- Provide a rich financial response:
  > *"We need an automated loan origination platform for retail borrowers. The system must verify identity through government ID scanning and facial biometrics. Decisions must execute under 30 seconds. All customer data must be encrypted with AES-256. Audit records must be retained for 7 years according to banking directives."*
- Click **Submit Answer**. Highlight that the AI tracks conversation turns and poses context-aware follow-up questions.
- Click **Complete Interview & Extract Requirements**.

#### Stage 4: Requirement Extraction & Analysis
- **Requirement Extraction**: Show how unstructured interview transcript text is parsed into formal Functional (`FR-LOAN-XXX`) and Non-Functional (`NFR-SEC-XXX`, `NFR-PERF-XXX`) requirements with priorities and testable acceptance criteria.
- **7-Dimension Analysis**:
  - Show the **Clarification** items identifying ambiguities.
  - Show the **Classification** table (Security, Functional, Usability, Performance).
  - Show the **Conflict Detection** card identifying design trade-offs.
  - Show the **Compliance Analysis** panel linking requirements to KYC and AML directives.
  - Show the **Security & Privacy** analysis with STRIDE threat categorizations.
  - Show the **Risk Register** with likelihood, severity, and mitigation plans.
  - Show the **Validation Scores** (Completeness, Testability, Traceability).

#### Stage 5: SDLC Methodology Recommendation
- Show the quantitative evaluation comparing Agile, V-Model, Hybrid Agile V-Model, Waterfall, and Spiral.
- Explain why Hybrid Agile V-Model or V-Model is ranked highest due to strict compliance overhead and high security sensitivity.

#### Stage 6: IEEE 29148 SRS Document Generation
- Click **Generate IEEE 29148 SRS Document**.
- Display the live structured preview with all 11 IEEE sections.
- Click **Download PDF** and open the resulting PDF. Show the running headers, section numbering, tables, and page numbers.
- Click **Download DOCX** to show the editable Word document.

#### Stage 7: Governance Sign-Off & Audit Trail
- Move to the **Approval** stage.
- Point out the pending baseline approval sign-off request.
- Add reviewer feedback: *"Verified against statutory KYC/AML directives and IEEE 29148 standards. Approved for sprint backlog."*
- Click **Approve**.
- Show the completed project status, immutable audit trail timestamps, and previous project history retrieval.

---

##  Project Structure

```
SE_Project/
├── backend/
│   ├── agents/               # 13 Specialized AI Agents
│   │   ├── interview.py      # Adaptive elicitation
│   │   ├── extraction.py     # Unstructured to structured extraction
│   │   ├── clarification.py  # Ambiguity detection
│   │   ├── classification.py # Requirement categorization
│   │   ├── conflict.py       # Contradiction & trade-off detection
│   │   ├── compliance.py     # Regulatory compliance checker
│   │   ├── security.py       # Threat modeling & security controls
│   │   ├── risk.py           # Risk assessment & mitigation
│   │   ├── validation.py     # Completeness & testability scoring
│   │   ├── sdlc.py           # Multi-criteria SDLC recommendation
│   │   ├── srs_generator.py  # IEEE Std 29148 PDF & DOCX generator
│   │   ├── documentation.py  # Artefact coordinator
│   │   └── orchestrator.py   # State machine & database synchronization
│   ├── api/                  # FastAPI REST Routers
│   │   ├── auth.py           # Register, login, logout, token refresh
│   │   ├── projects.py       # Project lifecycle and stage progression
│   │   ├── requirements.py   # Extraction and analytical pipelines
│   │   ├── sdlc.py           # SDLC recommendation & audit logs
│   │   ├── srs.py            # SRS generation and download endpoints
│   │   └── approvals.py      # Governance and review actions
│   ├── llm/                  # LLM Provider Abstraction
│   │   ├── gateway.py        # Dynamic provider routing
│   │   └── providers/
│   │       ├── ollama_provider.py # Native Ollama HTTP client (Qwen3:4B)
│   │       ├── openai_provider.py # OpenAI client (GPT-4o)
│   │       └── mock.py            # Dynamic prompt-aware test provider
│   ├── models/               # SQLAlchemy Async Models
│   ├── security/             # JWT, Bcrypt, RBAC
│   ├── test_e2e.py           # 13-stage end-to-end test suite
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx      # Unified Sequential SaaS Wizard UI
│   │   │   ├── layout.tsx    # Root layout & font stack
│   │   │   └── globals.css   # Light SaaS design system & components
│   │   └── lib/
│   │       └── api.ts        # Typed API client
│   └── package.json          # Next.js dependencies & scripts
├── docs/                     # Architecture & design specifications
├── .env.example              # Root environment template
└── README.md                 # Project documentation
```

---

##  License
Academic and Research Use — Developed for Software Requirements Engineering.
