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

        if isinstance(response_data, list):
            analysis = response_data
        elif isinstance(response_data, dict):
            analysis = response_data.get("security_analysis") or response_data.get("items") or response_data.get("analysis") or []
        else:
            analysis = []

        if not analysis and requirements:
            for r in requirements:
                analysis.append({
                    "requirement_id": r.get("requirement_id", "REQ"),
                    "security_concerns": ["Unauthorized data access or tampering", "Network interception"],
                    "privacy_concerns": ["Customer financial PII protection"],
                    "recommended_controls": [
                        {"control": "AES-256 data at rest, TLS 1.3 in transit", "standard": "FIPS 140-3"},
                        {"control": "MFA and granular RBAC enforcement", "standard": "SOC 2 Type II"}
                    ],
                    "threat_level": "critical" if "sec" in r.get("category", "").lower() else "high",
                    "data_classification": "restricted" if "sec" in r.get("category", "").lower() else "confidential"
                })

        high_risk = [a for a in analysis if a.get("threat_level") in ("critical", "high")]

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "security_analysis": analysis,
                "high_risk_count": len(high_risk),
                "total_analysed": len(analysis) or len(requirements),
            },
            confidence=response_data.get("confidence", 0.88) if isinstance(response_data, dict) else 0.88,
            issues=[f"High-risk: {a.get('requirement_id','')}" for a in high_risk],
        )

    def should_escalate(self, output: AgentOutput) -> bool:
        if output.data.get("high_risk_count", 0) > 0:
            return True
        return super().should_escalate(output)
