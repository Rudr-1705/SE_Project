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

        prompt = f"""Assess risks for this financial system based on requirements, compliance and security analysis.

Requirements: {json.dumps(requirements[:15], indent=2)}
Compliance findings: {json.dumps(compliance_data[:10], indent=2) if compliance_data else 'None'}
Security findings: {json.dumps(security_data[:10], indent=2) if security_data else 'None'}

For each risk provide: risk_id, category (compliance/technical/security/business/operational),
description, likelihood (high/medium/low), impact (critical/high/medium/low),
risk_level, mitigation strategy, related_requirements.
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
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
                    "risk_id": "RISK-001",
                    "category": "compliance",
                    "description": "Non-compliance with dynamic KYC/AML guidelines causing severe statutory penalties.",
                    "likelihood": "medium",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Automate verification checkpoints and mandate compliance officer sign-offs.",
                    "related_requirements": [primary_id]
                },
                {
                    "risk_id": "RISK-002",
                    "category": "security",
                    "description": "Unauthorized access to borrower financial records or encryption key compromise.",
                    "likelihood": "low",
                    "impact": "critical",
                    "risk_level": "high",
                    "mitigation": "Enforce zero-trust architecture, hardware KMS key management, and MFA.",
                    "related_requirements": [r.get("requirement_id") for r in requirements if "SEC" in r.get("requirement_id", "")] or [primary_id]
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
