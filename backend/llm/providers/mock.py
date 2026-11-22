"""Mock LLM provider — returns structured responses for all agent operations.

This enables the entire system to run without external API keys.
Each agent type gets context-aware mock responses that exercise
the full pipeline: extraction, classification, compliance, etc.
"""
import json
import uuid
import random
from datetime import datetime, timezone
from llm.providers.base import BaseLLMProvider


# ── Loan-processing domain mock data ──────────────────

MOCK_REQUIREMENTS = [
    {
        "requirement_id": "FR-LOAN-001",
        "statement": "The system shall verify applicant identity using government-issued ID and biometric verification before processing any loan application.",
        "category": "functional",
        "subcategory": "identity_verification",
        "business_justification": "KYC compliance requires positive identification of all loan applicants to prevent fraud and money laundering.",
        "priority": "critical",
        "acceptance_criteria": [
            "System accepts government-issued photo ID (passport, driver's license, national ID)",
            "Biometric verification achieves 99.5% accuracy rate",
            "Failed verification blocks loan application progression",
            "All verification attempts are logged with timestamps"
        ],
        "applicable_regulations": ["KYC Regulations", "AML Directives", "Data Protection Act"],
        "risks": [{"description": "Identity fraud if verification is bypassed", "level": "high", "mitigation": "Multi-factor verification with liveness detection"}],
        "confidence": 0.92
    },
    {
        "requirement_id": "FR-LOAN-002",
        "statement": "The system shall perform automated credit scoring using applicant financial history, income verification, and debt-to-income ratio analysis.",
        "category": "functional",
        "subcategory": "credit_assessment",
        "business_justification": "Automated credit scoring reduces processing time and ensures consistent evaluation criteria across all applications.",
        "priority": "critical",
        "acceptance_criteria": [
            "Credit score calculated within 30 seconds of data submission",
            "Score considers minimum 3 years of credit history",
            "Debt-to-income ratio threshold configurable by product type",
            "Manual override available for edge cases with audit trail"
        ],
        "applicable_regulations": ["Fair Lending Regulations", "Consumer Credit Act"],
        "risks": [{"description": "Biased scoring algorithm leading to discriminatory lending", "level": "high", "mitigation": "Regular bias audits and explainable AI scoring"}],
        "confidence": 0.89
    },
    {
        "requirement_id": "FR-LOAN-003",
        "statement": "The system shall enforce configurable loan amount limits based on product type, applicant risk profile, and regulatory requirements.",
        "category": "functional",
        "subcategory": "loan_limits",
        "business_justification": "Regulatory compliance requires adherence to lending limits and risk-based pricing.",
        "priority": "high",
        "acceptance_criteria": [
            "Loan limits configurable per product category",
            "Limits automatically adjusted based on risk assessment",
            "Exceeding limits triggers mandatory manual review",
            "All limit calculations are auditable"
        ],
        "applicable_regulations": ["Prudential Lending Standards", "Consumer Protection Regulations"],
        "risks": [{"description": "Exceeding regulatory lending limits", "level": "medium", "mitigation": "Automated limit enforcement with compliance alerts"}],
        "confidence": 0.87
    },
    {
        "requirement_id": "NFR-SEC-001",
        "statement": "The system shall encrypt all personally identifiable information (PII) at rest using AES-256 and in transit using TLS 1.3.",
        "category": "security",
        "subcategory": "encryption",
        "business_justification": "Protection of sensitive financial and personal data is a regulatory and business imperative.",
        "priority": "critical",
        "acceptance_criteria": [
            "All PII fields encrypted at rest in database",
            "All API communications use TLS 1.3 minimum",
            "Encryption keys rotated on defined schedule",
            "Key management follows industry standards"
        ],
        "applicable_regulations": ["Data Protection Act", "PCI-DSS", "Information Security Standards"],
        "risks": [{"description": "Data breach exposing customer PII", "level": "critical", "mitigation": "Defense-in-depth encryption strategy with monitoring"}],
        "confidence": 0.95
    },
    {
        "requirement_id": "NFR-SEC-002",
        "statement": "The system shall implement role-based access control with multi-factor authentication for all staff accessing loan processing functions.",
        "category": "security",
        "subcategory": "access_control",
        "business_justification": "Prevents unauthorized access to sensitive loan data and processing functions.",
        "priority": "critical",
        "acceptance_criteria": [
            "Minimum 3 role levels: viewer, processor, approver",
            "MFA required for all staff logins",
            "Session timeout after 15 minutes of inactivity",
            "All access attempts logged"
        ],
        "applicable_regulations": ["Information Security Standards", "Access Control Policies"],
        "risks": [{"description": "Unauthorized access to loan records", "level": "high", "mitigation": "RBAC with MFA and continuous session monitoring"}],
        "confidence": 0.93
    },
    {
        "requirement_id": "NFR-PERF-001",
        "statement": "The loan application submission process shall complete within 5 seconds under normal load conditions and support 500 concurrent users.",
        "category": "performance",
        "subcategory": "response_time",
        "business_justification": "User experience and competitive positioning require fast application processing.",
        "priority": "high",
        "acceptance_criteria": [
            "95th percentile response time under 5 seconds",
            "System supports 500 concurrent loan applications",
            "Graceful degradation under peak load",
            "Performance metrics monitored in real-time"
        ],
        "applicable_regulations": [],
        "risks": [{"description": "System overload during peak periods", "level": "medium", "mitigation": "Auto-scaling infrastructure with load balancing"}],
        "confidence": 0.85
    },
    {
        "requirement_id": "FR-LOAN-004",
        "statement": "The system shall generate a complete audit trail for each loan application including all status changes, approvals, document submissions, and communication records.",
        "category": "audit_reporting",
        "subcategory": "audit_trail",
        "business_justification": "Regulatory examination readiness requires complete, tamper-evident audit trails for all loan transactions.",
        "priority": "critical",
        "acceptance_criteria": [
            "Every state change recorded with timestamp and user ID",
            "Audit records are immutable once written",
            "Audit trail accessible for regulatory examination",
            "Retention period meets regulatory requirements (minimum 7 years)"
        ],
        "applicable_regulations": ["Banking Examination Guidelines", "Record Retention Regulations"],
        "risks": [{"description": "Incomplete audit trail leading to regulatory findings", "level": "high", "mitigation": "Automated audit logging at all decision points"}],
        "confidence": 0.91
    },
]

MOCK_INTERVIEW_QUESTIONS = {
    "business_objectives": [
        "What are the primary business objectives for this loan processing system?",
        "What types of loans will this system handle (personal, mortgage, business, auto)?",
        "What is the expected monthly loan application volume?"
    ],
    "users_roles": [
        "Who are the primary users of the loan processing system?",
        "What roles need access to the system (loan officers, underwriters, compliance staff)?",
        "Will customers interact directly with the system or only through staff?"
    ],
    "workflow": [
        "Can you describe the current loan processing workflow from application to disbursement?",
        "What are the key decision points in the loan approval process?",
        "How are exceptions and edge cases currently handled?"
    ],
    "data_requirements": [
        "What customer data needs to be collected during the application process?",
        "What external data sources need to be integrated (credit bureaus, income verification)?",
        "What are the data retention requirements for loan records?"
    ],
    "security": [
        "What authentication mechanisms are currently in place for staff access?",
        "Are there specific encryption requirements for data at rest and in transit?",
        "What are the incident response procedures for data breaches?"
    ],
    "compliance": [
        "Which regulatory frameworks apply to your loan processing operations?",
        "Are there jurisdiction-specific lending regulations to consider?",
        "How are regulatory changes currently incorporated into your processes?"
    ],
    "integration": [
        "What existing systems need to integrate with the new loan processing platform?",
        "Are there specific API standards or protocols required for integration?",
        "How should the system handle integration failures or timeouts?"
    ],
    "performance": [
        "What are the expected response time requirements for loan application processing?",
        "What are the peak load periods and expected concurrent user counts?",
        "Are there specific availability or uptime requirements?"
    ],
    "exceptional_conditions": [
    "How should the system handle incomplete applications, invalid documents, or failed verification?"
    ],
    "audit_reporting": [
        "What audit logs and operational reports should the system generate?"
    ],
    "transaction_limits": [
        "Are there any minimum or maximum loan amounts or transaction limits?"
    ],
    "schedule_budget": [
        "Are there any project deadlines, implementation milestones, or budget constraints?"
    ],
}

MOCK_QUALITY_ISSUES = {
    "ambiguous": {
        "issue": "ambiguity",
        "description": "The requirement uses vague terms that could be interpreted in multiple ways.",
        "suggestion": "Replace vague terms with specific, measurable criteria."
    },
    "incomplete": {
        "issue": "incompleteness",
        "description": "The requirement lacks sufficient detail for implementation.",
        "suggestion": "Add acceptance criteria, constraints, and boundary conditions."
    },
    "untestable": {
        "issue": "lack_of_testability",
        "description": "The requirement cannot be verified through testing.",
        "suggestion": "Add measurable acceptance criteria and expected outcomes."
    },
}

MOCK_SDLC_ANALYSIS = {
    "waterfall": {"score": 0.35, "rationale": "Regulatory requirements provide stability but financial systems need iterative development for compliance updates."},
    "v_model": {"score": 0.55, "rationale": "Strong verification/validation alignment with compliance testing needs, but limited flexibility for changing requirements."},
    "spiral": {"score": 0.45, "rationale": "Good risk management approach for financial systems, but may extend timelines beyond budget constraints."},
    "agile": {"score": 0.60, "rationale": "Enables iterative compliance integration and stakeholder feedback, but needs additional governance for regulatory requirements."},
    "devsecops": {"score": 0.70, "rationale": "Continuous security integration aligns with financial system requirements; automated compliance checks fit CI/CD pipelines."},
    "hybrid_agile_vmodel": {"score": 0.80, "rationale": "Combines Agile iteration speed with V-Model verification rigor; best fit for regulated financial systems with evolving requirements."},
}


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider that returns realistic, structured responses
    for all agent operations without requiring external API credentials.
    """

    def __init__(self):
        self.call_count = 0

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        self.call_count += 1

        prompt_lower = prompt.lower()

        # Route to appropriate mock response based on prompt content
        if "interview" in prompt_lower or "question" in prompt_lower or "stakeholder" in prompt_lower:
            return self._mock_interview_response(prompt)
        elif "extract" in prompt_lower and "requirement" in prompt_lower:
            return self._mock_extraction_response(prompt)
        elif "clarif" in prompt_lower:
            return self._mock_clarification_response(prompt)
        elif "classif" in prompt_lower:
            return self._mock_classification_response(prompt)
        elif "conflict" in prompt_lower or "duplicate" in prompt_lower:
            return self._mock_conflict_response(prompt)
        elif "compliance" in prompt_lower or "regulat" in prompt_lower:
            return self._mock_compliance_response(prompt)
        elif "security" in prompt_lower or "privacy" in prompt_lower:
            return self._mock_security_response(prompt)
        elif "risk" in prompt_lower:
            return self._mock_risk_response(prompt)
        elif "sdlc" in prompt_lower or "lifecycle" in prompt_lower:
            return self._mock_sdlc_response(prompt)
        elif "srs" in prompt_lower or "document" in prompt_lower or "generat" in prompt_lower:
            return self._mock_documentation_response(prompt)
        elif "validat" in prompt_lower or "quality" in prompt_lower:
            return self._mock_validation_response(prompt)
        else:
            return self._mock_generic_response(prompt)

    async def generate_structured(self, prompt: str, system_prompt: str = "",
                                   schema: dict | None = None,
                                   temperature: float = 0.1) -> dict:
        self.call_count += 1
        text = await self.generate(prompt, system_prompt, temperature)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"response": text, "structured": False}

    def get_model_info(self) -> dict:
        return {
            "provider": "mock",
            "model": "mock-financial-llm-v1",
            "version": "1.0.0",
            "calls": self.call_count
        }

    # ── Mock response generators ──

    
    def _mock_interview_response(self, prompt: str) -> str:
        # Read the explicitly provided remaining topics.
        remaining_line = next(
            (
                line for line in prompt.splitlines()
                if line.strip().startswith("Topics remaining:")
            ),
            ""
        )

        remaining_text = remaining_line.split(":", 1)[-1].strip()
        remaining_topics = [
            topic.strip()
            for topic in remaining_text.split(",")
            if topic.strip() and topic.strip() != "None"
        ]

        # Select the first remaining topic supported by mock questions.
        topic = next(
            (
                topic for topic in remaining_topics
                if topic in MOCK_INTERVIEW_QUESTIONS
            ),
            None
        )

        # Only wrap up when no supported topics remain.
        if topic is None:
            return json.dumps({
                "question": (
                    "Based on our discussion, are there any "
                    "additional requirements or constraints "
                    "you'd like to highlight?"
                ),
                "topic": "wrap_up",
                "follow_up": False,
                "reasoning": "All supported interview topics have been covered."
            })

        question = MOCK_INTERVIEW_QUESTIONS[topic][0]

        return json.dumps({
            "question": question,
            "topic": topic,
            "follow_up": True,
            "reasoning": (
                f"Gathering information about "
                f"{topic.replace('_', ' ')}."
            )
        })


    def _mock_extraction_response(self, prompt: str) -> str:
        # Return a subset of mock requirements
        count = min(3, len(MOCK_REQUIREMENTS))
        selected = random.sample(MOCK_REQUIREMENTS, count)
        return json.dumps({
            "requirements": selected,
            "extraction_notes": "Requirements extracted from stakeholder input and supporting documents.",
            "confidence": 0.88,
            "gaps_identified": ["Disaster recovery requirements not yet addressed", "Mobile access requirements unclear"]
        })

    def _mock_clarification_response(self, prompt: str) -> str:
        return json.dumps({
            "clarification_needed": True,
            "questions": [
                {
                    "target_requirement": "FR-LOAN-003",
                    "question": "What specific loan amount limits should apply to each product category (personal, mortgage, business)?",
                    "reason": "The requirement mentions configurable limits but does not specify the initial values or ranges.",
                    "priority": "high"
                },
                {
                    "target_requirement": "NFR-PERF-001",
                    "question": "What constitutes 'normal load conditions' — how many concurrent users and transactions per second?",
                    "reason": "Performance requirements need specific measurable thresholds.",
                    "priority": "medium"
                }
            ],
            "confidence": 0.75
        })

    def _mock_classification_response(self, prompt: str) -> str:
        return json.dumps({
            "classifications": [
                {"requirement_id": "FR-LOAN-001", "primary_category": "functional", "subcategories": ["identity_verification", "security"], "labels": ["kyc", "compliance", "onboarding"]},
                {"requirement_id": "FR-LOAN-002", "primary_category": "functional", "subcategories": ["credit_assessment", "data"], "labels": ["scoring", "analytics", "risk"]},
                {"requirement_id": "NFR-SEC-001", "primary_category": "security", "subcategories": ["encryption", "data_protection"], "labels": ["pii", "compliance", "infrastructure"]},
            ],
            "multi_label_rationale": "Financial requirements frequently span multiple categories due to regulatory and security overlap.",
            "confidence": 0.90
        })

    def _mock_conflict_response(self, prompt: str) -> str:
        return json.dumps({
            "conflicts": [
                {
                    "type": "potential_conflict",
                    "requirement_a": "NFR-PERF-001",
                    "requirement_b": "NFR-SEC-001",
                    "description": "Performance requirement for 5-second response may conflict with encryption overhead for PII data processing.",
                    "severity": "medium",
                    "resolution_suggestion": "Implement encryption at the data layer with hardware acceleration to minimize performance impact."
                }
            ],
            "duplicates": [],
            "confidence": 0.82
        })

    def _mock_compliance_response(self, prompt: str) -> str:
        return json.dumps({
            "compliance_analysis": [
                {
                    "requirement_id": "FR-LOAN-001",
                    "applicable_regulations": [
                        {"name": "KYC Regulations", "jurisdiction": "general", "relevance": "high"},
                        {"name": "Anti-Money Laundering (AML) Directives", "jurisdiction": "general", "relevance": "high"}
                    ],
                    "required_controls": ["Identity verification procedures", "Document authentication", "Suspicious activity reporting"],
                    "compliance_gaps": ["Liveness detection for biometric verification not specified"],
                    "evidence": ["KYC/AML requirements mandate positive identification for financial transactions"],
                    "approval_required": True,
                    "data_retention": "Customer identification records must be retained for minimum 5 years after account closure"
                }
            ],
            "disclaimer": "This analysis is advisory only. Final compliance determinations must be made by qualified legal and compliance personnel.",
            "confidence": 0.85
        })

    def _mock_security_response(self, prompt: str) -> str:
        return json.dumps({
            "security_analysis": [
                {
                    "requirement_id": "FR-LOAN-002",
                    "security_concerns": ["Credit data transmission requires encryption", "Scoring algorithm must prevent unauthorized access"],
                    "privacy_concerns": ["Financial history constitutes sensitive personal data", "Income data subject to data protection regulations"],
                    "recommended_controls": [
                        {"control": "Data encryption in transit and at rest", "standard": "AES-256, TLS 1.3"},
                        {"control": "Access logging for credit data queries", "standard": "Audit trail requirements"},
                        {"control": "Data minimization for scoring inputs", "standard": "Data protection principles"}
                    ],
                    "threat_level": "high",
                    "data_classification": "confidential"
                }
            ],
            "confidence": 0.87
        })

    def _mock_risk_response(self, prompt: str) -> str:
        return json.dumps({
            "risk_assessment": [
                {
                    "risk_id": "RISK-001",
                    "category": "compliance",
                    "description": "Non-compliance with KYC/AML regulations could result in significant fines and operational restrictions.",
                    "likelihood": "medium",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Implement comprehensive identity verification with regulatory-compliant audit trail.",
                    "related_requirements": ["FR-LOAN-001", "FR-LOAN-004"]
                },
                {
                    "risk_id": "RISK-002",
                    "category": "technical",
                    "description": "Integration with external credit bureaus may introduce latency and single points of failure.",
                    "likelihood": "high",
                    "impact": "medium",
                    "risk_level": "medium",
                    "mitigation": "Implement circuit breaker patterns and fallback scoring mechanisms.",
                    "related_requirements": ["FR-LOAN-002", "NFR-PERF-001"]
                },
                {
                    "risk_id": "RISK-003",
                    "category": "security",
                    "description": "Data breach of loan applicant PII could result in regulatory action and reputational damage.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Defense-in-depth security architecture with encryption, access controls, and monitoring.",
                    "related_requirements": ["NFR-SEC-001", "NFR-SEC-002"]
                }
            ],
            "overall_risk_level": "high",
            "confidence": 0.83
        })

    def _mock_sdlc_response(self, prompt: str) -> str:
        return json.dumps({
            "recommendation": {
                "primary": "hybrid_agile_vmodel",
                "display_name": "Agile-V-Model Hybrid",
                "confidence": 0.80,
                "rationale": "A hybrid Agile-V-Model approach is recommended for this loan processing system. The regulatory requirements demand the rigorous verification and validation phases of V-Model, while evolving business requirements and stakeholder feedback cycles benefit from Agile iteration. This hybrid approach provides sprint-based development with formal verification gates aligned to compliance checkpoints."
            },
            "scores": MOCK_SDLC_ANALYSIS,
            "factors": {
                "requirement_stability": 0.6,
                "regulatory_criticality": 0.9,
                "security_risk": 0.85,
                "complexity": 0.7,
                "system_size": 0.6,
                "legacy_dependence": 0.4,
                "change_frequency": 0.5,
                "continuous_delivery": 0.6,
                "stakeholder_availability": 0.7,
                "testing_requirements": 0.85,
                "budget_schedule_pressure": 0.5,
                "formal_verification": 0.75,
                "failure_consequences": 0.9
            },
            "alternatives": [
                {"model": "devsecops", "score": 0.70, "rationale": "Strong option if continuous deployment is prioritized."},
                {"model": "agile", "score": 0.60, "rationale": "Good for rapid iteration but needs additional compliance governance."}
            ],
            "requires_approval": True
        })

    def _mock_documentation_response(self, prompt: str) -> str:
        if "srs" in prompt.lower():
            return self._mock_srs()
        elif "user stor" in prompt.lower():
            return self._mock_user_stories()
        elif "use case" in prompt.lower():
            return self._mock_use_cases()
        else:
            return json.dumps({"content": "Document generated successfully.", "type": "general"})

    def _mock_srs(self) -> str:
        return json.dumps({
            "title": "Software Requirements Specification — Loan Processing System",
            "sections": {
                "1_introduction": {
                    "purpose": "This SRS defines the functional and non-functional requirements for the Loan Processing System.",
                    "scope": "The system handles loan application intake, credit assessment, approval workflow, disbursement, and regulatory compliance.",
                    "audience": "Development team, QA, compliance, and project stakeholders."
                },
                "2_functional_requirements": [r for r in MOCK_REQUIREMENTS if r["category"] == "functional"],
                "3_non_functional_requirements": [r for r in MOCK_REQUIREMENTS if r["category"] != "functional"],
                "4_constraints": ["Must comply with applicable financial regulations", "Must integrate with existing core banking system"],
                "5_assumptions": ["Credit bureau APIs are available and reliable", "Staff will receive training before system launch"]
            },
            "traceability": {"source": "stakeholder_interviews", "evidence_count": 7}
        })

    def _mock_user_stories(self) -> str:
        return json.dumps({
            "user_stories": [
                {
                    "id": "US-001",
                    "story": "As a loan officer, I want to verify applicant identity through automated checks so that I can ensure KYC compliance before processing the application.",
                    "acceptance_criteria": ["Government ID scan accepted", "Biometric match confirmed", "Verification logged"],
                    "source_requirement": "FR-LOAN-001",
                    "priority": "critical"
                },
                {
                    "id": "US-002",
                    "story": "As an underwriter, I want to see automated credit scores with detailed factor breakdowns so that I can make informed lending decisions.",
                    "acceptance_criteria": ["Credit score displayed within 30 seconds", "Factor breakdown visible", "Override option available"],
                    "source_requirement": "FR-LOAN-002",
                    "priority": "critical"
                },
                {
                    "id": "US-003",
                    "story": "As a compliance officer, I want to access complete audit trails for any loan application so that I can demonstrate regulatory compliance during examinations.",
                    "acceptance_criteria": ["Full history viewable", "Records immutable", "Export functionality available"],
                    "source_requirement": "FR-LOAN-004",
                    "priority": "critical"
                }
            ]
        })

    def _mock_use_cases(self) -> str:
        return json.dumps({
            "use_cases": [
                {
                    "id": "UC-001",
                    "title": "Submit Loan Application",
                    "actor": "Loan Applicant",
                    "preconditions": ["Applicant has valid identification", "System is operational"],
                    "main_flow": [
                        "1. Applicant accesses loan application portal",
                        "2. System presents application form",
                        "3. Applicant enters personal and financial information",
                        "4. System validates input data",
                        "5. Applicant uploads required documents",
                        "6. System initiates identity verification",
                        "7. System confirms application submission"
                    ],
                    "alternative_flows": ["4a. Validation fails — system highlights errors for correction"],
                    "postconditions": ["Application recorded in system", "Audit trail created"],
                    "source_requirements": ["FR-LOAN-001", "FR-LOAN-004"]
                }
            ]
        })

    def _mock_validation_response(self, prompt: str) -> str:
        return json.dumps({
            "validation_results": {
                "completeness": 0.85,
                "consistency": 0.90,
                "testability": 0.88,
                "traceability": 0.82,
                "overall_quality": 0.86
            },
            "issues": [
                {"type": "incompleteness", "requirement": "FR-LOAN-003", "detail": "Loan limit ranges not specified"},
                {"type": "ambiguity", "requirement": "NFR-PERF-001", "detail": "'Normal load conditions' needs definition"}
            ],
            "recommendations": [
                "Add specific loan limit values for each product category",
                "Define 'normal load' in terms of concurrent users and TPS",
                "Add disaster recovery and business continuity requirements"
            ],
            "confidence": 0.86
        })

    def _mock_generic_response(self, prompt: str) -> str:
        return json.dumps({
            "response": "Analysis completed. The financial requirements have been processed according to the specified criteria.",
            "confidence": 0.80,
            "notes": "This is a mock response for development. Connect a real LLM provider for production use."
        })
