"""Conflict Detection Agent — finds contradictions and duplicates."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements conflict detection specialist for financial systems.
Detect contradictions, inconsistencies, and duplicate requirements.
Respond with JSON: conflicts (array of {type, requirement_a, requirement_b, description, severity, resolution_suggestion}),
duplicates (array of {requirement_a, requirement_b, similarity, recommendation})."""


class ConflictDetectionAgent(BaseAgent):
    name = "conflict_detection"
    responsibility = "Detect contradictions and duplication"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["classification"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        if len(requirements) < 2:
            return AgentOutput(agent_name=self.name, status="success",
                             data={"conflicts": [], "duplicates": []}, confidence=1.0)

        req_text = json.dumps(requirements[:30], indent=2)
        prompt = f"""Analyse these requirements for conflicts, contradictions, and duplicates.

Requirements:
{req_text}

Identify:
1. Conflicts: requirements that contradict each other
2. Duplicates: requirements that say the same thing
3. Inconsistencies: requirements with mismatched assumptions
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]
        conflicts = response_data.get("conflicts", [])
        duplicates = response_data.get("duplicates", [])

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"conflicts": conflicts, "duplicates": duplicates,
                  "conflict_count": len(conflicts), "duplicate_count": len(duplicates)},
            confidence=response_data.get("confidence", 0.82),
            issues=[f"Conflict: {c.get('description','')}" for c in conflicts],
        )

    def should_escalate(self, output: AgentOutput) -> bool:
        if output.data.get("conflict_count", 0) > 0:
            return True
        return super().should_escalate(output)
