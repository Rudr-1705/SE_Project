# AIFRE — Agentic AI Financial Requirements Engineering

**An AI-powered platform for automating the Software Requirements Engineering lifecycle of financial systems.**

AIFRE is an intelligent, multi-agent requirements engineering platform that automates the end-to-end Software Requirements Engineering (RE) lifecycle. It guides analysts through adaptive stakeholder interviews, extracts structured requirements, performs multi-dimensional requirement analysis, recommends suitable SDLC methodologies, generates IEEE Std 29148-aligned Software Requirements Specification (SRS) documents, and supports human-in-the-loop approval workflows.

The platform is designed to improve the accuracy, consistency, traceability, and efficiency of requirements engineering, particularly in compliance-sensitive financial applications.

---

## Key Features

### 1. End-to-End Requirements Engineering Workflow

AIFRE provides a structured, sequential workflow:

`Registration/Login → Project Creation → Stakeholder Interview → Requirement Extraction → Multi-Agent Analysis → SDLC Recommendation → SRS Generation → Approval Sign-Off → Project Completion`

- Guided project creation and domain selection.
- Adaptive stakeholder interviews with context-aware follow-up questions.
- Automated extraction of functional and non-functional requirements.
- Structured requirement analysis across seven dimensions.
- SDLC methodology evaluation and recommendation.
- Automated SRS generation in PDF and DOCX formats.
- Human review, approval, rejection, and change-request workflows.

### 2. AI-Powered LLM Integration

AIFRE uses a configurable LLM provider architecture.

Supported providers include:

- **Ollama:** Local inference using Qwen3:4B.
- **OpenAI:** Configurable integration using GPT-4o.
- **Mock Provider:** Deterministic provider for testing and development.

Key capabilities:

- Structured JSON generation.
- Context-aware stakeholder interactions.
- Prompt and context management.
- Configurable inference parameters.
- Local inference support for CPU-based systems.

### 3. Multi-Agent Requirements Analysis

AIFRE uses specialized agents and workflow components to process stakeholder inputs and produce structured engineering artefacts.

**Stakeholder Interview and Extraction**
- Interview Agent: Conducts adaptive stakeholder interviews and asks relevant follow-up questions.
- Extraction Agent: Converts unstructured stakeholder responses into structured functional and non-functional requirements.

**Seven Analytical Dimensions**

1. **Clarification Analysis:** Identifies ambiguities, missing information, and incomplete requirements.
2. **Requirement Classification:** Categorizes requirements into functional, security, performance, data, and regulatory categories.
3. **Conflict Detection:** Identifies contradictory requirements, duplicates, and potential design trade-offs.
4. **Compliance Analysis:** Evaluates requirements against relevant regulatory and compliance considerations.
5. **Security and Privacy Analysis:** Identifies security threats, privacy concerns, and recommended security controls.
6. **Risk Assessment:** Evaluates potential risks based on likelihood, severity, and mitigation strategies.
7. **Requirement Validation:** Evaluates completeness, consistency, testability, and traceability.

**Additional Engineering Components**
- SDLC Recommendation Agent: Compares development methodologies using a multi-criteria evaluation approach.
- SRS Generator: Produces structured IEEE-aligned SRS documents.
- Documentation and Orchestration Components: Coordinate workflow execution, document generation, and application state synchronization.

### 4. SDLC Methodology Recommendation

AIFRE evaluates multiple software development methodologies, including:

- Agile
- Waterfall
- V-Model
- Spiral
- Hybrid Agile V-Model

The recommendation process considers project characteristics, requirements complexity, security sensitivity, regulatory considerations, and development constraints.

It provides comparative scores and qualitative reasoning to help stakeholders select an appropriate development methodology.

### 5. IEEE Std 29148-Aligned SRS Generation

AIFRE automatically generates structured Software Requirements Specification documents.

Features include:

- IEEE Std 29148-aligned document organization.
- Eleven structured SRS sections.
- Functional and non-functional requirements.
- Requirement priorities and acceptance criteria.
- System interfaces and constraints.
- Security and regulatory considerations.
- Risk documentation and requirement traceability.
- PDF generation with headers, footers, tables, and page numbering.
- Editable DOCX generation.
- Document preview and download functionality.

### 6. Human-in-the-Loop Governance

AIFRE incorporates a human review and approval workflow to ensure that generated requirements and documents can be reviewed before finalization.

Supported actions include:

- Approve
- Reject
- Request Changes

The system maintains approval records and audit logs to support accountability and traceability throughout the sign-off process.

### 7. Security and Authentication

The platform incorporates:

- JWT-based authentication.
- Bcrypt password hashing.
- Authenticated API requests.
- Project ownership checks.
- Controlled approval workflows.
- Audit logging for important application actions.

---

## System Architecture

AIFRE follows a modular architecture consisting of a Next.js frontend, FastAPI backend, specialized agent components, a persistence layer, and an LLM provider gateway.

```text
                  ┌──────────────────────────────┐
                  │       Next.js Frontend       │
                  │    React + Tailwind CSS      │
                  └──────────────┬───────────────┘
                                 │
                           HTTP / REST
                                 │
                  ┌──────────────▼───────────────┐
                  │        FastAPI Backend       │
                  │       API Gateway             │
                  └──────────────┬───────────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             │                   │                   │
    ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
    │   Agent Engine  │ │ Persistence     │ │  LLM Gateway    │
    │                 │ │ Layer           │ │                 │
    │ Interview       │ │ SQLite          │ │ Ollama          │
    │ Extraction      │ │ SQLAlchemy      │ │ Qwen3:4B        │
    │ Analysis        │ │ ChromaDB        │ │ OpenAI           │
    │ SDLC            │ │                 │ │ Mock Provider    │
    │ SRS Generation  │ │                 │ │                 │
    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Async Database Access | aiosqlite |
| LLM Integration | Ollama, OpenAI |
| Local LLM | Qwen3:4B |
| Vector Storage | ChromaDB |
| Authentication | JWT, Bcrypt |
| Document Generation | ReportLab, python-docx |
| API Communication | REST |

---

## Quick Start Guide

### Prerequisites

- Python 3.11+
- Node.js 20+ recommended
- npm
- Ollama (for local LLM inference)

### Step 1: Clone the Repository

```bash
git clone https://github.com/Rudr-1705/SE_Project.git
cd SE_Project
```

### Step 2: Configure the LLM

Install Ollama from:

https://ollama.com

Pull the recommended local model:

```bash
ollama pull qwen3:4b
```

Ensure the Ollama service is running.

```bash
ollama serve
```

If using another configured provider, configure the appropriate environment variables instead.

### Step 3: Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate it.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

Update the environment configuration according to your selected LLM provider.

Start the backend:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

The backend will be available at:

`http://localhost:8000`

Interactive API documentation:

`http://localhost:8000/docs`

### Step 4: Frontend Setup

Open a separate terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Configure the frontend environment:

```bash
cp .env.example .env.local
```

Start the development server:

```bash
npm run dev
```

Open:

`http://localhost:3000`

---

## Project Demonstration Guide

The following demonstration uses a **Secure Payment Processing Platform** as an example project.

### Stage 1: Authentication

- Open the application at `http://localhost:3000`.
- Register a new user account.
- Log in using the registered credentials.
- Demonstrate authenticated access and session persistence.

### Stage 2: Project Creation

Create a project using the following details:

**Project Name:** SecurePay – Payment Processing Platform

**Domain Use Case:** Payment Processing

**Description:**

A secure payment processing platform that enables customers and merchants to perform seamless digital transactions. The system validates payment details, authorizes transactions, prevents duplicate payments, manages refunds, detects suspicious activities, and maintains secure transaction records while ensuring regulatory compliance.

### Stage 3: Adaptive Stakeholder Interview

Introduce the AI interviewer and demonstrate how it gathers project-specific information through contextual questions.

Example stakeholder response:

> The platform should support secure digital payments for customers and merchants. It must validate payment information, authorize transactions, prevent duplicate payments, process refunds, and maintain transaction records. Sensitive payment information must be protected through encryption and secure authentication. Suspicious transactions should be flagged for further verification.

Highlight how the interviewer uses stakeholder responses to generate relevant follow-up questions.

### Stage 4: Requirement Extraction and Analysis

Complete the interview and trigger requirement extraction.

Demonstrate how AIFRE converts stakeholder responses into structured functional and non-functional requirements.

Explain the seven analytical dimensions:

1. Clarification Analysis
2. Requirement Classification
3. Conflict Detection
4. Compliance Analysis
5. Security and Privacy Analysis
6. Risk Assessment
7. Requirement Validation

Show the identified ambiguities, requirement categories, conflicts, compliance considerations, security findings, risks, and validation results.

### Stage 5: SDLC Recommendation

Demonstrate the comparative evaluation of:

- Agile
- Waterfall
- V-Model
- Spiral
- Hybrid Agile V-Model

Explain how the recommendation is influenced by project complexity, security requirements, regulatory considerations, and development constraints.

### Stage 6: SRS Generation

Generate the IEEE Std 29148-aligned SRS document.

Demonstrate:

- Structured SRS preview.
- Functional and non-functional requirements.
- System interfaces and constraints.
- Security and compliance requirements.
- Risk documentation.
- Requirement traceability.

Download both PDF and DOCX versions and demonstrate the generated document structure.

### Stage 7: Approval and Completion

Navigate to the approval stage.

Demonstrate the available review actions:

- Approve
- Reject
- Request Changes

Submit reviewer feedback and demonstrate the persistence of approval decisions and audit records.

After successful approval, navigate to the completion stage and download the approved SRS document.

---

## Project Structure

```text
SE_Project/
│
├── backend/
│   ├── agents/
│   │   ├── interview.py
│   │   ├── extraction.py
│   │   ├── clarification.py
│   │   ├── classification.py
│   │   ├── conflict.py
│   │   ├── compliance.py
│   │   ├── security.py
│   │   ├── risk.py
│   │   ├── validation.py
│   │   ├── sdlc.py
│   │   ├── srs_generator.py
│   │   ├── documentation.py
│   │   └── orchestrator.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── requirements.py
│   │   ├── sdlc.py
│   │   ├── srs.py
│   │   └── approvals.py
│   │
│   ├── llm/
│   │   ├── gateway.py
│   │   └── providers/
│   │       ├── ollama_provider.py
│   │       ├── openai_provider.py
│   │       └── mock.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── security/
│   ├── scripts/
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx
│   │   │   ├── layout.tsx
│   │   │   ├── globals.css
│   │   │   └── icons.tsx
│   │   └── lib/
│   │       └── api.ts
│   │
│   └── package.json
│
├── docs/
├── .gitignore
└── README.md
```

---

## Testing and Verification

AIFRE includes backend tests and frontend build checks to validate application functionality.

### Backend Tests

Navigate to the backend directory and run:

```bash
python test_e2e.py
```

Additional test suites cover areas such as:

- Backend stabilization.
- Multi-agent pipeline and governance.
- Security and workflow behavior.

Run the available test suites individually as required.

### Frontend TypeScript Check

Navigate to the frontend directory:

```bash
npx tsc --noEmit
```

### Frontend Production Build

```bash
npm run build
```

These checks help identify type errors, compilation issues, and regressions before deployment.

---

## Security and Compliance Considerations

AIFRE is designed to support requirements engineering for financial applications where security, privacy, and regulatory considerations are important.

Depending on the project jurisdiction and use case, the platform can analyze requirements related to:

- Know Your Customer (KYC).
- Anti-Money Laundering (AML).
- Payment security and PCI DSS.
- RBI payment-related regulations.
- Applicable data protection requirements.
- Encryption and secure communication.
- Authentication and access control.
- Auditability and requirement traceability.

Regulatory applicability and compliance conclusions must be validated against the actual jurisdiction, system scope, and applicable regulatory guidance.

AIFRE provides engineering analysis and documentation support; it does not independently certify regulatory compliance.

---

## Future Enhancements

Potential areas for further development include:

- Expanded LLM provider support.
- More sophisticated requirement traceability.
- Enhanced regulatory knowledge bases.
- Advanced stakeholder collaboration.
- Improved analytical evaluation metrics.
- Additional document export and integration capabilities.

---

## License

Academic and Research Use.

Developed as an academic Software Engineering project focused on applying Agentic AI to Financial Requirements Engineering.

---

**AIFRE — Transforming Financial Requirements Engineering through Agentic AI.**
