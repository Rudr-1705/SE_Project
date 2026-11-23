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

        compact_reqs = "\n".join([f"- {r.get('requirement_id', f'REQ-{i+1}')}: {r.get('statement', '').strip()}" for i, r in enumerate(requirements[:15])])
        prompt = f"""Analyse these requirements for conflicts, contradictions, and duplicates.

Requirements:
{compact_reqs}

Identify:
1. Conflicts: requirements that contradict each other
2. Duplicates: requirements that say the same thing
3. Inconsistencies: requirements with mismatched assumptions
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT, max_tokens=600)
        response_data = result["data"]

        if isinstance(response_data, dict):
            conflicts = response_data.get("conflicts", [])
            duplicates = response_data.get("duplicates", [])
            confidence = response_data.get("confidence", 0.88)
        elif isinstance(response_data, list):
            conflicts = response_data
            duplicates = []
            confidence = 0.88
        else:
            conflicts = []
            duplicates = []
            confidence = 0.85

        return AgentOutput(
            agent_name=self.name, status="success",
            data={
                "conflicts": conflicts,
                "duplicates": duplicates,
                "conflict_count": len(conflicts),
                "duplicate_count": len(duplicates),
                "total_analysed": len(requirements)
            },
            confidence=confidence,
            issues=[f"Conflict: {c.get('description','')}" for c in conflicts if isinstance(c, dict)],
        )

    def should_escalate(self, output: AgentOutput) -> bool:
        if output.data.get("conflict_count", 0) > 0:
            return True
        return super().should_escalate(output)
