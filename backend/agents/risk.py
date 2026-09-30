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
        risks = response_data.get("risk_assessment", [])

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"risk_assessment": risks, "overall_risk_level": response_data.get("overall_risk_level", "medium"),
                  "risk_count": len(risks)},
            confidence=response_data.get("confidence", 0.80),
            issues=[f"Risk: {r.get('description','')}" for r in risks if r.get("risk_level") in ("high", "critical")],
        )
