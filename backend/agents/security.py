"""Security & Privacy Agent — identifies cybersecurity, privacy and control requirements."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a cybersecurity and privacy analysis specialist for financial systems.
Analyse requirements for security concerns, privacy risks, and recommend controls.
Respond with JSON: security_analysis (array of {requirement_id, security_concerns, privacy_concerns,
recommended_controls, threat_level, data_classification})."""


class SecurityAgent(BaseAgent):
    name = "security_privacy"
    responsibility = "Identify cybersecurity, privacy and control requirements"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate", "rag_retrieve"]
    dependencies = ["classification"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        req_text = json.dumps(requirements[:15], indent=2)

        prompt = f"""Analyse these financial system requirements for security and privacy.
For each requirement identify:
- security_concerns
- privacy_concerns (PII, financial data, etc.)
- recommended_controls (with applicable standards)
- threat_level (critical/high/medium/low)
- data_classification (public/internal/confidential/restricted)

Requirements:
{req_text}

Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]
        analysis = response_data.get("security_analysis", [])
        high_risk = [a for a in analysis if a.get("threat_level") in ("critical", "high")]

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"security_analysis": analysis, "high_risk_count": len(high_risk),
                  "total_analysed": len(analysis)},
            confidence=response_data.get("confidence", 0.84),
            issues=[f"High-risk: {a.get('requirement_id','')}" for a in high_risk],
        )

    def should_escalate(self, output: AgentOutput) -> bool:
        if output.data.get("high_risk_count", 0) > 0:
            return True
        return super().should_escalate(output)
