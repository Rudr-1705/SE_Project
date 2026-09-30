"""Validation Agent — verifies completeness, consistency and evidence."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements validation specialist for financial systems.
Check each requirement for: ambiguity, incompleteness, inconsistency, duplication,
infeasibility, lack of testability, missing source, undefined terminology,
conflicting stakeholder expectations, missing security/compliance controls.
Respond with JSON: validation_results (metrics), issues (array), recommendations (array)."""


class ValidationAgent(BaseAgent):
    name = "validation"
    responsibility = "Verify completeness, consistency and evidence"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["compliance", "security_privacy", "conflict_detection"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        req_text = json.dumps(requirements[:20], indent=2)

        prompt = f"""Validate these financial system requirements for quality.
Check for: ambiguity, incompleteness, inconsistency, duplication, infeasibility,
lack of testability, missing source, undefined terminology, missing controls.

Requirements:
{req_text}

Provide: validation_results (completeness, consistency, testability, traceability scores 0-1),
issues (array of {{type, requirement, detail}}), recommendations (array of strings).
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]
        issues = response_data.get("issues", [])
        metrics = response_data.get("validation_results", {})

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"validation_results": metrics, "issues": issues,
                  "recommendations": response_data.get("recommendations", []),
                  "issue_count": len(issues), "overall_quality": metrics.get("overall_quality", 0.0)},
            confidence=metrics.get("overall_quality", 0.8),
            issues=[f"{i.get('type','')}: {i.get('detail','')}" for i in issues],
        )
