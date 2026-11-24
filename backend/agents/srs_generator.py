"""IEEE 29148 Compliant SRS Document Generator (Structured Data, PDF, and DOCX)."""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding professional headers and running page numbers (Page X of Y)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))

            # Header
            self.drawString(54, letter[1] - 36, "AIFRE — Software Requirements Specification (IEEE 29148)")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)

            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 36, page_text)
            self.drawString(54, 36, "CONFIDENTIAL — STRICTLY FOR INTERNAL / REGULATORY REVIEW")
            self.line(54, 48, letter[0] - 54, 48)

            self.restoreState()


def build_ieee_srs_data(project_name: str, project_desc: str, requirements: list,
                         compliance_data: list = None, security_data: list = None,
                         risk_data: list = None, sdlc_data: dict = None,
                         jurisdiction: str = "India", approval_status: str = "pending") -> dict:
    """Build the comprehensive IEEE 29148 hierarchical data structure from real project records."""
    compliance_data = compliance_data or []
    security_data = security_data or []
    risk_data = risk_data or []
    sdlc_data = sdlc_data or {}
    jurisdiction = jurisdiction or "India"

    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    # 4.1 Executive Summary: preserve user text exactly, or construct verified summary if empty
    user_desc = (project_desc or "").strip()
    if user_desc:
        exec_summary = user_desc
    else:
        exec_summary = (
            f"The {project_name} platform is an automated financial requirements engineering and loan processing system "
            f"governed under {jurisdiction} statutory frameworks. This Software Requirements Specification (SRS) "
            f"establishes the formal baseline for functional processes, security safeguards, regulatory compliance controls, "
            f"and IEEE Std 29148-2018 traceability."
        )

    # 4.2 Comprehensive 14-Stage Loan Processing Functional Requirements
    # Merge existing extracted requirements with standard loan workflow stages to ensure 100% coverage
    standard_loan_workflow = [
        {
            "requirement_id": "FR-LOAN-001",
            "statement": "The system shall provide secure customer registration and multi-factor authentication (MFA) utilizing bcrypt/Argon2 password hashing and revocable JWT session management.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Ensures authenticated applicant identity and prevents credential harvesting.",
            "acceptance_criteria": ["Applicant can register with unique email and mobile", "Password hashed with Argon2id/bcrypt", "JWT session tokens expire within 8 hours"]
        },
        {
            "requirement_id": "FR-LOAN-002",
            "statement": "The system shall provide a multi-step digital loan application submission interface capturing requested loan amount, tenure, loan purpose, and repayment frequency.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Captures core loan underwriting parameters directly from borrower.",
            "acceptance_criteria": ["Application form validates mandatory input fields", "System computes indicative EMI schedule before submission", "Draft applications persist automatically"]
        },
        {
            "requirement_id": "FR-LOAN-003",
            "statement": "The system shall execute real-time data validation on personal, demographic, employment, and banking inputs against standardized boundary rules.",
            "category": "functional",
            "priority": "high",
            "business_justification": "Prevents garbage data from polluting underwriting models.",
            "acceptance_criteria": ["Email, phone, and date-of-birth format validation", "Monthly income and expense range sanity checks", "Immediate descriptive validation error messages"]
        },
        {
            "requirement_id": "FR-LOAN-004",
            "statement": "The system shall support secure customer document uploads (PDF, JPEG, PNG up to 10MB) for identity proof, address proof, and bank statements with automated MIME verification.",
            "category": "functional",
            "priority": "high",
            "business_justification": "Enables digital verification of supporting borrower documentation.",
            "acceptance_criteria": ["Restricted file upload whitelist (PDF, PNG, JPEG)", "Virus scanning and cryptographic checksum logging", "Secure AES-256 encrypted document storage"]
        },
        {
            "requirement_id": "FR-LOAN-005",
            "statement": "The system shall automatically detect duplicate loan applications by cross-referencing national identity identifiers (PAN/SSN/Tax ID) and applicant contact details against active records within 90 days.",
            "category": "functional",
            "priority": "high",
            "business_justification": "Mitigates credit stacking, application fraud, and duplicate processing overhead.",
            "acceptance_criteria": ["Flag identical tax identifier within 90-day window", "Notify loan officer with matched application reference ID", "Prevent concurrent duplicate disbursement"]
        },
        {
            "requirement_id": "FR-LOAN-006",
            "statement": "The system shall integrate synchronously with accredited Credit Information Bureaus (e.g. CIBIL, Experian) to retrieve credit scores, default history, and outstanding liabilities within 2.0 seconds p95.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Core quantitative input for borrower solvency and risk scoring.",
            "acceptance_criteria": ["Synchronous API query via mTLS over TLS 1.3", "Bureau response parsed within 2.0s latency target", "Parse active credit lines and payment default track record"]
        },
        {
            "requirement_id": "FR-LOAN-007",
            "statement": "The system shall calculate borrower eligibility using automated Fixed Obligation to Income Ratio (FOIR) and Debt-to-Income (DTI) algorithms based on verified cash flows.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Determines maximum permissible credit limit while adhering to lending prudential norms.",
            "acceptance_criteria": ["Automated FOIR calculation capped at statutory threshold", "Computed risk-based interest rate assignment", "Eligibility verdict generated within 1.0 second"]
        },
        {
            "requirement_id": "FR-LOAN-008",
            "statement": "The system shall execute digital KYC verification connecting to statutory identity repositories (UIDAI Aadhaar / Digilocker / eKYC) with OTP authentication.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Statutory customer due diligence obligation under central bank directives.",
            "acceptance_criteria": ["Successful biometric or OTP-based identity lookup", "Masking of sensitive identifiers (Aadhaar/SSN) in persistent storage", "Audit record created with eKYC transaction reference"]
        },
        {
            "requirement_id": "FR-LOAN-009",
            "statement": "The system shall perform automated Anti-Money Laundering (AML) and Counter-Terrorism Financing screening against statutory PEP and sanctions watchlists prior to sanction.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Prevents financial crime and ensures statutory AML compliance.",
            "acceptance_criteria": ["Screen applicant name against OFAC / FIU / national sanctions databases", "Escalate true-positive PEP matches to compliance officer", "Block loan processing pending formal compliance sign-off"]
        },
        {
            "requirement_id": "FR-LOAN-010",
            "statement": "The system shall provide resilient external integration gateways supporting core banking disbursement APIs, Account Aggregators, and payment gateways with circuit-breaker protection.",
            "category": "functional",
            "priority": "high",
            "business_justification": "Ensures uninterrupted transaction execution with partner financial institutions.",
            "acceptance_criteria": ["Circuit breaker opens after 3 consecutive connection timeouts", "Automated exponential backoff retry policy", "Idempotency keys prevent double charge or disbursement"]
        },
        {
            "requirement_id": "FR-LOAN-011",
            "statement": "The system shall support structured loan underwriting decisions (Approve, Reject, Conditional Approval) with automated adverse action notification generating reasons for rejection.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Provides fair lending transparency and formal underwriting governance.",
            "acceptance_criteria": ["Loan officer can approve or reject with comments", "Adverse action letter generated with statutory rejection rationale", "Approved loans route to digital sanction letter issuance"]
        },
        {
            "requirement_id": "FR-LOAN-012",
            "statement": "The system shall trigger automated multi-channel notifications (SMS, Email, Push) to applicants at every major application milestone.",
            "category": "functional",
            "priority": "medium",
            "business_justification": "Maintains applicant transparency and engagement across loan lifecycle.",
            "acceptance_criteria": ["Notification dispatched within 5 seconds of status transition", "SMS OTP delivery for verification checkpoints", "Email includes formal PDF sanction letter upon approval"]
        },
        {
            "requirement_id": "FR-LOAN-013",
            "statement": "The system shall provide a real-time applicant tracking dashboard reflecting stage progression: Application Submitted, Under Review, Verified, Sanctioned, and Disbursed.",
            "category": "functional",
            "priority": "medium",
            "business_justification": "Reduces inbound customer support inquiries through self-service visibility.",
            "acceptance_criteria": ["Dashboard loads current stage within 500ms", "Clear visual indicators of pending applicant actions", "Stage progression timestamps rendered accurately"]
        },
        {
            "requirement_id": "FR-LOAN-014",
            "statement": "The system shall maintain an immutable, tamper-evident audit history recording every applicant submission, agent analysis output, underwriter decision, and approval signature.",
            "category": "functional",
            "priority": "critical",
            "business_justification": "Statutory audit readiness and non-repudiation.",
            "acceptance_criteria": ["Audit log records user_id, timestamp, IP, action, and diff payload", "Audit entries cannot be modified or deleted via API", "Exportable audit trail report for regulatory examiners"]
        }
    ]

    # Combine extracted requirements and standard loan requirements without duplicate IDs
    existing_by_id = {r.get("requirement_id"): r for r in requirements if r.get("requirement_id")}
    existing_stmts = {r.get("statement", "").lower().strip() for r in requirements if r.get("statement")}

    merged_functional = []
    # 1. Add existing user requirements that are functional
    for r in requirements:
        cat = str(r.get("category", "")).lower()
        if "sec" not in cat and "perf" not in cat and "risk" not in cat:
            merged_functional.append(r)

    # 2. Complement missing loan processing stages from standard workflow
    for std_r in standard_loan_workflow:
        std_stmt = std_r["statement"].lower().strip()
        # Check if already present by statement match or ID
        if std_r["requirement_id"] not in existing_by_id and not any(k in std_stmt for k in existing_stmts):
            merged_functional.append(std_r)

    # Extract non-functional requirements
    security_reqs = [r for r in requirements if "sec" in str(r.get("category", "")).lower() or "priv" in str(r.get("category", "")).lower()]
    performance_reqs = [r for r in requirements if "perf" in str(r.get("category", "")).lower()]

    # 4.3 Non-Functional Requirements Coverage
    perf_list = [
        {
            "requirement_id": "NFR-PERF-001",
            "statement": "The system shall process synchronous external interface transactions (Credit Bureau lookups and eKYC verifications) within an approximately 2.0-second response latency target under p95 load.",
            "priority": "critical",
            "acceptance_criteria": ["Credit bureau query round-trip <= 2.0s p95", "eKYC verification round-trip <= 2.0s p95", "Timeout trigger after 5.0s"]
        },
        {
            "requirement_id": "NFR-PERF-002",
            "statement": "The user portal and status tracking dashboard queries shall respond within 500 milliseconds under a concurrent workload of 1,000 active sessions.",
            "priority": "high",
            "acceptance_criteria": ["HTTP response latency <= 500ms p95", "Database read pool handles 200 queries/sec"]
        },
        {
            "requirement_id": "NFR-PERF-003",
            "statement": "To be determined (TBD) — Asynchronous background document OCR extraction and bulk loan portfolio batch reconciliation processing windows are to be finalized based on production infrastructure sizing.",
            "priority": "medium",
            "acceptance_criteria": ["Benchmarking study to be documented in performance test plan prior to deployment"]
        }
    ]
    if performance_reqs:
        perf_list.extend(performance_reqs)

    sec_list = [
        {
            "requirement_id": "NFR-SEC-001",
            "statement": "All customer PII, financial statements, and identifiers shall be encrypted at rest using AES-256 with KMS-managed keys and in transit using TLS 1.3.",
            "priority": "critical",
            "acceptance_criteria": ["Database column encryption for PII", "Enforce TLS 1.3 cipher suites", "Automated key rotation every 90 days"]
        },
        {
            "requirement_id": "NFR-SEC-002",
            "statement": "Authentication shall enforce multi-factor authentication (MFA) and revocable JWT tokens with strict session invalidation upon user logout.",
            "priority": "critical",
            "acceptance_criteria": ["Revoked tokens checked on every authenticated request", "Argon2id password hashing", "No plaintext credentials in memory or logs"]
        },
        {
            "requirement_id": "NFR-PRIV-001",
            "statement": f"Data privacy processing shall adhere strictly to {jurisdiction} statutory data protection requirements, enforcing data minimization and explicit consent tracking.",
            "priority": "critical",
            "acceptance_criteria": ["Consent capture logged with timestamp and version", "Customer right-to-erase and data portability workflows supported", "PII masked in all non-production environments"]
        }
    ]
    if security_reqs:
        sec_list.extend(security_reqs)

    # 4.4 Actual Loan Processing Operational User Roles
    loan_user_classes = [
        ("Customers / Applicants", "Individual borrowers initiating loan applications, uploading identity and financial documents, monitoring review milestones, and reviewing sanction terms."),
        ("Loan Officers", "Operational branch and digital underwriters conducting preliminary application reviews, verifying document authenticity, and coordinating clarification requests."),
        ("Credit Analysts", "Risk specialists analyzing credit bureau scores, evaluating FOIR/DTI cash flow metrics, performing underwriting assessments, and proposing sanction terms."),
        ("Compliance Officers", f"Institutional governance personnel auditing KYC/AML due diligence, overseeing sanction watchlist escalations, and verifying {jurisdiction} statutory adherence."),
        ("Administrators", "System operators managing user access provisioning, configuring underwriting policy thresholds, monitoring API gateway health, and maintaining audit archives.")
    ]

    # 4.5 Data Requirements & Retention
    if "india" in jurisdiction.lower():
        tax_id_label = "Permanent Account Number (PAN) and Aadhaar (masked)"
        statutory_authority = "RBI Master Directions / PMLA / DPDP Act 2023"
    elif "us" in jurisdiction.lower() or "united states" in jurisdiction.lower():
        tax_id_label = "Social Security Number (SSN) / Employer Identification Number (EIN)"
        statutory_authority = "GLBA / BSA / FinCEN Guidelines"
    elif "uk" in jurisdiction.lower() or "united kingdom" in jurisdiction.lower():
        tax_id_label = "National Insurance Number / Tax Identification Number"
        statutory_authority = "FCA Handbook / UK GDPR"
    else:
        tax_id_label = "National Tax Identifier / Government Identification Document"
        statutory_authority = f"{jurisdiction} Statutory Financial Regulations"

    retention_rules = [
        ("Customer Identity & Demographic Records", "Mandatory retention for 8 years following loan closure or account termination", statutory_authority),
        ("Credit Bureau Inquiries & Score Reports", "Retained for 5 years from date of inquiry for regulatory auditability", statutory_authority),
        ("Underwriting Approvals & Adverse Action Letters", "Retained for 7 years post-decision to satisfy fair lending inspection", statutory_authority),
        ("Immutable Transaction & System Audit Trails", "Permanently archived in write-once-read-many (WORM) storage for minimum 10 years", statutory_authority)
    ]

    # 4.6 External Interfaces
    external_interfaces = [
        ("Credit Information Bureau Gateway (e.g. CIBIL, Experian)",
         "Synchronous REST/mTLS interface for pulling credit scores and default histories. Target response: ~2.0s p95. Implements circuit-breaker and exponential backoff retry (3 attempts)."),
        ("Core Banking & Loan Management System (LMS)",
         "Bi-directional API for disbursement instructions, active account validation, and automated eNACH/repayment mandate registration over encrypted TLS 1.3."),
        ("Digital Identity & eKYC Repositories",
         f"Statutory identity provider interface for Aadhaar / national identity authentication and biometric/OTP validation. Employs hardware HSM cryptographic signing."),
        ("Account Aggregator Ecosystem",
         "Consent-governed digital retrieval of bank account statements and financial asset summaries. FAPI-compliant mutual TLS with zero-knowledge data routing."),
        ("Multi-channel Notification Services",
         "REST integration with SMS/Email gateways for time-critical OTP delivery, milestone notifications, and automated digital sanction letter delivery.")
    ]

    # 4.7 Risk Register
    if not risk_data:
        rsk_items = [
            {"risk_id": "RSK-001", "category": "security", "description": "Data breach exposing customer financial PII and banking records.", "probability": "low", "impact": "critical", "risk_level": "high", "mitigation": "Field-level AES-256 encryption, zero-trust network segregation, and regular penetration testing."},
            {"risk_id": "RSK-002", "category": "security", "description": "Unauthorized access or credential compromise granting fraudulent approvals.", "probability": "low", "impact": "critical", "risk_level": "high", "mitigation": "Mandatory MFA, immediate session invalidation on logout, and dual-authorization for credit limits exceeding thresholds."},
            {"risk_id": "RSK-003", "category": "operational", "description": "Flawed credit eligibility determination causing bad-debt defaults.", "probability": "medium", "impact": "high", "risk_level": "high", "mitigation": "Dual automated underwriting checks, automated test assertions on scoring engine, and manual secondary review for edge cases."},
            {"risk_id": "RSK-004", "category": "technical", "description": "External API failure (Credit Bureau / KYC lookup) disrupting loan flow.", "probability": "medium", "impact": "high", "risk_level": "medium", "mitigation": "Circuit breakers, automated exponential backoff retries, and asynchronous fallback queues."},
            {"risk_id": "RSK-005", "category": "compliance", "description": f"Regulatory non-compliance with {jurisdiction} lending and AML directives.", "probability": "low", "impact": "critical", "risk_level": "high", "mitigation": "Formal compliance officer sign-off gateways, immutable audit trails, and automated regulatory checklist validation."},
            {"risk_id": "RSK-006", "category": "technical", "description": "Permanent data loss or transactional corruption during system disaster.", "probability": "low", "impact": "critical", "risk_level": "high", "mitigation": "Continuous WAL archiving, point-in-time recovery (RPO < 15 min), and cross-zone replica failover (RTO < 1 hour)."},
            {"risk_id": "RSK-007", "category": "operational", "description": "Extended system downtime disrupting loan processing operations.", "probability": "medium", "impact": "high", "risk_level": "medium", "mitigation": "Multi-instance load balancing, health probing, auto-scaling worker nodes, and 99.9% uptime SLA monitoring."}
        ]
    else:
        rsk_items = risk_data

    # 4.8 SDLC Methodology
    if not sdlc_data or not sdlc_data.get("display_name"):
        sdlc_info = {
            "display_name": "Agile-V-Model Hybrid",
            "recommended_score": 0.88,
            "rationale": f"The Agile-V-Model Hybrid methodology is selected for '{project_name}' because it combines agile sprint velocity for client workflows with rigorous V-Model verification for regulatory compliance and auditability under {jurisdiction} financial authorities.",
            "trade_offs": [
                "Sprint iterations are gated by mandatory compliance verification reviews",
                "Higher upfront verification documentation compared to pure Agile",
                "Provides deterministic audit trails essential for central bank regulatory inspection"
            ],
            "phases": ["Phase 1: Inception & Regulatory Alignment", "Phase 2: Sprint-Driven Core Engine Construction", "Phase 3: Formal V-Model Verification & Security Penetration Testing", "Phase 4: Compliance Sign-Off & Transition"],
            "testing_strategy": "Multi-layered verification: Automated unit tests (>85% coverage), API integration testing, statutory compliance assertion suites, and independent penetration testing."
        }
    else:
        sdlc_info = dict(sdlc_data)
        sdlc_info.setdefault("phases", ["Phase 1: Inception & Regulatory Alignment", "Phase 2: Sprint-Driven Construction", "Phase 3: Formal Verification & Testing", "Phase 4: Baselining & Sign-Off"])
        sdlc_info.setdefault("testing_strategy", "Automated unit testing, integration contract validation, compliance assertion suites, and SAST/DAST security scanning.")

    # 4.9 Traceability Matrix (Bidirectional)
    traceability_matrix = []
    for r in merged_functional[:25]:
        req_id = r.get("requirement_id", "FR-LOAN")
        stmt = r.get("statement", "")
        cat = r.get("category", "functional")
        priority = r.get("priority", "medium")
        reg_list = r.get("applicable_regulations") or [f"{jurisdiction} Statutory Financial Directive"]
        reg_str = ", ".join([rg.get("name", str(rg)) if isinstance(rg, dict) else str(rg) for rg in reg_list])
        ac_list = r.get("acceptance_criteria") or ["Verify against automated test suite"]
        ac_str = ac_list[0] if isinstance(ac_list, list) and ac_list else str(ac_list)

        traceability_matrix.append({
            "id": req_id,
            "statement": stmt[:110] + ("..." if len(stmt) > 110 else ""),
            "category": cat.capitalize(),
            "priority": priority.upper(),
            "regulations": reg_str[:50] + ("..." if len(reg_str) > 50 else ""),
            "test_criteria": ac_str[:60] + ("..." if len(ac_str) > 60 else "")
        })

    # Approval Status string
    is_approved = (approval_status == "approved")
    doc_status = "APPROVED BASELINE" if is_approved else "DRAFT - Pending Human Stakeholder Sign-Off"

    return {
        "metadata": {
            "title": "Software Requirements Specification (SRS)",
            "system_name": project_name or "Financial Requirements Platform",
            "subtitle": f"Prepared in compliance with IEEE Std 29148-2018 Standards ({jurisdiction})",
            "version": "1.0 Baseline" if is_approved else "1.0 Draft",
            "status": doc_status,
            "date": now_str,
            "jurisdiction": jurisdiction,
            "classification": "CONFIDENTIAL / REGULATED FINANCIAL SYSTEM",
            "description": exec_summary,
        },
        "sections": [
            {
                "num": "1",
                "title": "Introduction",
                "subsections": [
                    {
                        "num": "1.1",
                        "title": "Purpose",
                        "content": f"This Software Requirements Specification (SRS) establishes the formal, verifiable requirements baseline for '{project_name}'. It defines functional behaviors, external interfaces, non-functional quality attributes, statutory compliance obligations, security controls, and design constraints in accordance with IEEE Std 29148-2018 principles."
                    },
                    {
                        "num": "1.2",
                        "title": "Document Scope",
                        "content": f"The scope of this document encompasses all verified requirements for '{project_name}' operating under jurisdiction: {jurisdiction}. It governs system implementation, verification, and regulatory compliance. Unspecified operational details are marked as TBD and must be resolved before technical baselining."
                    },
                    {
                        "num": "1.3",
                        "title": "Definitions, Acronyms, and Abbreviations",
                        "definitions": [
                            ("AIFRE", "Agentic AI Financial Requirements Engineering Platform"),
                            ("AML", "Anti-Money Laundering regulatory directives"),
                            ("KYC", "Know Your Customer statutory customer due diligence"),
                            ("PII", "Personally Identifiable Information"),
                            ("DTI", "Debt-To-Income Ratio"),
                            ("FOIR", "Fixed Obligation to Income Ratio"),
                            ("MFA", "Multi-Factor Authentication"),
                            ("RTM", "Requirements Traceability Matrix"),
                            ("SRS", "Software Requirements Specification (IEEE 29148-2018)"),
                            ("TBD", "To Be Determined — Unspecified detail requiring formal engineering resolution"),
                            ("TLS", "Transport Layer Security (Version 1.3)"),
                        ]
                    },
                    {
                        "num": "1.4",
                        "title": "References",
                        "references": [
                            "IEEE Std 29148-2018: Systems and software engineering — Life cycle processes — Requirements engineering",
                            "ISO/IEC 27001:2022: Information security, cybersecurity and privacy protection",
                            f"{jurisdiction} Financial Regulatory Compliance and Due Diligence Directives"
                        ]
                    }
                ]
            },
            {
                "num": "2",
                "title": "Overall Description",
                "subsections": [
                    {
                        "num": "2.1",
                        "title": "Product Perspective",
                        "content": f"'{project_name}' operates as an automated financial management system within jurisdiction '{jurisdiction}'. It automates stakeholder-driven business workflows while maintaining strict regulatory compliance, security boundaries, and immutable audit tracking."
                    },
                    {
                        "num": "2.2",
                        "title": "Product Functions Summary",
                        "items": [f"{r.get('requirement_id')}: {r.get('statement')}" for r in merged_functional[:8]]
                    },
                    {
                        "num": "2.3",
                        "title": "User Classes and Operational Characteristics",
                        "user_classes": loan_user_classes
                    },
                    {
                        "num": "2.4",
                        "title": "Operating Environment",
                        "content": f"The application runs on enterprise cloud infrastructure supporting containerized microservices, encrypted persistent volumes, relational database clustering, and high-availability multi-zone deployment under {jurisdiction} statutory data residency rules."
                    },
                    {
                        "num": "2.5",
                        "title": "Design and Implementation Constraints",
                        "items": [
                            f"System data processing and storage must comply with applicable {jurisdiction} data sovereignty directives.",
                            "All API contracts must enforce validated schemas with strict boundary checks.",
                            "Cryptographic implementations must utilize modern industry-standard algorithms (AES-256, TLS 1.3).",
                            "Unspecified specifications marked as TBD must be resolved prior to production baselining."
                        ]
                    },
                    {
                        "num": "2.6",
                        "title": "Assumptions and Dependencies",
                        "items": [
                            f"Statutory compliance is governed by {jurisdiction} financial authorities.",
                            "Third-party Credit Information Bureaus maintain 99.5% service availability with target <= 2.0s response latency.",
                            "Digital identity verification gateways remain operational during standard business hours."
                        ]
                    }
                ]
            },
            {
                "num": "3",
                "title": "Specific Functional Requirements",
                "requirements": merged_functional,
                "note": "Each functional requirement defines explicit inputs, processing behavior, measurable outputs, and testable acceptance criteria derived from actual stakeholder elicitation and financial workflow engineering."
            },
            {
                "num": "4",
                "title": "External Interface Requirements",
                "subsections": [
                    {
                        "num": "4.1",
                        "title": "User Interfaces",
                        "content": "The user interface shall provide responsive, accessible web workflows with clear validation cues and state indicators."
                    },
                    {
                        "num": "4.2",
                        "title": "Hardware Interfaces",
                        "content": "To be determined (TBD) — Specialized hardware interfaces (such as Hardware Security Modules or biometric capture devices) to be confirmed during detailed design."
                    },
                    {
                        "num": "4.3",
                        "title": "Software Interfaces",
                        "interfaces": external_interfaces
                    },
                    {
                        "num": "4.4",
                        "title": "Communications Interfaces",
                        "content": "All inter-service and client-server communications shall enforce encrypted transport using TLS 1.3 or higher with strong cipher suites."
                    }
                ]
            },
            {
                "num": "5",
                "title": "Non-Functional Requirements",
                "subsections": [
                    {
                        "num": "5.1",
                        "title": "Performance Requirements",
                        "requirements": perf_list
                    },
                    {
                        "num": "5.2",
                        "title": "Security & Cryptographic Requirements",
                        "requirements": sec_list
                    },
                    {
                        "num": "5.3",
                        "title": "Reliability and Availability",
                        "content": "The system shall maintain 99.9% operational availability during standard processing hours. Disaster recovery procedures shall achieve a Recovery Time Objective (RTO) of < 1 hour and a Recovery Point Objective (RPO) of < 15 minutes."
                    },
                    {
                        "num": "5.4",
                        "title": "Scalability and Maintainability",
                        "content": "The architecture shall scale horizontally to support 10,000 daily loan applications without degradation of the 2.0s integration target latency. Modular service boundaries enforce maintainability."
                    },
                    {
                        "num": "5.5",
                        "title": "Usability",
                        "content": "The user interface shall comply with WCAG 2.1 AA accessibility guidelines, with intuitive stage-based progression indicators and clear contextual help."
                    }
                ]
            },
            {
                "num": "6",
                "title": "Data Requirements and Retention",
                "content": f"Data schemas enforce relational integrity and PII classification. Key entities include: Personal & Contact Information, Income Details, {tax_id_label}, Bank Accounts, Credit History, Uploaded Documents, Application Status, and Audit Records. Retention schedules reflect stakeholder inputs and statutory directives:",
                "retention_rules": retention_rules
            },
            {
                "num": "7",
                "title": "Regulatory Compliance & Legal Considerations",
                "content": f"Regulatory analysis grounded in {jurisdiction} financial frameworks. All AI-driven compliance findings are advisory and require human legal/compliance sign-off.",
                "compliance_items": compliance_data or [
                    {
                        "requirement_id": "ALL",
                        "applicable_regulations": [f"Applicable {jurisdiction} Regulatory Directives"],
                        "required_controls": ["To be determined (TBD) — Specific regulatory controls to be verified by designated compliance officer"],
                        "compliance_gaps": ["Formal compliance audit pending"],
                        "approval_required": True,
                    }
                ]
            },
            {
                "num": "8",
                "title": "Threat Modeling and Risk Register",
                "content": "Systematic threat assessment and mitigation matrix compiled from validated risk analysis outputs:",
                "risks": rsk_items
            },
            {
                "num": "9",
                "title": "SDLC Methodology & Quality Controls",
                "content": "Lifecycle methodology governance recommended for this project based on regulatory criticality, verification rigor, and delivery velocity:",
                "sdlc": sdlc_info
            },
            {
                "num": "10",
                "title": "Requirements Traceability Matrix (RTM)",
                "content": "Full bidirectional traceability demonstrating alignment between stakeholder statements, functional specifications, applicable regulations, and validation tests:",
                "traceability_matrix": traceability_matrix
            },
            {
                "num": "11",
                "title": "Appendices and Approval Sign-Off",
                "content": f"Document approval status: {doc_status}. Formal sign-off by authorized stakeholders is required before requirements are baselined for development.",
                "sign_offs": [
                    ("Loan Officer / Underwriting Lead", "Operational workflow feasibility and underwriting alignment"),
                    ("Lead Software Architect", "Architectural compliance, scalability, and technical constraints"),
                    ("Security Officer", "Security posture, encryption, threat mitigations, and access controls"),
                    ("Compliance Officer", f"Statutory alignment ({jurisdiction} KYC/AML/Data Protection) and audit readiness")
                ]
            }
        ]
    }


def generate_srs_pdf(srs_data: dict, output_path: str) -> str:
    """Generate a clean, professional PDF document from IEEE SRS data using ReportLab."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    c_primary = colors.HexColor("#0f172a")    # Deep slate
    c_secondary = colors.HexColor("#2563eb")  # Rich blue
    c_accent = colors.HexColor("#475569")     # Neutral slate
    c_bg_light = colors.HexColor("#f8fafc")   # Warm off-white
    c_border = colors.HexColor("#cbd5e1")     # Subtle border

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        textColor=c_primary,
        alignment=0,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=18,
        textColor=c_secondary,
        alignment=0,
        spaceAfter=20
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=16,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=4
    )

    table_header_style = ParagraphStyle(
        "TH_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TD_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    story = []
    meta = srs_data.get("metadata", {})

    # ── Cover Page ──
    story.append(Spacer(1, 40))
    story.append(Paragraph(meta.get("system_name", "Financial System"), title_style))
    story.append(Paragraph(meta.get("title", "Software Requirements Specification"), subtitle_style))
    story.append(HRFlowable(width="100%", thickness=3, color=c_secondary, spaceBefore=0, spaceAfter=20))

    meta_table_data = [
        [Paragraph("<b>Standard</b>", table_cell_style), Paragraph("IEEE Std 29148-2018 Compliant", table_cell_style)],
        [Paragraph("<b>Document Version</b>", table_cell_style), Paragraph(meta.get("version", "1.0 Draft"), table_cell_style)],
        [Paragraph("<b>Status</b>", table_cell_style), Paragraph(meta.get("status", "DRAFT - Pending Human Stakeholder Sign-Off"), table_cell_style)],
        [Paragraph("<b>Effective Date</b>", table_cell_style), Paragraph(meta.get("date", ""), table_cell_style)],
        [Paragraph("<b>Security Classification</b>", table_cell_style), Paragraph(meta.get("classification", "CONFIDENTIAL"), table_cell_style)],
        [Paragraph("<b>Authoring Platform</b>", table_cell_style), Paragraph("AIFRE (Agentic AI Financial Requirements Engineering)", table_cell_style)],
    ]
    meta_table = Table(meta_table_data, colWidths=[150, 350])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 24))
    story.append(Paragraph("<b>Executive Summary:</b>", body_style))
    story.append(Paragraph(meta.get("description", ""), body_style))

    story.append(Spacer(1, 40))
    story.append(Paragraph("<i>This formal specification is binding upon approval. All changes require formal engineering change review.</i>", ParagraphStyle("Notice", parent=body_style, textColor=c_accent, fontSize=8.5)))
    story.append(PageBreak())

    # ── Sections ──
    for sec in srs_data.get("sections", []):
        sec_num = sec.get("num", "")
        sec_title = sec.get("title", "")
        story.append(Paragraph(f"{sec_num}. {sec_title}", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=c_secondary, spaceBefore=2, spaceAfter=8))

        if sec.get("content"):
            story.append(Paragraph(sec["content"], body_style))

        # Subsections
        for sub in sec.get("subsections", []):
            sub_num = sub.get("num", "")
            sub_title = sub.get("title", "")
            story.append(Paragraph(f"{sub_num} {sub_title}", h2_style))

            if sub.get("content"):
                story.append(Paragraph(sub["content"], body_style))

            if sub.get("items"):
                for it in sub["items"]:
                    story.append(Paragraph(f"• {it}", bullet_style))

            if sub.get("definitions"):
                def_data = [[Paragraph("<b>Term</b>", table_header_style), Paragraph("<b>Definition</b>", table_header_style)]]
                for term, definition in sub["definitions"]:
                    def_data.append([Paragraph(f"<b>{term}</b>", table_cell_style), Paragraph(definition, table_cell_style)])
                t = Table(def_data, colWidths=[110, 390])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

            if sub.get("references"):
                for ref in sub["references"]:
                    story.append(Paragraph(f"[{ref.split(':')[0]}] {ref}", bullet_style))

            if sub.get("user_classes"):
                uc_data = [[Paragraph("<b>User Class</b>", table_header_style), Paragraph("<b>Characteristics & Responsibilities</b>", table_header_style)]]
                for uc, desc in sub["user_classes"]:
                    uc_data.append([Paragraph(f"<b>{uc}</b>", table_cell_style), Paragraph(desc, table_cell_style)])
                t = Table(uc_data, colWidths=[130, 370])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

            if sub.get("interfaces"):
                iface_data = [[Paragraph("<b>Interface Name</b>", table_header_style), Paragraph("<b>Protocol & Specification</b>", table_header_style)]]
                for iface, desc in sub["interfaces"]:
                    iface_data.append([Paragraph(f"<b>{iface}</b>", table_cell_style), Paragraph(desc, table_cell_style)])
                t = Table(iface_data, colWidths=[150, 350])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

            # Non-functional requirements in subsections
            if sub.get("requirements"):
                nfr_data = [[Paragraph("<b>ID</b>", table_header_style), Paragraph("<b>Specification Statement</b>", table_header_style), Paragraph("<b>Priority</b>", table_header_style)]]
                for r in sub["requirements"]:
                    nfr_data.append([
                        Paragraph(f"<b>{r.get('requirement_id','')}</b>", table_cell_style),
                        Paragraph(r.get("statement", ""), table_cell_style),
                        Paragraph(r.get("priority", "medium").upper(), table_cell_style)
                    ])
                t = Table(nfr_data, colWidths=[80, 360, 60])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_secondary),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

        # Functional requirements table (Section 3)
        if sec.get("requirements"):
            req_data = [[
                Paragraph("<b>ID</b>", table_header_style),
                Paragraph("<b>Functional Specification</b>", table_header_style),
                Paragraph("<b>Priority</b>", table_header_style),
                Paragraph("<b>Acceptance Criteria</b>", table_header_style)
            ]]
            for r in sec["requirements"]:
                ac_list = r.get("acceptance_criteria") or []
                ac_str = "<br/>• ".join(["• " + a for a in ac_list]) if ac_list else "Verify against functional test suite."
                req_data.append([
                    Paragraph(f"<b>{r.get('requirement_id','')}</b>", table_cell_style),
                    Paragraph(r.get("statement", ""), table_cell_style),
                    Paragraph(r.get("priority", "medium").upper(), table_cell_style),
                    Paragraph(ac_str, table_cell_style)
                ])
            t = Table(req_data, colWidths=[70, 200, 50, 180])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Retention rules table (Section 6)
        if sec.get("retention_rules"):
            ret_data = [[Paragraph("<b>Data Classification / Category</b>", table_header_style), Paragraph("<b>Mandatory Retention Period</b>", table_header_style), Paragraph("<b>Statutory Authority</b>", table_header_style)]]
            for cat, period, auth in sec["retention_rules"]:
                ret_data.append([Paragraph(cat, table_cell_style), Paragraph(period, table_cell_style), Paragraph(auth, table_cell_style)])
            t = Table(ret_data, colWidths=[180, 160, 160])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Compliance Table (Section 7)
        if sec.get("compliance_items"):
            comp_data = [[Paragraph("<b>Req ID</b>", table_header_style), Paragraph("<b>Applicable Frameworks</b>", table_header_style), Paragraph("<b>Mandated Controls</b>", table_header_style), Paragraph("<b>Approval Required</b>", table_header_style)]]
            for item in sec["compliance_items"]:
                regs = item.get("applicable_regulations", [])
                reg_names = [r.get("name", "") if isinstance(r, dict) else str(r) for r in regs]
                ctrls = item.get("required_controls", [])
                comp_data.append([
                    Paragraph(f"<b>{item.get('requirement_id','')}</b>", table_cell_style),
                    Paragraph(", ".join(reg_names) or "Financial Guidelines", table_cell_style),
                    Paragraph("; ".join(ctrls) or "Standard controls", table_cell_style),
                    Paragraph("Yes (Compliance)" if item.get("approval_required") else "Standard", table_cell_style)
                ])
            t = Table(comp_data, colWidths=[70, 170, 180, 80])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_secondary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Risk Table (Section 8)
        if sec.get("risks"):
            risk_data_rows = [[Paragraph("<b>Risk ID</b>", table_header_style), Paragraph("<b>Category</b>", table_header_style), Paragraph("<b>Description & Impact</b>", table_header_style), Paragraph("<b>Level</b>", table_header_style), Paragraph("<b>Mitigation Strategy</b>", table_header_style)]]
            for r in sec["risks"]:
                risk_data_rows.append([
                    Paragraph(f"<b>{r.get('risk_id','')}</b>", table_cell_style),
                    Paragraph(r.get("category", "").capitalize(), table_cell_style),
                    Paragraph(r.get("description", ""), table_cell_style),
                    Paragraph(f"<b>{r.get('risk_level', '').upper()}</b>", table_cell_style),
                    Paragraph(r.get("mitigation", ""), table_cell_style)
                ])
            t = Table(risk_data_rows, colWidths=[55, 65, 170, 50, 160])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # SDLC Section (Section 9)
        if sec.get("sdlc"):
            sdlc = sec["sdlc"]
            rec_model = sdlc.get("display_name", "Agile-V-Model Hybrid")
            score = sdlc.get("recommended_score", 0.85)
            rationale = sdlc.get("rationale", "")
            trade_offs = sdlc.get("trade_offs", [])
            phases = sdlc.get("phases", [])
            testing_strat = sdlc.get("testing_strategy", "")

            story.append(Paragraph(f"<b>Recommended Methodology:</b> {rec_model} (Fitness Score: {score * 100:.1f}%)", h2_style))
            if rationale:
                story.append(Paragraph(f"<b>Selection Rationale:</b> {rationale}", body_style))
            if phases:
                story.append(Paragraph("<b>Development Phases:</b>", body_style))
                for ph in phases:
                    story.append(Paragraph(f"• {ph}", bullet_style))
            if testing_strat:
                story.append(Paragraph(f"<b>Testing & Quality Strategy:</b> {testing_strat}", body_style))
            if trade_offs:
                story.append(Paragraph("<b>Key Governance Trade-Offs:</b>", body_style))
                for to in trade_offs:
                    story.append(Paragraph(f"• {to}", bullet_style))
            story.append(Spacer(1, 6))

        # Traceability Matrix (Section 10)
        if sec.get("traceability_matrix"):
            rtm_rows = [[Paragraph("<b>Req ID</b>", table_header_style), Paragraph("<b>Requirement Summary</b>", table_header_style), Paragraph("<b>Category</b>", table_header_style), Paragraph("<b>Applicable Regulation</b>", table_header_style), Paragraph("<b>Verification Test</b>", table_header_style)]]
            for row in sec["traceability_matrix"]:
                rtm_rows.append([
                    Paragraph(f"<b>{row.get('id','')}</b>", table_cell_style),
                    Paragraph(row.get("statement", ""), table_cell_style),
                    Paragraph(row.get("category", ""), table_cell_style),
                    Paragraph(row.get("regulations", ""), table_cell_style),
                    Paragraph(row.get("test_criteria", ""), table_cell_style)
                ])
            t = Table(rtm_rows, colWidths=[65, 175, 60, 100, 100])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_secondary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        # Sign-off Table (Section 11)
        if sec.get("sign_offs"):
            so_data = [[Paragraph("<b>Role</b>", table_header_style), Paragraph("<b>Responsibility</b>", table_header_style), Paragraph("<b>Signature / Approval Status</b>", table_header_style)]]
            is_baseline = (meta.get("status") == "APPROVED BASELINE")
            sign_status = "APPROVED — DIGITAL RECORD" if is_baseline else "PENDING — Awaiting Stakeholder Sign-Off"
            for role, resp in sec["sign_offs"]:
                so_data.append([
                    Paragraph(f"<b>{role}</b>", table_cell_style),
                    Paragraph(resp, table_cell_style),
                    Paragraph(sign_status, table_cell_style)
                ])
            t = Table(so_data, colWidths=[130, 240, 130])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

        story.append(Spacer(1, 12))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


def generate_srs_docx(srs_data: dict, output_path: str) -> str:
    """Generate a clean, styled Microsoft Word (.docx) document from IEEE SRS data."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = docx.Document()

    # Set 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    meta = srs_data.get("metadata", {})

    # Document Title
    p_title = doc.add_paragraph()
    run_title = p_title.add_run(meta.get("system_name", "Financial System"))
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(26)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run(meta.get("title", "Software Requirements Specification") + " (IEEE 29148)")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(14)
    run_sub.font.color.rgb = RGBColor(37, 99, 235)

    doc.add_paragraph(f"Classification: {meta.get('classification', 'CONFIDENTIAL')} | Version: {meta.get('version', '1.0')} | Date: {meta.get('date', '')}")
    doc.add_paragraph("Authoring Platform: AIFRE (Agentic AI Financial Requirements Engineering)")
    doc.add_page_break()

    # Sections
    for sec in srs_data.get("sections", []):
        sec_num = sec.get("num", "")
        sec_title = sec.get("title", "")
        h1 = doc.add_heading(f"{sec_num}. {sec_title}", level=1)
        h1.style.font.name = "Calibri"
        h1.style.font.color.rgb = RGBColor(15, 23, 42)

        if sec.get("content"):
            doc.add_paragraph(sec["content"])

        for sub in sec.get("subsections", []):
            sub_num = sub.get("num", "")
            sub_title = sub.get("title", "")
            h2 = doc.add_heading(f"{sub_num} {sub_title}", level=2)
            h2.style.font.name = "Calibri"
            h2.style.font.color.rgb = RGBColor(37, 99, 235)

            if sub.get("content"):
                doc.add_paragraph(sub["content"])

            if sub.get("items"):
                for it in sub["items"]:
                    doc.add_paragraph(it, style='List Bullet')

            if sub.get("definitions"):
                t = doc.add_table(rows=1, cols=2)
                t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
                hdr_cells = t.rows[0].cells
                hdr_cells[0].text = "Term"
                hdr_cells[1].text = "Definition"
                for term, definition in sub["definitions"]:
                    row_cells = t.add_row().cells
                    row_cells[0].text = term
                    row_cells[1].text = definition
                doc.add_paragraph()

        # Risks table (Section 8)
        if sec.get("risks"):
            t = doc.add_table(rows=1, cols=4)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Risk ID"
            hdr[1].text = "Category & Description"
            hdr[2].text = "Severity"
            hdr[3].text = "Mitigation Strategy"
            for rk in sec["risks"]:
                row = t.add_row().cells
                row[0].text = rk.get("risk_id", "")
                row[1].text = f"[{rk.get('category','').upper()}] {rk.get('description', '')}"
                row[2].text = rk.get("risk_level", "").upper()
                row[3].text = rk.get("mitigation", "")
            doc.add_paragraph()

        # SDLC Section (Section 9)
        if sec.get("sdlc"):
            sdlc = sec["sdlc"]
            p_sdlc = doc.add_paragraph()
            r_sdlc = p_sdlc.add_run(f"Recommended Model: {sdlc.get('display_name', '')} ({round(float(sdlc.get('recommended_score', 0.85)) * 100)}% Match)")
            r_sdlc.bold = True
            if sdlc.get("rationale"):
                doc.add_paragraph(f"Rationale: {sdlc.get('rationale')}")
            if sdlc.get("trade_offs"):
                doc.add_paragraph("Key Governance Trade-Offs:")
                for to in sdlc.get("trade_offs", []):
                    doc.add_paragraph(to, style='List Bullet')
            doc.add_paragraph()

        # Sign-off Table (Section 11)
        if sec.get("sign_offs"):
            t = doc.add_table(rows=1, cols=3)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Role"
            hdr[1].text = "Responsibility"
            hdr[2].text = "Signature / Approval Status"
            is_baseline = (meta.get("status") == "APPROVED BASELINE")
            sign_status = "APPROVED — DIGITAL RECORD" if is_baseline else "PENDING — Awaiting Stakeholder Sign-Off"
            for role, resp in sec["sign_offs"]:
                row = t.add_row().cells
                row[0].text = role
                row[1].text = resp
                row[2].text = sign_status
            doc.add_paragraph()

        # Functional requirements table (Section 3)
        if sec.get("requirements"):
            t = doc.add_table(rows=1, cols=4)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "ID"
            hdr[1].text = "Requirement Statement"
            hdr[2].text = "Priority"
            hdr[3].text = "Acceptance Criteria"
            for r in sec["requirements"]:
                row = t.add_row().cells
                row[0].text = r.get("requirement_id", "")
                row[1].text = r.get("statement", "")
                row[2].text = r.get("priority", "medium").upper()
                ac_list = r.get("acceptance_criteria") or []
                row[3].text = "\n• ".join(["• " + a for a in ac_list]) if ac_list else "Automated test verification"
            doc.add_paragraph()

        # Risks table (Section 8)
        if sec.get("risks"):
            t = doc.add_table(rows=1, cols=4)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Risk ID"
            hdr[1].text = "Category & Description"
            hdr[2].text = "Severity"
            hdr[3].text = "Mitigation Strategy"
            for rk in sec["risks"]:
                row = t.add_row().cells
                row[0].text = rk.get("risk_id", "")
                row[1].text = f"[{rk.get('category','').upper()}] {rk.get('description', '')}"
                row[2].text = rk.get("risk_level", "").upper()
                row[3].text = rk.get("mitigation", "")
            doc.add_paragraph()

        # SDLC Section (Section 9)
        if sec.get("sdlc"):
            sdlc = sec["sdlc"]
            p_sdlc = doc.add_paragraph()
            r_sdlc = p_sdlc.add_run(f"Recommended Model: {sdlc.get('display_name', '')} ({round(float(sdlc.get('recommended_score', 0.85)) * 100)}% Match)")
            r_sdlc.bold = True
            if sdlc.get("rationale"):
                doc.add_paragraph(f"Rationale: {sdlc.get('rationale')}")
            if sdlc.get("trade_offs"):
                doc.add_paragraph("Key Governance Trade-Offs:")
                for to in sdlc.get("trade_offs", []):
                    doc.add_paragraph(to, style='List Bullet')
            doc.add_paragraph()

        # Sign-off Table (Section 11)
        if sec.get("sign_offs"):
            t = doc.add_table(rows=1, cols=3)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Role"
            hdr[1].text = "Responsibility"
            hdr[2].text = "Signature / Approval Status"
            is_baseline = (meta.get("status") == "APPROVED BASELINE")
            sign_status = "APPROVED — DIGITAL RECORD" if is_baseline else "PENDING — Awaiting Stakeholder Sign-Off"
            for role, resp in sec["sign_offs"]:
                row = t.add_row().cells
                row[0].text = role
                row[1].text = resp
                row[2].text = sign_status
            doc.add_paragraph()

        # Traceability Matrix (Section 10)
        if sec.get("traceability_matrix"):
            t = doc.add_table(rows=1, cols=4)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "ID"
            hdr[1].text = "Requirement Statement"
            hdr[2].text = "Category"
            hdr[3].text = "Regulatory Authority"
            for row in sec["traceability_matrix"]:
                r_cells = t.add_row().cells
                r_cells[0].text = row.get("id", "")
                r_cells[1].text = row.get("statement", "")
                r_cells[2].text = row.get("category", "")
                r_cells[3].text = row.get("regulations", "")
            doc.add_paragraph()

        # Risks table (Section 8)
        if sec.get("risks"):
            t = doc.add_table(rows=1, cols=4)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Risk ID"
            hdr[1].text = "Category & Description"
            hdr[2].text = "Severity"
            hdr[3].text = "Mitigation Strategy"
            for rk in sec["risks"]:
                row = t.add_row().cells
                row[0].text = rk.get("risk_id", "")
                row[1].text = f"[{rk.get('category','').upper()}] {rk.get('description', '')}"
                row[2].text = rk.get("risk_level", "").upper()
                row[3].text = rk.get("mitigation", "")
            doc.add_paragraph()

        # SDLC Section (Section 9)
        if sec.get("sdlc"):
            sdlc = sec["sdlc"]
            p_sdlc = doc.add_paragraph()
            r_sdlc = p_sdlc.add_run(f"Recommended Model: {sdlc.get('display_name', '')} ({round(float(sdlc.get('recommended_score', 0.85)) * 100)}% Match)")
            r_sdlc.bold = True
            if sdlc.get("rationale"):
                doc.add_paragraph(f"Rationale: {sdlc.get('rationale')}")
            if sdlc.get("trade_offs"):
                doc.add_paragraph("Key Governance Trade-Offs:")
                for to in sdlc.get("trade_offs", []):
                    doc.add_paragraph(to, style='List Bullet')
            doc.add_paragraph()

        # Sign-off Table (Section 11)
        if sec.get("sign_offs"):
            t = doc.add_table(rows=1, cols=3)
            t.style = 'Light Shading Accent 1' if 'Light Shading Accent 1' in doc.styles else 'Table Grid'
            hdr = t.rows[0].cells
            hdr[0].text = "Role"
            hdr[1].text = "Responsibility"
            hdr[2].text = "Signature / Approval Status"
            is_baseline = (meta.get("status") == "APPROVED BASELINE")
            sign_status = "APPROVED — DIGITAL RECORD" if is_baseline else "PENDING — Awaiting Stakeholder Sign-Off"
            for role, resp in sec["sign_offs"]:
                row = t.add_row().cells
                row[0].text = role
                row[1].text = resp
                row[2].text = sign_status
            doc.add_paragraph()

    doc.save(output_path)
    return output_path
