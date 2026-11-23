"""Mock LLM provider — dynamically derives realistic responses for all agent operations.
Used for offline testing and test harness.
"""
import json
import re
from llm.providers.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """Dynamic mock LLM provider that extracts and structures data based on input."""

    def __init__(self):
        self.call_count = 0

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        self.call_count += 1
        prompt_lower = prompt.lower()

        if "extract" in prompt_lower and "requirement" in prompt_lower:
            return self._mock_extraction_response(prompt)
        elif "interview" in prompt_lower or "stakeholder" in prompt_lower:
            return self._mock_interview_response(prompt)
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
        elif "srs" in prompt_lower or "software requirements" in prompt_lower:
            return self._mock_srs_response(prompt)
        elif "validat" in prompt_lower or "quality" in prompt_lower:
            return self._mock_validation_response(prompt)
        else:
            return json.dumps({
                "response": "Analysis completed according to financial domain standards.",
                "confidence": 0.85
            })

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
            "model": "mock-financial-llm-v2",
            "version": "2.0.0",
            "calls": self.call_count
        }

    # ── Helpers to parse IDs from prompt ──────────────────
    def _extract_req_ids(self, prompt: str) -> list[str]:
        ids = re.findall(r'["\']requirement_id["\']\s*:\s*["\']([^"\']+)["\']', prompt)
        if not ids:
            ids = re.findall(r'(?:FR|NFR)-[A-Z0-9]+-[0-9]{3}', prompt)
        return list(dict.fromkeys(ids))

    # ── Mock Response Generators ─────────────────────────

    def _mock_interview_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()
        if "wrap_up" in prompt_lower or "topics remaining: none" in prompt_lower:
            return json.dumps({
                "question": "Thank you for these comprehensive details. We have covered all essential functional, security, compliance, and architectural topics. Shall we proceed to requirement extraction?",
                "topic": "wrap_up",
                "follow_up": False,
                "reasoning": "Interview topics have been sufficiently explored for requirements synthesis."
            })

        # Adaptive questions based on what user mentioned
        if "loan" in prompt_lower or "kyc" in prompt_lower or "identity" in prompt_lower:
            return json.dumps({
                "question": "What specific customer verification and KYC compliance steps are required before a loan can be approved? For example, are government ID uploads, credit bureau integration, or biometric checks required?",
                "topic": "compliance",
                "follow_up": True,
                "reasoning": "Inquiring about regulatory identity verification requirements."
            })
        elif "security" in prompt_lower or "encrypt" in prompt_lower or "access" in prompt_lower:
            return json.dumps({
                "question": "Could you specify the security and access control model for financial transactions? Are there specific encryption standards (e.g. AES-256, TLS 1.3) or multi-factor authentication requirements for staff and applicants?",
                "topic": "security",
                "follow_up": True,
                "reasoning": "Clarifying data protection and security access controls."
            })
        elif "workflow" in prompt_lower or "approval" in prompt_lower or "limit" in prompt_lower:
            return json.dumps({
                "question": "What are the decision thresholds and automated approval criteria? For instance, what is the maximum loan amount that can be auto-approved versus requiring multi-level underwriter review?",
                "topic": "workflow",
                "follow_up": True,
                "reasoning": "Defining business workflow decision logic and approval limits."
            })
        elif "performance" in prompt_lower or "user" in prompt_lower or "volume" in prompt_lower:
            return json.dumps({
                "question": "What are your expected performance targets and peak concurrency levels? For example, target response times for credit decisioning and peak concurrent users?",
                "topic": "performance",
                "follow_up": True,
                "reasoning": "Establishing non-functional performance benchmarks."
            })
        else:
            return json.dumps({
                "question": "What are the core business objectives, expected loan products (personal, mortgage, commercial), and primary regulatory jurisdictions for this platform?",
                "topic": "business_objectives",
                "follow_up": True,
                "reasoning": "Initiating high-level business scope and regulatory context."
            })

    def _mock_extraction_response(self, prompt: str) -> str:
        # Extract from the actual source text inside the prompt!
        text_match = re.search(r"(?:Source text:|--- TRANSCRIPT BEGIN ---)\s*([\s\S]*?)(?:--- TRANSCRIPT END ---|Extract ALL identifiable|\Z)", prompt)
        source_text = text_match.group(1).strip() if text_match else prompt

        requirements = []
        counter = 1

        # Check topics in source text
        source_lower = source_text.lower()

        # 1. Identity / KYC
        if any(w in source_lower for w in ["identity", "kyc", "government id", "passport", "biometric", "verify applicant", "onboard"]):
            requirements.append({
                "requirement_id": f"FR-LOAN-{counter:03d}",
                "statement": "The system shall verify applicant identity using government-issued photo identification and automated KYC verification prior to loan application progression.",
                "category": "functional",
                "subcategory": "identity_verification",
                "business_justification": "Mandated by KYC and AML regulations to prevent identity fraud and unauthorized lending.",
                "priority": "critical",
                "acceptance_criteria": [
                    "Accepts valid government ID formats (passport, driver license, national ID)",
                    "Validates document authenticity against authorized databases within 60 seconds",
                    "Blocks unverified applications from moving to credit decision stage",
                    "Logs all verification transactions with immutable timestamp and officer ID"
                ],
                "applicable_regulations": ["KYC Regulations", "AML Directives", "Data Protection Act"],
                "risks": [{"description": "Identity fraud if bypass occurs", "level": "high", "mitigation": "Multi-factor verification and manual review queue"}],
                "confidence": 0.94
            })
            counter += 1

        # 2. Credit Scoring / Assessment
        if any(w in source_lower for w in ["credit", "scoring", "financial history", "debt", "income", "assessment", "score"]):
            requirements.append({
                "requirement_id": f"FR-LOAN-{counter:03d}",
                "statement": "The system shall compute an automated credit score based on applicant financial history, income verification, and debt-to-income ratio analysis.",
                "category": "functional",
                "subcategory": "credit_assessment",
                "business_justification": "Standardizes credit risk assessment and accelerates lending turnaround time.",
                "priority": "critical",
                "acceptance_criteria": [
                    "Calculates credit score within 30 seconds of receiving verified credit bureau data",
                    "Enforces configurable debt-to-income (DTI) thresholds per loan product category",
                    "Provides explainable risk factor breakdown for all credit decisions",
                    "Enables authorized underwriter manual override with mandatory rationale logging"
                ],
                "applicable_regulations": ["Fair Lending Regulations", "Consumer Credit Act"],
                "risks": [{"description": "Algorithm bias or scoring inaccuracy", "level": "high", "mitigation": "Periodic model validation and explainable AI scoring"}],
                "confidence": 0.92
            })
            counter += 1

        # 3. Loan Limits / Approval Workflow
        if any(w in source_lower for w in ["limit", "amount", "threshold", "mortgage", "personal loan", "approval", "underwriter"]):
            requirements.append({
                "requirement_id": f"FR-LOAN-{counter:03d}",
                "statement": "The system shall enforce configurable loan amount limits and route applications exceeding threshold amounts to senior underwriters for dual approval.",
                "category": "functional",
                "subcategory": "approval_workflow",
                "business_justification": "Ensures risk-appropriate authorization and compliance with prudential lending limits.",
                "priority": "high",
                "acceptance_criteria": [
                    "Applies distinct maximum credit ceilings per product tier (e.g. personal up to $50,000, mortgage up to $1,000,000)",
                    "Automatically routes high-value applications to two-person authorization workflow",
                    "Maintains tamper-evident record of all approver decisions and timestamps"
                ],
                "applicable_regulations": ["Prudential Lending Standards", "Internal Credit Policy"],
                "risks": [{"description": "Exceeding regulatory exposure limits", "level": "medium", "mitigation": "Automated workflow enforcement with limit checks"}],
                "confidence": 0.90
            })
            counter += 1

        # 4. Security / Encryption
        if any(w in source_lower for w in ["encrypt", "aes", "tls", "security", "pii", "protect"]):
            requirements.append({
                "requirement_id": f"NFR-SEC-{counter:03d}",
                "statement": "The system shall encrypt all customer personally identifiable information (PII) and financial records at rest using AES-256 and in transit using TLS 1.3.",
                "category": "security",
                "subcategory": "cryptography",
                "business_justification": "Protection of sensitive consumer financial data is an absolute regulatory mandate.",
                "priority": "critical",
                "acceptance_criteria": [
                    "All database columns containing PII, account numbers, or tax IDs are encrypted with AES-256",
                    "All external and internal REST API endpoints enforce TLS 1.3 minimum cipher suites",
                    "Cryptographic keys are managed via dedicated KMS with annual rotation"
                ],
                "applicable_regulations": ["Data Protection Act", "PCI-DSS", "Financial Security Standards"],
                "risks": [{"description": "Data breach exposing customer financial records", "level": "critical", "mitigation": "Zero-trust architecture, tokenization, and end-to-end encryption"}],
                "confidence": 0.96
            })
            counter += 1

        # 5. Access Control / MFA
        if any(w in source_lower for w in ["mfa", "role", "rbac", "access", "staff", "auth", "login"]):
            requirements.append({
                "requirement_id": f"NFR-SEC-{counter:03d}",
                "statement": "The system shall implement granular role-based access control (RBAC) and mandatory multi-factor authentication (MFA) for all administrative and underwriting staff.",
                "category": "security",
                "subcategory": "access_control",
                "business_justification": "Prevents unauthorized access and privilege escalation within lending operations.",
                "priority": "critical",
                "acceptance_criteria": [
                    "Supports distinct roles: applicant, loan officer, underwriter, compliance officer, system admin",
                    "Enforces hardware/software token MFA for all back-office logins",
                    "Automatic session invalidation after 15 minutes of inactivity"
                ],
                "applicable_regulations": ["Information Security Standards", "Banking Access Guidelines"],
                "risks": [{"description": "Account compromise by malicious actors", "level": "high", "mitigation": "MFA, IP allowlisting, and anomaly detection"}],
                "confidence": 0.93
            })
            counter += 1

        # 6. Performance / Scalability
        if any(w in source_lower for w in ["concurrent", "user", "speed", "response", "second", "load", "performance", "scalability"]):
            requirements.append({
                "requirement_id": f"NFR-PERF-{counter:03d}",
                "statement": "The loan application intake portal shall handle at least 500 concurrent users with 95th percentile page response times under 3.0 seconds under normal operations.",
                "category": "performance",
                "subcategory": "response_time",
                "business_justification": "Provides friction-free customer onboarding and avoids application drop-offs.",
                "priority": "high",
                "acceptance_criteria": [
                    "95% of customer portal interactions complete in under 3.0 seconds",
                    "Sustains 500 concurrent active loan application sessions without error rate exceeding 0.1%",
                    "Graceful degradation with informative status during upstream service degradation"
                ],
                "applicable_regulations": [],
                "risks": [{"description": "System throttling during peak marketing campaigns", "level": "medium", "mitigation": "Horizontal container auto-scaling and Redis caching"}],
                "confidence": 0.88
            })
            counter += 1

        # 7. Audit Logging / Retention
        if any(w in source_lower for w in ["audit", "log", "trail", "history", "retention", "compliance"]):
            requirements.append({
                "requirement_id": f"FR-LOAN-{counter:03d}",
                "statement": "The system shall maintain an immutable, tamper-evident audit trail recording every state change, document submission, underwriting decision, and external API call for 7 years.",
                "category": "audit_reporting",
                "subcategory": "audit_trail",
                "business_justification": "Required for statutory bank regulatory examinations and forensic audits.",
                "priority": "critical",
                "acceptance_criteria": [
                    "All status changes log user ID, timestamp (UTC), IP, previous state, and new state",
                    "Audit records are write-once, read-many (WORM) and cannot be deleted or altered",
                    "Automated retention policy preserves records for exactly 7 years minimum"
                ],
                "applicable_regulations": ["Record Retention Guidelines", "Banking Examination Guidelines"],
                "risks": [{"description": "Regulatory penalties for incomplete transaction audit records", "level": "high", "mitigation": "Append-only database journaling with cryptographic hashing"}],
                "confidence": 0.95
            })
            counter += 1

        # Default fallback requirements if user text was very short
        if not requirements:
            requirements = [
                {
                    "requirement_id": "FR-LOAN-001",
                    "statement": "The system shall provide digital loan application intake with applicant identity verification and eligibility validation.",
                    "category": "functional",
                    "subcategory": "intake",
                    "business_justification": "Core entry point for digital financial services.",
                    "priority": "critical",
                    "acceptance_criteria": ["Captures personal and employment data", "Validates input formats"],
                    "applicable_regulations": ["KYC Regulations"],
                    "risks": [{"description": "Incomplete submission", "level": "medium", "mitigation": "Step-by-step form validation"}],
                    "confidence": 0.90
                },
                {
                    "requirement_id": "NFR-SEC-002",
                    "statement": "The system shall encrypt all sensitive customer and financial records at rest using AES-256.",
                    "category": "security",
                    "subcategory": "encryption",
                    "business_justification": "Protection of consumer data.",
                    "priority": "critical",
                    "acceptance_criteria": ["Database encryption active", "TLS 1.3 in transit"],
                    "applicable_regulations": ["Data Protection Act"],
                    "risks": [{"description": "Data leak", "level": "critical", "mitigation": "Standardized encryption"}],
                    "confidence": 0.95
                }
            ]

        return json.dumps({
            "requirements": requirements,
            "extraction_notes": f"Extracted {len(requirements)} domain requirements from stakeholder session input.",
            "confidence": 0.91,
            "gaps_identified": [
                "Integration interface specifications for external credit bureaus should be formalized",
                "Specific disaster recovery time objectives (RTO/RPO) require stakeholder sign-off"
            ]
        })

    def _mock_clarification_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        questions = []
        if req_ids:
            target_1 = req_ids[0]
            questions.append({
                "target_requirement": target_1,
                "question": f"For {target_1}, what specific fallback procedures should apply if automated verification is temporarily unavailable?",
                "reason": "Boundary and exception conditions need explicit definition.",
                "priority": "high"
            })
            if len(req_ids) > 1:
                target_2 = req_ids[1]
                questions.append({
                    "target_requirement": target_2,
                    "question": f"For {target_2}, are there specific external API timeout limits and retry strategies to enforce?",
                    "reason": "Clarification required on SLA parameters and failure recovery.",
                    "priority": "medium"
                })

        return json.dumps({
            "clarification_needed": len(questions) > 0,
            "questions": questions,
            "confidence": 0.84
        })

    def _mock_classification_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        classifications = []
        for rid in req_ids:
            cat = "security" if "SEC" in rid else ("performance" if "PERF" in rid else "functional")
            classifications.append({
                "requirement_id": rid,
                "primary_category": cat,
                "subcategories": ["compliance", "banking"],
                "labels": ["financial", "core", cat]
            })

        return json.dumps({
            "classifications": classifications,
            "multi_label_rationale": "Financial requirements cross-cut functional workflows, data security, and statutory compliance.",
            "confidence": 0.92
        })

    def _mock_conflict_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        conflicts = []
        perf_req = next((r for r in req_ids if "PERF" in r), None)
        sec_req = next((r for r in req_ids if "SEC" in r), None)

        if perf_req and sec_req:
            conflicts.append({
                "type": "potential_latency_tradeoff",
                "requirement_a": perf_req,
                "requirement_b": sec_req,
                "description": f"Sub-second latency in {perf_req} may be impacted by multi-layer cryptographic operations specified in {sec_req}.",
                "severity": "medium",
                "resolution_suggestion": "Utilize hardware cryptographic acceleration and asynchronous verification queues."
            })

        return json.dumps({
            "conflicts": conflicts,
            "duplicates": [],
            "confidence": 0.88
        })

    def _mock_compliance_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        analysis = []
        for rid in req_ids:
            analysis.append({
                "requirement_id": rid,
                "applicable_regulations": [
                    {"name": "KYC/AML Guidelines", "jurisdiction": "statutory", "relevance": "high"},
                    {"name": "Financial Consumer Protection Act", "jurisdiction": "federal", "relevance": "high"}
                ],
                "required_controls": ["Automated validation", "Audit logging", "Access restriction"],
                "compliance_gaps": ["Ensure biometric consent records comply with local privacy regulations"],
                "evidence": ["Statutory bank compliance framework requirement for identity assurance"],
                "approval_required": True,
                "data_retention": "Preserve verification and transaction records for minimum 7 years"
            })

        return json.dumps({
            "compliance_analysis": analysis,
            "disclaimer": "This analysis is advisory only. Final compliance determinations must be validated by licensed legal and compliance officers.",
            "confidence": 0.89
        })

    def _mock_security_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        analysis = []
        for rid in req_ids:
            threat = "critical" if "SEC" in rid else "high"
            analysis.append({
                "requirement_id": rid,
                "security_concerns": ["Unauthorized data access", "Man-in-the-middle attacks", "Data tampering"],
                "privacy_concerns": ["Customer financial data exposure", "PII mishandling"],
                "recommended_controls": [
                    {"control": "AES-256 / TLS 1.3 cryptographic enforcement", "standard": "NIST SP 800-52 / FIPS 140-3"},
                    {"control": "Role-Based Access Control with MFA", "standard": "ISO/IEC 27001 / SOC 2 Type II"}
                ],
                "threat_level": threat,
                "data_classification": "restricted"
            })

        return json.dumps({
            "security_analysis": analysis,
            "confidence": 0.90
        })

    def _mock_risk_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        primary_id = req_ids[0] if req_ids else "FR-LOAN-001"
        risks = [
            {
                "risk_id": "RISK-001",
                "category": "compliance",
                "description": "Non-compliance with evolving AML/KYC requirements leading to regulatory fines or operating restrictions.",
                "likelihood": "medium",
                "impact": "critical",
                "risk_level": "high",
                "mitigation": "Establish automated regulatory rule updating and real-time compliance gate verification.",
                "related_requirements": [primary_id]
            },
            {
                "risk_id": "RISK-002",
                "category": "security",
                "description": "Exfiltration of sensitive customer financial data through targeted API exploitation.",
                "likelihood": "low",
                "impact": "critical",
                "risk_level": "high",
                "mitigation": "Enforce zero-trust architecture, automated penetration testing, and rate limiting.",
                "related_requirements": [r for r in req_ids if "SEC" in r] or [primary_id]
            },
            {
                "risk_id": "RISK-003",
                "category": "technical",
                "description": "Third-party credit bureau or identity verification provider downtime causing application bottlenecks.",
                "likelihood": "high",
                "impact": "medium",
                "risk_level": "medium",
                "mitigation": "Implement redundant multi-bureau failover and resilient retry queues.",
                "related_requirements": req_ids[:2]
            }
        ]

        return json.dumps({
            "risk_assessment": risks,
            "overall_risk_level": "high",
            "confidence": 0.88
        })

    def _mock_sdlc_response(self, prompt: str) -> str:
        return json.dumps({
            "rationale": "For this regulated financial platform, an Agile-V-Model Hybrid methodology is strongly recommended. The system must meet strict regulatory compliance, data protection, and external audit mandates which demand the structured verification, traceability, and sign-off gates of the V-Model. Concurrently, evolving business lending criteria and iterative stakeholder feedback cycles require the flexibility and rapid delivery sprints of Agile.",
            "trade_offs": [
                "Requires additional upfront governance and traceability overhead compared to pure Agile",
                "Requires rigorous automated regression test suites to maintain sprint velocity during compliance verification"
            ],
            "implementation_notes": "Structure bi-weekly feature sprints with formal compliance and threat-modeling review gates at the conclusion of each milestone release."
        })

    def _mock_srs_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        return json.dumps({
            "title": "Software Requirements Specification — Financial Platform",
            "overview": "Comprehensive IEEE 29148 aligned specification generated from stakeholder requirements.",
            "functional_count": len(req_ids)
        })

    def _mock_validation_response(self, prompt: str) -> str:
        req_ids = self._extract_req_ids(prompt)
        return json.dumps({
            "validation_results": {
                "completeness": 0.92,
                "consistency": 0.94,
                "testability": 0.90,
                "traceability": 0.95,
                "overall_quality": 0.93
            },
            "issues": [
                {
                    "type": "minor_boundary",
                    "requirement": req_ids[0] if req_ids else "FR-LOAN-001",
                    "detail": "Recommend explicitly documenting maximum document upload file sizes."
                }
            ],
            "recommendations": [
                "Establish automated contract tests with external credit verification services",
                "Formulate formal disaster recovery RTO and RPO benchmarks"
            ],
            "confidence": 0.91
        })
