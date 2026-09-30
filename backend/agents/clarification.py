"""Clarification Agent — detects ambiguous/incomplete info and generates follow-up questions."""
import json
from agents.base import BaseAgent
from schemas.models import AgentInput, AgentOutput

SYSTEM_PROMPT = """You are a requirements clarification specialist for financial systems.
Analyse requirements for ambiguity, incompleteness, vagueness, and missing details.
Generate targeted follow-up questions (NOT generic questionnaires).
Respond with JSON: clarification_needed (bool), questions (array of {target_requirement, question, reason, priority})."""


class ClarificationAgent(BaseAgent):
    name = "clarification"
    responsibility = "Detect and resolve missing/ambiguous information through follow-up questions"
    required_permissions = ["agents.execute"]
    allowed_tools = ["llm_generate"]
    dependencies = ["requirement_extraction"]

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        requirements = agent_input.data.get("requirements", [])
        if not requirements:
            return AgentOutput(agent_name=self.name, status="success",
                             data={"clarification_needed": False, "questions": []}, confidence=1.0)

        req_text = json.dumps(requirements[:20], indent=2)
        prompt = f"""Analyse these financial requirements for ambiguity, incompleteness, and vagueness.
Generate specific follow-up questions for unclear items.

Requirements:
{req_text}

For each issue found provide:
- target_requirement: the requirement ID
- question: specific clarification question
- reason: why clarification is needed
- priority: high/medium/low
Respond as JSON."""

        result = await self.llm.generate_structured(prompt, SYSTEM_PROMPT)
        response_data = result["data"]
        questions = response_data.get("questions", [])

        return AgentOutput(
            agent_name=self.name, status="success",
            data={"clarification_needed": len(questions) > 0, "questions": questions,
                  "count": len(questions)},
            confidence=response_data.get("confidence", 0.8),
            issues=[f"Clarification needed: {q.get('target_requirement','')}" for q in questions],
        )
