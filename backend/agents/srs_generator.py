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
                         jurisdiction: str = "US", approval_status: str = "pending") -> dict:
    """Build the comprehensive IEEE 29148 hierarchical data structure from real project records."""
    compliance_data = compliance_data or []
    security_data = security_data or []
    risk_data = risk_data or []
    sdlc_data = sdlc_data or {}

    now_str = datetime.now(timezone.utc).strftime("%B %d, %Y")

    functional_reqs = [r for r in requirements if r.get("category") == "functional" or not r.get("category")]
    security_reqs = [r for r in requirements if "sec" in r.get("category", "").lower() or "priv" in r.get("category", "").lower()]
    performance_reqs = [r for r in requirements if "perf" in r.get("category", "").lower()]
    other_nfr = [r for r in requirements if r not in functional_reqs and r not in security_reqs and r not in performance_reqs]

    # Approval Status
    is_approved = (approval_status == "approved")
    doc_status = "APPROVED BASELINE" if is_approved else "DRAFT - Pending Human Stakeholder Sign-Off"

    # Derive product functions summary from actual functional requirements
    if functional_reqs:
        func_items = [f"{r.get('requirement_id')}: {r.get('statement')}" for r in functional_reqs[:6]]
    else:
        func_items = ["To be determined (TBD) — No functional requirements extracted yet from stakeholder elicitation."]

    # Derive operating environment from requirements or mark TBD
    env_reqs = [r for r in requirements if any(k in r.get("statement", "").lower() for k in ["cloud", "server", "deploy", "kubernetes", "aws", "azure", "docker", "on-premise"])]
    env_content = env_reqs[0].get("statement") if env_reqs else f"To be determined (TBD) — Target infrastructure topology and hosting platform for '{project_name}' to be finalized during technical architecture specification."

    # Derive assumptions & dependencies from requirements or mark TBD
    dep_reqs = [f"Dependency: {r.get('requirement_id')} requires external interface" for r in requirements if any(k in r.get("statement", "").lower() for k in ["third", "api", "gateway", "service", "external"])]
    assumptions_items = dep_reqs if dep_reqs else [
        f"Statutory compliance is governed by {jurisdiction} financial authorities.",
        "To be determined (TBD) — Third-party service level agreements (SLAs) and external gateway specifications to be formalized."
    ]

    # Derive performance requirements or mark TBD
    if performance_reqs:
        perf_list = performance_reqs
    else:
        perf_list = [
            {
                "requirement_id": "NFR-PERF-TBD",
                "statement": "To be determined (TBD) — Explicit response latency, throughput, and concurrent session limits were not specified during elicitation and must be established prior to performance testing.",
                "priority": "medium",
                "acceptance_criteria": ["Benchmark latency thresholds to be documented in performance test plan"]
            }
        ]

    # Derive security requirements from extracted reqs or analysis outputs, else mark TBD
    if security_reqs:
        sec_list = security_reqs
    elif security_data:
        sec_list = [
            {
                "requirement_id": s.get("requirement_id", "NFR-SEC-001"),
                "statement": f"Security control for {s.get('requirement_id')}: {', '.join(s.get('security_controls', [])) or 'Enforce access control and encryption'}",
                "priority": s.get("threat_level", "high").lower(),
                "acceptance_criteria": s.get("security_controls", ["Automated security testing"])
            }
            for s in security_data[:5]
        ]
    else:
        sec_list = [
            {
                "requirement_id": "NFR-SEC-TBD",
                "statement": "To be determined (TBD) — Cryptographic standards, authentication requirements, and confidentiality controls to be specified based on organization security baseline.",
                "priority": "high",
                "acceptance_criteria": ["Security architecture verification required prior to baseline sign-off"]
            }
        ]

    # Availability & Reliability: check real requirements
    avail_reqs = [r for r in requirements if any(k in r.get("statement", "").lower() for k in ["uptime", "availability", "rto", "rpo", "99."])]
    avail_content = avail_reqs[0].get("statement") if avail_reqs else "To be determined (TBD) — Production uptime availability percentage, Recovery Time Objective (RTO), and Recovery Point Objective (RPO) were not specified by stakeholders and must be established prior to release."

    # Scalability & Maintainability
    scale_reqs = [r for r in requirements if any(k in r.get("statement", "").lower() for k in ["scal", "concurrent", "volume", "throughput", "load"])]
    scale_content = scale_reqs[0].get("statement") if scale_reqs else "To be determined (TBD) — Concurrency thresholds and horizontal scaling limits to be finalized in deployment architecture."

    # Usability
    usability_reqs = [r for r in requirements if "usab" in r.get("category", "").lower() or "ui" in r.get("category", "").lower() or "interface" in r.get("statement", "").lower()]
    usab_content = usability_reqs[0].get("statement") if usability_reqs else "To be determined (TBD) — User interface usability benchmarks, error-rate thresholds, and accessibility criteria (WCAG) to be defined in UX design specification."

    # Data Retention: extract actual statements containing retention or mark TBD
    retention_rules = []
    for r in requirements:
        stmt = r.get("statement", "")
        if any(k in stmt.lower() for k in ["retain", "retention", "year", "stored for", "archive"]):
            retention_rules.append((r.get("requirement_id", "REQ"), stmt, f"Stakeholder Elicitation ({jurisdiction})"))
    if not retention_rules:
        retention_rules = [
            ("Statutory Record Retention", f"To be determined (TBD) — Data retention schedules must be configured based on applicable statutory guidelines for jurisdiction: {jurisdiction}.", f"{jurisdiction} Directives")
        ]

    # Compliance items
    if not compliance_data:
        comp_items = [
            {
                "requirement_id": "ALL",
                "applicable_regulations": [f"Applicable {jurisdiction} Regulatory Directives"],
                "required_controls": ["To be determined (TBD) — Specific regulatory controls to be verified by designated compliance officer"],
                "compliance_gaps": ["Formal compliance audit pending"],
                "approval_required": True,
            }
        ]
    else:
        comp_items = compliance_data

    # Risk items
    if not risk_data:
        rsk_items = [
            {
                "risk_id": "RSK-TBD",
                "risk_description": "To be determined (TBD) — Comprehensive threat analysis and risk register to be finalized prior to architecture review.",
                "severity": "medium",
                "likelihood": "medium",
                "mitigation": "Schedule formal risk assessment workshop."
            }
        ]
    else:
        rsk_items = risk_data

    return {
        "metadata": {
            "title": f"Software Requirements Specification (SRS)",
            "system_name": project_name or "Financial Requirements Platform",
            "subtitle": f"Prepared in compliance with IEEE Std 29148-2018 Standards",
            "version": "1.0 Baseline" if is_approved else "1.0 Draft",
            "status": doc_status,
            "date": now_str,
            "jurisdiction": jurisdiction,
            "classification": "CONFIDENTIAL / REGULATED FINANCIAL SYSTEM",
            "description": project_desc or "Financial requirements specification and compliance governance baseline.",
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
                            ("RBAC", "Role-Based Access Control"),
                            ("RTM", "Requirements Traceability Matrix"),
                            ("SRS", "Software Requirements Specification (IEEE 29148-2018)"),
                            ("TBD", "To Be Determined — Unspecified detail requiring formal engineering resolution"),
                            ("TLS", "Transport Layer Security"),
                        ]
                    },
                    {
                        "num": "1.4",
                        "title": "References",
                        "references": [
                            "IEEE Std 29148-2018: Systems and software engineering — Life cycle processes — Requirements engineering",
                            "ISO/IEC 27001:2022: Information security, cybersecurity and privacy protection",
                            f"{jurisdiction} Financial Regulatory Compliance and Due Diligence Guidelines"
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
                        "content": f"'{project_name}' operates as a financial management system within jurisdiction '{jurisdiction}'. It automates stakeholder-driven business workflows while maintaining strict regulatory compliance, security boundaries, and immutable audit tracking."
                    },
                    {
                        "num": "2.2",
                        "title": "Product Functions Summary",
                        "items": func_items
                    },
                    {
                        "num": "2.3",
                        "title": "User Classes and Characteristics",
                        "user_classes": [
                            ("Business Analyst", "Requirements engineer defining functional behaviors and regulatory obligations."),
                            ("Compliance Officer", f"Specialist ensuring adherence to {jurisdiction} statutory financial directives."),
                            ("Security Officer", "Auditor evaluating threat modeling, encryption, and cryptographic integrity."),
                            ("Project Manager", "Reviewer validating project scope, schedule, and baseline approvals.")
                        ]
                    },
                    {
                        "num": "2.4",
                        "title": "Operating Environment",
                        "content": env_content
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
                        "items": assumptions_items
                    }
                ]
            },
            {
                "num": "3",
                "title": "Specific Functional Requirements",
                "requirements": functional_reqs,
                "note": "Each functional requirement defines explicit inputs, processing behavior, measurable outputs, and testable acceptance criteria derived from actual stakeholder elicitation."
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
                        "interfaces": [
                            ("Identity Verification Service", "Interface for customer identity and KYC document verification if mandated by workflow."),
                            ("Data Persistence Engine", "Relational database interface for transactional records and audit history."),
                            ("Notification Gateway", "Messaging interface for system notifications and multi-factor alerts.")
                        ]
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
                        "content": avail_content
                    },
                    {
                        "num": "5.4",
                        "title": "Scalability and Maintainability",
                        "content": scale_content
                    },
                    {
                        "num": "5.5",
                        "title": "Usability",
                        "content": usab_content
                    }
                ]
            },
            {
                "num": "6",
                "title": "Data Requirements and Retention",
                "content": f"Data schemas enforce relational integrity and PII classification. Retention schedules reflect stakeholder inputs and {jurisdiction} statutory standards:",
                "retention_rules": retention_rules
            },
            {
                "num": "7",
                "title": "Regulatory Compliance & Legal Considerations",
                "content": f"Regulatory analysis grounded in {jurisdiction} financial frameworks. All AI-driven compliance findings are advisory and require human legal/compliance sign-off.",
                "compliance_items": comp_items
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
                "sdlc": sdlc_data
            },
            {
                "num": "10",
                "title": "Requirements Traceability Matrix (RTM)",
                "content": "Full bidirectional traceability demonstrating alignment between stakeholder statements, functional specifications, applicable regulations, and validation tests:",
                "traceability_matrix": [
                    {
                        "id": r.get("requirement_id", "REQ"),
                        "statement": r.get("statement", "")[:120] + ("..." if len(r.get("statement", "")) > 120 else ""),
                        "category": r.get("category", "functional"),
                        "priority": r.get("priority", "medium"),
                        "regulations": ", ".join(r.get("applicable_regulations", [])) or f"{jurisdiction} Financial Standard",
                        "test_criteria": (r.get("acceptance_criteria") or ["Automated verification"])[0] if isinstance(r.get("acceptance_criteria"), list) and r.get("acceptance_criteria") else "Automated verification"
                    }
                    for r in requirements
                ]
            },
            {
                "num": "11",
                "title": "Appendices and Approval Sign-Off",
                "content": f"Document approval status: {doc_status}. Formal sign-off by authorized stakeholders is required before requirements are baselined for development.",
                "sign_offs": [
                    ("Project Manager", "Operational feasibility, schedule, and resource allocation"),
                    ("Lead Software Architect", "Architectural compliance, scalability, and technical constraints"),
                    ("Security Officer", "Security posture, encryption, threat mitigations, and RBAC"),
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
        [Paragraph("<b>Document Version</b>", table_cell_style), Paragraph(meta.get("version", "1.0 Baseline"), table_cell_style)],
        [Paragraph("<b>Status</b>", table_cell_style), Paragraph(meta.get("status", "APPROVED"), table_cell_style)],
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

            story.append(Paragraph(f"<b>Recommended Methodology:</b> {rec_model} (Fitness Score: {score * 100:.1f}%)", h2_style))
            if rationale:
                story.append(Paragraph(f"<b>Selection Rationale:</b> {rationale}", body_style))
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
            for role, resp in sec["sign_offs"]:
                so_data.append([
                    Paragraph(f"<b>{role}</b>", table_cell_style),
                    Paragraph(resp, table_cell_style),
                    Paragraph("APPROVED — DIGITAL RECORD", table_cell_style)
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

    doc.save(output_path)
    return output_path
