"""Risk Analysis Agent — assesses business, technical and compliance risks."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a risk analysis specialist for financial systems.
Assess business, technical, security, privacy and compliance risks.
Respond with JSON: risk_assessment (array of {risk_id, category, description,
likelihood, impact, risk_level, mitigation, related_requirements}), overall_risk_level."""


class RiskAnalysisAgent(BaseAgent):
    name = "risk_analysis"
    responsibility = "Assess business, technical and compliance risks"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["compliance", "security_privacy"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        compliance_data = agent_input.data.get("compliance_analysis", [])
        security_data = agent_input.data.get("security_analysis", [])
        jurisdiction = agent_input.data.get("jurisdiction", "India")

        compact_reqs = "\n".join([f"- {r.get('requirement_id', f'REQ-{i+1}')}: {r.get('statement', '').strip()}" for i, r in enumerate(requirements[:15])])

        prompt = f"""Assess risks for this financial system operating in jurisdiction: '{jurisdiction}'.
Generate a concise risk register of exactly 2-3 core risks covering data security, regulatory compliance, and system availability.
Be concise (max 1 sentence per field).

Requirements:
{compact_reqs}

For each risk provide:
- risk_id (e.g. RSK-001)
- category (security/operational/technical/compliance/financial)
- description (specific impact scenario)
- likelihood (high/medium/low)
- impact (critical/high/medium/low)
- risk_level (critical/high/medium/low)
- mitigation (actionable control)
- related_requirements (array of requirement IDs)

Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT, max_tokens=600)
        response_data = result["data"]

        if isinstance(response_data, list):
            risks = response_data
            overall_level = "high"
            confidence = 0.88
        elif isinstance(response_data, dict):
            risks = response_data.get("risk_assessment") or response_data.get("items") or response_data.get("risks") or []
            overall_level = response_data.get("overall_risk_level", "high")
            confidence = response_data.get("confidence", 0.88)
        else:
            risks = []
            overall_level = "medium"
            confidence = 0.75

        if not risks and requirements:
            primary_id = requirements[0].get("requirement_id", "FR-LOAN-001")
            risks = [
                {
                    "risk_id": "RSK-001",
                    "category": "security",
                    "description": "Customer financial PII exposure or data breach via application vulnerabilities or insecure storage.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Enforce field-level AES-256 encryption, TLS 1.3 in transit, and continuous vulnerability scanning.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-002",
                    "category": "security",
                    "description": "Unauthorized access or privilege escalation to loan records and administrative controls.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Implement strict MFA, cryptographic token revocation, and zero-trust API gateway authentication.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-003",
                    "category": "operational",
                    "description": "Flawed credit eligibility determination resulting from erroneous calculation logic or stale bureau data.",
                    "likelihood": "medium",
                    "impact": "high",
                    "risk_level": "high",
                    "mitigation": "Dual automated underwriting checks, automated test assertions on scoring engine, and manual secondary review for edge cases.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-004",
                    "category": "technical",
                    "description": "External integration outages (Credit Bureau / eKYC provider / Banking API) causing loan application stall.",
                    "likelihood": "medium",
                    "impact": "high",
                    "risk_level": "medium",
                    "mitigation": "Circuit breakers, automated exponential backoff retries, and asynchronous fallback queues.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-005",
                    "category": "compliance",
                    "description": f"Regulatory non-compliance with {jurisdiction} statutory financial and AML due diligence directives.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Formal compliance officer sign-off gateways, immutable audit trails, and automated regulatory checklist validation.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-006",
                    "category": "technical",
                    "description": "Permanent data loss or transactional corruption during system disaster or primary storage failure.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Continuous WAL archiving, point-in-time recovery (RPO < 15 min), and cross-zone replica failover (RTO < 1 hour).",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RSK-007",
                    "category": "operational",
                    "description": "Extended system downtime disrupting loan processing during peak business hours.",
                    "likelihood": "medium",
                    "impact": "high",
                    "risk_level": "medium",
                    "mitigation": "Multi-instance load balancing, health probing, auto-scaling worker nodes, and 99.9% uptime SLA monitoring.",
                    "related_requirements": [primary_id]
                }
            ]

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "risk_assessment": risks,
                "overall_risk_level": overall_level,
                "risk_count": len(risks),
                "total_analysed": len(requirements)
            },
            confidence=confidence,
            issues=[f"Risk: {r.get('description','')}" for r in risks if isinstance(r, dict) and r.get("risk_level") in ("high", "critical")],
        )
